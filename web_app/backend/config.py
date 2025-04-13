import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("PSQL_DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def check_env_variables() -> None:
        if Config.SECRET_KEY is None:
            raise ValueError(
                f"The 'FLASK_SECRET_KEY' must be supplied using the '-e' flag when starting the Docker container."
            )
        if Config.SQLALCHEMY_DATABASE_URI is None:
            raise ValueError(
                f"The 'PSQL_DATABASE_URL' must be supplied using the '-e' flag when starting the Docker container."
            )
