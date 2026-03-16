from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_API_KEY: str
    SPRING_API_BASE_URL: str = "http://localhost:8080"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TIMEOUT_SECONDS: int = 20
    CHROMA_DIR: str = "./chroma_data"
    CHAT_LOG_DB_PATH: str = "./data/chatbot_logs.db"
    CHAT_RATE_LIMIT_WINDOW_SECONDS: int = 60
    CHAT_RATE_LIMIT_MAX_REQUESTS: int = 12

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
