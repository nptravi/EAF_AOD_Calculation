from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base

Path("data").mkdir(exist_ok=True)

DATABASE_URL = "sqlite:///data/process_calculator.db"

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

print("Database and tables created successfully")