from sqlalchemy import select, func

from app.database.database import SessionLocal
from app.database.models import RecoveryMaster, Unit, MaterialMaster


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


def get_material_master():
    with SessionLocal() as session:
        result = session.execute(
            select(MaterialMaster).order_by(MaterialMaster.material_name)
        )
        return result.scalars().all()


def save_material_master(rows):
    """
    rows: list of dicts, one per material row from the editor.
    Each dict may contain "id" (None/"" for a new, unsaved row).
    Any existing DB row whose id is NOT present in `rows` is treated
    as user-deleted and removed.
    """
    with SessionLocal() as session:

        incoming_ids = {
            int(row["id"])
            for row in rows
            if row.get("id") not in (None, "")
        }

        existing = session.execute(
            select(MaterialMaster)
        ).scalars().all()

        for material in existing:
            if material.id not in incoming_ids:
                session.delete(material)

        next_code = session.execute(
            select(func.max(MaterialMaster.material_code))
        ).scalar() or 1000

        for row in rows:
            values = {
                "material_name": str(row["Material Name"]).strip(),
                "bucket_only": bool(row["Bucket Only"]),
                "lpp": (
                    float(row["LPP"])
                    if row.get("LPP") not in (None, "")
                    else None
                ),
                "C": float(row["C"]) / 100,
                "Si": float(row["Si"]) / 100,
                "Mn": float(row["Mn"]) / 100,
                "Cr": float(row["Cr"]) / 100,
                "Ni": float(row["Ni"]) / 100,
                "Cu": float(row["Cu"]) / 100,
                "Ti": float(row["Ti"]) / 100,
                "Nb": float(row["Nb"]) / 100,
                "Mo": float(row["Mo"]) / 100,
                "P": float(row["P"]) / 100,
                "S": float(row["S"]) / 100,
                "N": float(row["N"]) / 100,
            }

            row_id = row.get("id")

            if row_id not in (None, ""):
                material = session.get(MaterialMaster, int(row_id))
                for key, value in values.items():
                    setattr(material, key, value)
            else:
                next_code += 1
                material = MaterialMaster(
                    material_code=next_code,
                    **values
                )
                session.add(material)

        session.commit()