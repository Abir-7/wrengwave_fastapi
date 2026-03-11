from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "WrengWave"
    DATABASE_URL: str
# email-------------
    SMTP_SERVER: str 
    SMTP_PORT: int
    EMAIL_USER: str 
    EMAIL_PASS: str 
    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
#----------------
    class Config:
        env_file = ".env"

settings = Settings()

