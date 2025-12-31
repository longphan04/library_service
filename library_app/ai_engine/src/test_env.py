import os
import sys
from dotenv import load_dotenv
from google import genai

# Load key từ file .env
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def test_connection():
    print("------- TEST MÔI TRƯỜNG -------")
    
    # 1. Kiểm tra Key
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        print(f"Đã tìm thấy API Key: {key[:5]}...*****")
    else:
        print("LỖI: Chưa thấy file .env hoặc chưa có Key!")
        return

    # 2. Kiểm tra gọi Google
    print("Đang gọi thử Gemini...")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents="Chào AI, bạn có khỏe không?"
        )
        print("KẾT NỐI THÀNH CÔNG!")
        print(f"AI trả lời: {response.text.strip()}")
    except Exception as e:
        print(f"Lỗi kết nối: {e}")

if __name__ == "__main__":
    test_connection()