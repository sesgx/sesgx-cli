from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sesgx_cli.env_vars import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"connect_timeout": 10},
)


Session = sessionmaker(bind=engine, autoflush=False)
