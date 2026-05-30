# core/config.py
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Feature Toggles (สวิตช์สลับร่าง) ---
    # ปิดไว้ก่อนเป็นค่า Default (ของเก่า) ครับป๋า
    # ENABLE_NEW_EXAMINATION_FLOW: bool = False

    # --- Database Config ---
    DB_NAME: str = "hospital_database.db"

    secret_key: str = "my-super-secret-key-for-local-tdd-12345"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # บอกให้ไปอ่านจากไฟล์ .env ถ้ามีครับป๋า
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def model_post_init(self, __context):
        """เตือนถ้าใช้ default key"""
        if self.secret_key == "my-super-secret-key-for-local-tdd-12345":
            warnings.warn(
                "⚠️ ใช้ SECRET_KEY แบบ default อยู่ — ห้ามใช้ใน Production!",
                stacklevel=2,
            )


# สร้างตัวแปรไว้เรียกใช้ทั่วโลก
settings = Settings()
