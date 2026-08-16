from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Unit

Path("data").mkdir(exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "process_calculator.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)


def ensure_default_units():
    default_units = [
        (3501, "EAF"),
        (3502, "AOD"),
        (3503, "LF"),
    ]

    with SessionLocal() as session:
        for unit_code, unit_name in default_units:
            existing = session.execute(
                select(Unit).where(
                    Unit.unit_code == unit_code
                )
            ).scalar_one_or_none()

            if existing is None:
                session.add(
                    Unit(
                        unit_code=unit_code,
                        unit_name=unit_name
                    )
                )

        session.commit()

Base.metadata.create_all(engine)
ensure_default_units()

print("Database and tables created successfully")