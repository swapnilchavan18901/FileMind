from pydantic_settings import BaseSettings

class Env(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str

    # optional defaults
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    class Config:
        env_file = "../.env"
        case_sensitive = True

env = Env()
