import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# --- CẤU HÌNH ĐƯỜNG DẪN (PATH CONFIGURATION) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Thư mục ai_engine
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Load API Key
load_dotenv(os.path.join(BASE_DIR, '.env'))
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("FATAL ERROR: GOOGLE_API_KEY not found.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

def ensure_directories():
    """Tự động tạo folder reports và logs nếu chưa có"""
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        print(f"Created directory: {REPORTS_DIR}")
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        print(f"Created directory: {LOGS_DIR}")

def save_report(content):
    """Lưu nội dung vào file text có gắn thời gian"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"system_check_{timestamp}.txt"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n[REPORT SAVED] Path: {filepath}")

def get_clean_model_name(model_obj):
    if hasattr(model_obj, 'name'):
        return model_obj.name
    return str(model_obj)

def run_system_check():
    ensure_directories()
    
    # Chuẩn bị nội dung báo cáo (String Buffer)
    report_lines = []
    def log(text):
        print(text)
        report_lines.append(text)

    log("SYSTEM CHECK INITIATED...")
    log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("-" * 50)

    results = []

    try:
        all_models = list(client.models.list())
        target_models = []
        for m in all_models:
            name = get_clean_model_name(m)
            if "gemini" in name or "embedding" in name:
                target_models.append(name)

        log(f"Models found: {len(target_models)}. Testing connectivity...\n")

        for model_name in target_models:
            start_time = time.time()
            status = "UNKNOWN"
            note = ""
            try:
                if "embedding" in model_name:
                    client.models.embed_content(model=model_name, contents="Test")
                    status = "PASS"
                else:
                    if "vision" in model_name:
                        status = "SKIP"
                        note = "Vision only"
                    else:
                        client.models.generate_content(model=model_name, contents="Ping")
                        status = "PASS"
            except Exception as e:
                status = "FAIL"
                note = str(e)[:50]

            latency = (time.time() - start_time) * 1000
            
            # Chỉ thêm vào danh sách kết quả (không in từng dòng ra màn hình cho gọn)
            results.append({
                "model": model_name,
                "type": "EMBED" if "embedding" in model_name else "CHAT",
                "status": status,
                "latency": f"{latency:.0f}ms",
                "note": note
            })
            print(".", end="", flush=True) # Chỉ in dấu chấm tiến độ

    except Exception as e:
        log(f"\nCRITICAL ERROR: {e}")
        return

    # Tạo bảng báo cáo
    header = f"\n\n{'MODEL NAME':<55} | {'TYPE':<8} | {'STATUS':<6} | {'TIME':<8} | {'NOTE'}"
    divider = "-" * 100
    
    log(header)
    log(divider)

    for res in results:
        if res['status'] != "SKIP":
            line = f"{res['model']:<55} | {res['type']:<8} | {res['status']:<6} | {res['latency']:<8} | {res['note']}"
            log(line)
            
    log(divider)
    log("TEST COMPLETED.")
    
    # Lưu toàn bộ nội dung in ra màn hình vào file
    save_report("\n".join(report_lines))

if __name__ == "__main__":
    run_system_check()