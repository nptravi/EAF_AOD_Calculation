from app.database.database import SessionLocal
from app.database.models import Unit

with SessionLocal() as session:
    existing_units = session.query(Unit).count()

    if existing_units == 0:
        session.add_all([
            Unit(unit_code=3501, unit_name="EAF"),
            Unit(unit_code=3502, unit_name="AOD"),
            Unit(unit_code=3503, unit_name="LF"),
        ])
        session.commit()
        print("Unit master populated")
    else:
        print("Unit master already contains data")