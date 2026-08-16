from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import RecoveryMaster, Unit


def get_recovery_master():
    with SessionLocal() as session:
        result = session.execute(
            select(RecoveryMaster)
        )
        return result.scalars().all()


def get_units():
    with SessionLocal() as session:
        result = session.execute(
            select(Unit).order_by(Unit.unit_code)
        )
        return result.scalars().all()


def save_recovery_master(data):
    with SessionLocal() as session:
        for item in data:
            unit_code = int(item["Unit Code"])

            recovery = session.execute(
                select(RecoveryMaster).where(
                    RecoveryMaster.unit_code == unit_code
                )
            ).scalar_one_or_none()

            values = {
                "Fe": float(item["Fe"]) / 100,
                "C": float(item["C"]) / 100,
                "Si": float(item["Si"]) / 100,
                "Mn": float(item["Mn"]) / 100,
                "Cr": float(item["Cr"]) / 100,
                "Ni": float(item["Ni"]) / 100,
                "Cu": float(item["Cu"]) / 100,
                "Ti": float(item["Ti"]) / 100,
                "Nb": float(item["Nb"]) / 100,
                "Mo": float(item["Mo"]) / 100,
                "P": float(item["P"]) / 100,
                "S": float(item["S"]) / 100,
                "N": float(item["N"]) / 100,
            }

            if recovery:
                for key, value in values.items():
                    setattr(recovery, key, value)
            else:
                recovery = RecoveryMaster(
                    unit_code=unit_code,
                    **values
                )
                session.add(recovery)

        session.commit()


