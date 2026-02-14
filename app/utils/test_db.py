from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

try:
    with engine.connect() as conn:
        print("Database connected successfully!")
except Exception as e:
    print("Error:", e)
