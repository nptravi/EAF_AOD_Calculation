from sqlalchemy.exc import IntegrityError

from app.database.database import SessionLocal
from app.database.models import RecoveryMaster

with SessionLocal() as session:
    test_recovery = RecoveryMaster(
        unit_code=3501,
        Fe=1.10
    )

    session.add(test_recovery)

    try:
        session.commit()
        print("ERROR: Invalid recovery was accepted")
    except IntegrityError:
        session.rollback()
        print("SUCCESS: Invalid recovery was rejected")