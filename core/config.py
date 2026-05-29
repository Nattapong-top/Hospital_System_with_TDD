# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Feature Toggles (สวิตช์สลับร่าง) ---
    # ปิดไว้ก่อนเป็นค่า Default (ของเก่า) ครับป๋า
    # ENABLE_NEW_EXAMINATION_FLOW: bool = False

    # --- Database Config ---
    DB_NAME: str = "hospital_database.db"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # บอกให้ไปอ่านจากไฟล์ .env ถ้ามีครับป๋า
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# สร้างตัวแปรไว้เรียกใช้ทั่วโลก
settings = Settings()
