from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import RecoveryMaster


def get_recovery_master():
    with SessionLocal() as session:
        result = session.execute(
            select(RecoveryMaster)
        )
        return result.scalars().all()