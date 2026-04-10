from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "WrengWave"
    DATABASE_URL: str
    BASE_URL: str
    FRONTEND_URL: str
# email-------------
    SMTP_SERVER: str 
    SMTP_PORT: int
    EMAIL_USER: str 
    EMAIL_PASS: str 
    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_DAYS: int
    REFRESH_TOKEN_EXPIRE_DAYS:int

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
#----------------
    class Config:
        env_file = ".env"

settings = Settings()

