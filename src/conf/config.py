from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_domain: str
    postgres_port: int

    secret_key: str
    algorithm: str

    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str

    redis_host: str
    redis_port: int

    allowed_ips: str

    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def sqlalchemy_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_domain}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()  # type: ignore
