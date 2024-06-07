import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "asd123")  # Change 'your_secret_key' to a strong, random value
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
