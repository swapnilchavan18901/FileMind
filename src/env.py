from pydantic_settings import BaseSettings

class Env(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str

    # optional defaults
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    AWS_REGION: str
    AWS_S3_BUCKET: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    RABBIT_MQ_URL: str
    RABBIT_MQ_API_KEY: str
    OPENAI_API_KEY:str
    class Config:
        env_file = "../.env"
        case_sensitive = True

env = Env()
