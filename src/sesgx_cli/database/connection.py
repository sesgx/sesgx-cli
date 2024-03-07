import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(find_dotenv(usecwd=True))


database_url = os.environ.get("SESG_DATABASE_URL")

if database_url is None:
    raise RuntimeError("Must set SESG_DATABASE_URL environment variable")

engine = create_engine(database_url)


Session = sessionmaker(bind=engine, autoflush=False)
