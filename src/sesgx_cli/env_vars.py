import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

DATABASE_URL = os.environ.get("SESG_DATABASE_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID_EXPERIMENT = os.environ.get("TELEGRAM_CHAT_ID_EXPERIMENT")
TELEGRAM_CHAT_ID_SCOPUS = os.environ.get("TELEGRAM_CHAT_ID_SCOPUS")
PC_SPECS = os.environ.get("PC_SPECS")
USER_NAME = os.environ.get("USER_NAME")

if DATABASE_URL is None:
    raise RuntimeError("Must set SESG_DATABASE_URL environment variable")
