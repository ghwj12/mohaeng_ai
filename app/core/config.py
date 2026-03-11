from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_API_KEY: str
    SPRING_API_BASE_URL: str = "http://localhost:8080"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TIMEOUT_SECONDS: int = 20
    CHROMA_DIR: str = "./chroma_data"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()