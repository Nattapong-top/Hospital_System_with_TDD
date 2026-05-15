# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Feature Toggles (สวิตช์สลับร่าง) ---
    # ปิดไว้ก่อนเป็นค่า Default (ของเก่า) ครับป๋า
    ENABLE_NEW_EXAMINATION_FLOW: bool = False

    # --- Database Config ---
    DB_NAME: str = "hospital_database.db"

    # บอกให้ไปอ่านจากไฟล์ .env ถ้ามีครับป๋า
    model_config = SettingsConfigDict(env_file=".env")


# สร้างตัวแปรไว้เรียกใช้ทั่วโลก
settings = Settings()
