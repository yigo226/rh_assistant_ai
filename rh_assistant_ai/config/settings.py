import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    password = quote_plus(os.getenv("DB_PASSWORD"))

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('DB_USER')}:"
        f"{password}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False