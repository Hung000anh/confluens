import os
import io
import json
import logging
import zipfile
import threading
import tempfile
import pandas as pd
import requests
from datetime import date
from bs4 import BeautifulSoup
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

COT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cot")
METADATA_FILE = os.path.join(COT_DATA_DIR, "metadata.json")

COT_REPORT_TYPES = [
    "legacy_fut", 
    "legacy_futopt", 
    "supplemental_futopt", 
    "disaggregated_fut", 
    "disaggregated_futopt", 
    "traders_in_financial_futures_fut", 
    "traders_in_financial_futures_futopt"
]

class CotService:
    @staticmethod
    def _get_metadata() -> dict:
        if not os.path.exists(METADATA_FILE):
            return {}
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading COT metadata: {e}")
            return {}

    @staticmethod
    def _save_metadata(metadata: dict):
        os.makedirs(COT_DATA_DIR, exist_ok=True)
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=4)

    @staticmethod
    def _cot_year(year=2020, cot_report_type="legacy_fut", temp_dir=None):    
        if cot_report_type == "legacy_fut": 
            rep = "deacot"
            txt_name ="annual.txt"
        elif cot_report_type == "legacy_futopt": 
            rep = "deahistfo"
            txt_name ="annualof.txt"
        elif cot_report_type == "supplemental_futopt": 
            rep = "dea_cit_txt_"
            txt_name ="annualci.txt"
        elif cot_report_type == "disaggregated_fut": 
            rep = "fut_disagg_txt_"
            txt_name ="f_year.txt"
        elif cot_report_type == "disaggregated_futopt": 
            rep = "com_disagg_txt_"
            txt_name ="c_year.txt"
        elif cot_report_type == "traders_in_financial_futures_fut": 
            rep = "fut_fin_txt_"
            txt_name ="FinFutYY.txt"
        elif cot_report_type == "traders_in_financial_futures_futopt": 
            rep = "com_fin_txt_"
            txt_name ="FinComYY.txt"
        else:
            raise ValueError("Invalid cot_report_type")
        
        cot_url = f"https://cftc.gov/files/dea/history/{rep}{year}.zip"
        r = requests.get(cot_url, timeout=30)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(path=temp_dir)
        txt_path = os.path.join(temp_dir, txt_name)
        df = pd.read_csv(txt_path, low_memory=False, dtype=str)  
        return df

    @classmethod
    def download_recent_data(cls, report_type):
        """Tải dữ liệu của năm ngoái và năm nay"""
        os.makedirs(COT_DATA_DIR, exist_ok=True)
        file_path = os.path.join(COT_DATA_DIR, f"{report_type}.parquet")
        
        current_year = date.today().year
        years_to_download = [current_year - 1, current_year]
        
        logger.info(f"Downloading recent data ({years_to_download}) for {report_type}...")
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                df_list = []
                for year in years_to_download:
                    try:
                        df_year = cls._cot_year(year, report_type, temp_dir=temp_dir)
                        df_list.append(df_year)
                    except Exception as e:
                        logger.warning(f"Could not download {report_type} for {year}: {e}")
                
                if not df_list:
                    return False
                
                df = pd.concat(df_list, ignore_index=True)
                
                # Tạo cột Date chuẩn từ các biến thể tên cột của CFTC
                for date_col in ['Report_Date_as_MM_DD_YYYY', 'Report_Date_as_YYYY-MM-DD', 'As of Date in Form YYYY-MM-DD', 'As_of_Date_In_Form_YYYY-MM-DD', 'As of Date in Form YYMMDD', 'As_of_Date_In_Form_YYMMDD']:
                    if date_col in df.columns:
                        if 'YYMMDD' in date_col:
                            df['Date'] = pd.to_datetime(df[date_col], format='%y%m%d', errors='coerce').dt.strftime('%Y-%m-%d')
                        elif 'MM_DD_YYYY' in date_col:
                            df['Date'] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
                        else:
                            df['Date'] = pd.to_datetime(df[date_col], format='%Y-%m-%d', errors='coerce').dt.strftime('%Y-%m-%d')
                        break
                
                df = df.astype(str)
                df.to_parquet(file_path, index=False)
                logger.info(f"Saved {report_type} to {file_path}. Total rows: {len(df)}")
                return True
            except Exception as e:
                logger.error(f"Failed to download {report_type}: {e}")
                return False

    @classmethod
    def sync_current_year(cls, report_type):
        """Cập nhật dữ liệu của năm hiện tại cho một báo cáo đã tồn tại"""
        file_path = os.path.join(COT_DATA_DIR, f"{report_type}.parquet")
        if not os.path.exists(file_path):
            return cls.download_recent_data(report_type)
            
        current_year = date.today().year
        logger.info(f"Syncing current year ({current_year}) for {report_type}...")
        
        try:
            df = pd.read_parquet(file_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                df_year = cls._cot_year(current_year, report_type, temp_dir=temp_dir)
                
                for date_col in ['Report_Date_as_MM_DD_YYYY', 'Report_Date_as_YYYY-MM-DD', 'As of Date in Form YYYY-MM-DD', 'As_of_Date_In_Form_YYYY-MM-DD', 'As of Date in Form YYMMDD', 'As_of_Date_In_Form_YYMMDD']:
                    if date_col in df_year.columns:
                        if 'YYMMDD' in date_col:
                            df_year['Date'] = pd.to_datetime(df_year[date_col], format='%y%m%d', errors='coerce').dt.strftime('%Y-%m-%d')
                        elif 'MM_DD_YYYY' in date_col:
                            df_year['Date'] = pd.to_datetime(df_year[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
                        else:
                            df_year['Date'] = pd.to_datetime(df_year[date_col], format='%Y-%m-%d', errors='coerce').dt.strftime('%Y-%m-%d')
                        break
                
                # Chỉ giữ lại dữ liệu của năm ngoái (xoá năm cũ hơn và xoá năm nay để chèn đè)
                if 'Date' in df.columns:
                    # Chuyển về str để so sánh an toàn
                    df['Date'] = df['Date'].astype(str)
                    df = df[df['Date'].str.slice(0, 4) == str(current_year - 1)]
                
                df = df.astype(str)
                df_year = df_year.astype(str)
                df = pd.concat([df, df_year], ignore_index=True)
                
                df.to_parquet(file_path, index=False)
                logger.info(f"Successfully synced {report_type} for {current_year}.")
                return True
        except Exception as e:
            logger.error(f"Failed to sync {report_type}: {e}")
            return False

    @classmethod
    def _run_sync_task(cls):
        metadata = cls._get_metadata()
        today_str = date.today().isoformat()
        
        last_updated = metadata.get("last_updated")
        
        # Kiểm tra xem có file nào bị thiếu không (trường hợp bị xóa thủ công)
        all_files_exist = all(
            os.path.exists(os.path.join(COT_DATA_DIR, f"{report}.parquet")) 
            for report in COT_REPORT_TYPES
        )
        
        if last_updated == today_str and all_files_exist:
            logger.info("COT data is already up-to-date for today.")
            return

        success_count = 0
        for report in COT_REPORT_TYPES:
            # Nếu chưa có file thì download all, nếu có rồi thì sync year
            file_path = os.path.join(COT_DATA_DIR, f"{report}.parquet")
            if not os.path.exists(file_path):
                if cls.download_recent_data(report):
                    success_count += 1
            else:
                if cls.sync_current_year(report):
                    success_count += 1
                    
        if success_count == len(COT_REPORT_TYPES):
            metadata["last_updated"] = today_str
            cls._save_metadata(metadata)
            logger.info("COT data sync completed successfully.")
        else:
            logger.warning(f"COT sync finished with {success_count}/{len(COT_REPORT_TYPES)} successes. Will try again tomorrow.")

    @classmethod
    def init_and_sync(cls):
        """Chạy tiến trình tải/cập nhật ở background"""
        thread = threading.Thread(target=cls._run_sync_task)
        thread.daemon = True
        thread.start()

    @classmethod
    def get_cot_data(cls, report_type: str, limit: int = 1000):
        """Lấy dữ liệu COT từ file Parquet (chỉ đọc)"""
        if report_type not in COT_REPORT_TYPES:
            raise ValueError(f"Invalid report type: {report_type}")
            
        file_path = os.path.join(COT_DATA_DIR, f"{report_type}.parquet")
        if not os.path.exists(file_path):
            return []
            
        try:
            # Chỉ lấy limit dòng mới nhất
            df = pd.read_parquet(file_path)
            if 'Date' in df.columns:
                df = df.sort_values(by='Date', ascending=False)
            
            # Lọc các cột cần thiết cho Web UI
            cols_to_keep = []
            if 'Date' in df.columns:
                cols_to_keep.append('Date')
                
            for col in df.columns:
                if col == 'Date': continue
                
                # Chuẩn hóa tên cột để kiểm tra dễ dàng hơn (áp dụng cho cả Legacy và Financial)
                col_norm = col.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
                
                if col_norm in ['market_and_exchange_names', 'open_interest_all', 'change_in_open_interest_all', 'change_open_interest_all']:
                    cols_to_keep.append(col)
                elif 'positions_long_all' in col_norm or 'positions_short_all' in col_norm or 'positions_spread' in col_norm:
                    cols_to_keep.append(col)
                elif 'change' in col_norm and ('long_all' in col_norm or 'short_all' in col_norm or 'spread' in col_norm):
                    cols_to_keep.append(col)
            
            # Đảm bảo thứ tự cột: Date, Market_and_Exchange_Names, Open_Interest_All, rồi đến các cột khác
            preferred_order = [c for c in cols_to_keep if c == 'Date' or 'market' in c.lower() or 'interest' in c.lower()]
            other_cols = [c for c in cols_to_keep if c not in preferred_order]
            df = df[preferred_order + other_cols]
            
            # Đổi tên các cột quá dài cho giao diện Web
            rename_map = {}
            for col in df.columns:
                if 'market_and_exchange_names' == col.lower() or 'market and exchange names' == col.lower():
                    rename_map[col] = 'Market'
                    # Lọc bớt tên sàn trong giá trị dữ liệu (Ví dụ: "GOLD - COMMODITY EXCHANGE INC." -> "GOLD")
                    df[col] = df[col].astype(str).apply(lambda x: x.split(' - ')[0].strip() if ' - ' in x else x)
            if rename_map:
                df = df.rename(columns=rename_map)
            
            # Trả về dưới dạng danh sách dicts
            result = df.head(limit).to_dict(orient="records")
            return result
        except Exception as e:
            logger.error(f"Error reading COT data {report_type}: {e}")
            return []
