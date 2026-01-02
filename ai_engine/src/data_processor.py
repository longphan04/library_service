import json
import csv
import os
import glob
import logging
from datetime import datetime
from config.settings import settings

# --- 1. CẤU HÌNH LOGGER ---
log_filename = os.path.join(settings.LOG_DIR, "data_processor.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataProcessor")

class DataProcessor:
    def __init__(self):
        self.raw_dir = settings.DATA_RAW_DIR
        self.processed_dir = settings.DATA_PROCESSED_DIR
        self.report_dir = settings.REPORT_DIR # Folder lưu báo cáo
        
        # Bộ đếm thống kê
        self.stats = {
            "start_time": datetime.now(),
            "total_raw_items": 0,
            "success": 0,
            "dropped_duplicate": 0,
            "dropped_no_desc": 0,
            "dropped_short_desc": 0,
            "dropped_bad_data": 0,
            "dropped_no_id": 0
        }

    def extract_best_identifier(self, identifiers):
        """
        Lấy identifier và type gốc (Ưu tiên ISBN 13 -> 10 -> Khác)
        """
        if not identifiers:
            return "", ""
        
        # 1. Ưu tiên ISBN_13
        for item in identifiers:
            if item.get('type') == 'ISBN_13':
                return item.get('identifier'), "ISBN_13"
        
        # 2. Ưu tiên ISBN_10
        for item in identifiers:
            if item.get('type') == 'ISBN_10':
                return item.get('identifier'), "ISBN_10"
        
        # 3. Lấy bất kỳ loại nào khác
        first_item = identifiers[0]
        return first_item.get('identifier', ""), first_item.get('type', "UNKNOWN")

    def clean_item(self, raw_item, seen_ids):
        self.stats["total_raw_items"] += 1
        
        book_id = raw_item.get("id")
        info = raw_item.get("volumeInfo", {})
        
        title = info.get("title")
        subtitle = info.get("subtitle", "")
        description = info.get("description", "")
        
        # Lấy Identifier & Type
        ident_val, ident_type = self.extract_best_identifier(info.get("industryIdentifiers", []))

        # --- CÁC BỘ LỌC (FILTERS) ---
        if not book_id or not title:
            self.stats["dropped_bad_data"] += 1
            return None
        
        if book_id in seen_ids:
            self.stats["dropped_duplicate"] += 1
            return None

        if not ident_val:
            self.stats["dropped_no_id"] += 1
            return None

        if not description:
            self.stats["dropped_no_desc"] += 1
            return None

        if len(description) < 20:
            self.stats["dropped_short_desc"] += 1
            return None

        # --- LÀM SẠCH ---
        thumbnail = info.get("imageLinks", {}).get("thumbnail", "")
        if thumbnail:
            thumbnail = thumbnail.replace("&zoom=1", "").replace("&edge=curl", "")

        authors_list = info.get("authors", ["Unknown"])
        authors_str = ", ".join(authors_list) if isinstance(authors_list, list) else str(authors_list)

        published_date = info.get("publishedDate", "N/A")
        year = published_date[:4] if len(published_date) >= 4 else "N/A"

        categories = info.get("categories", ["General"])
        category_str = categories[0] if categories else "General"

        # Rich Text
        full_title_text = f"{title} - {subtitle}" if subtitle else title
        rich_text = (
            f"Tiêu đề: {full_title_text}\n"
            f"Mã định danh: {ident_val} ({ident_type})\n"
            f"Tác giả: {authors_str}\n"
            f"Thể loại: {category_str}\n"
            f"Năm xuất bản: {year}\n"
            f"Tóm tắt nội dung: {description}"
        )

        clean_data = {
            "id": book_id,
            "identifier": ident_val,    # Giữ nguyên
            "type": ident_type,         # Giữ nguyên
            "title": title,
            "subtitle": subtitle,
            "authors": authors_str,
            "publisher": info.get("publisher", "Unknown"),
            "published_year": year,
            "category": category_str,
            "language": info.get("language", "en"),
            "thumbnail": thumbnail,
            "google_link": info.get("infoLink", ""),
            "description": description, 
            "rich_text": rich_text
        }

        self.stats["success"] += 1
        return clean_data

    def save_to_json(self, data, filename):
        path = os.path.join(self.processed_dir, filename)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON Saved: {path}")
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")

    def save_to_csv(self, data, filename):
        if not data: return
        path = os.path.join(self.processed_dir, filename)
        keys = data[0].keys()
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"CSV Saved: {path}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")

    def generate_report_content(self):
        """Tạo nội dung báo cáo dưới dạng String"""
        duration = datetime.now() - self.stats["start_time"]
        content = (
            f"========================================\n"
            f"       DATA PROCESSING REPORT           \n"
            f"========================================\n"
            f"Date         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Duration     : {duration}\n"
            f"Status       : COMPLETED\n"
            f"----------------------------------------\n"
            f"TOTAL RAW INPUT     : {self.stats['total_raw_items']:>5}\n"
            f"VALID BOOKS (KEPT)  : {self.stats['success']:>5}\n"
            f"----------------------------------------\n"
            f"DROPPED ITEMS DETAILS:\n"
            f"Duplicate ID        : {self.stats['dropped_duplicate']:>5}\n"
            f"No Identifier       : {self.stats['dropped_no_id']:>5}\n"
            f"No Description      : {self.stats['dropped_no_desc']:>5}\n"
            f"Short Description   : {self.stats['dropped_short_desc']:>5}\n"
            f"Bad Data (ID/Title) : {self.stats['dropped_bad_data']:>5}\n"
            f"========================================\n"
        )
        return content

    def save_report_to_file(self):
        """[MỚI] Lưu báo cáo vào folder reports"""
        report_content = self.generate_report_content()
        
        # In ra màn hình console để xem ngay
        print("\n" + report_content)

        # Lưu vào file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processor_report_{timestamp}.txt"
        filepath = os.path.join(self.report_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Report saved to: {filepath}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def run(self):
        logger.info("STARTING DATA PROCESSOR...")
        
        raw_files = glob.glob(os.path.join(self.raw_dir, "*.json"))
        if not raw_files:
            logger.warning("No raw files found. Please run 'crawl' first!")
            return

        all_clean_books = []
        seen_ids = set()

        logger.info(f"Found {len(raw_files)} raw files. Processing...")

        for filepath in raw_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, list):
                        for item in raw_data:
                            cleaned_book = self.clean_item(item, seen_ids)
                            if cleaned_book:
                                all_clean_books.append(cleaned_book)
                                seen_ids.add(cleaned_book['id'])
            except Exception as e:
                logger.error(f"Error processing file {filepath}: {e}")

        # [MỚI] Lưu và in báo cáo
        self.save_report_to_file()

        if all_clean_books:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_to_json(all_clean_books, f"clean_books_{timestamp}.json")
            self.save_to_csv(all_clean_books, f"clean_books_{timestamp}.csv")
        else:
            logger.warning("No valid books found.")

def run_processor():
    processor = DataProcessor()
    processor.run()

if __name__ == "__main__":
    run_processor()