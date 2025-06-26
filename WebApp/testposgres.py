from dotenv import load_dotenv
import psycopg2
load_dotenv()
import os


def get_connection():
    return psycopg2.connect(DATABASE_URL)

DATABASE_URL = os.getenv("DATABASE_URL")
print(get_connection())
