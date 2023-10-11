import redis.asyncio

from pydantic_settings import BaseSettings

async def init_async_redis():
    return redis.asyncio.Redis(
        host=settings.redis_host,
        password=settings.redis_password,
        port=settings.redis_port,
        db=0,
        encoding="utf-8",
    )
    
class Settings(BaseSettings):
    postgres_user: str = "postgres"
    postgres_password: str = "secretPassword"
    postgres_db: str = "postgres"
    postgres_domain: str = "localhost"
    postgres_port: int = 5432
    
    secret_key: str = "secret_key"
    algorithm: str = "HS256"

    mail_username: str = "example@meta.ua"
    mail_password: str = "secretPassword"
    mail_from: str = "example@meta.ua"
    mail_port: int = 465
    mail_server: str = "smtp.meta.ua"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    # allowed_ips: str

    cloudinary_name: str = "name"
    cloudinary_api_key: str = "1234567890"
    cloudinary_api_secret: str = "secret"

    class ConfigDict:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def sqlalchemy_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_domain}/{self.postgres_db}"

settings = Settings()  # type: ignore
