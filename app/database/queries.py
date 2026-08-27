from sqlalchemy import select, func

from app.database.database import SessionLocal
from app.database.models import RecoveryMaster, Unit, MaterialMaster, Grade, AODProvider


def _is_missing(value):
    # Defensive check: treat None, "", and float NaN as missing.
    # NaN != NaN is True, so this catches it without a pandas import.
    if value is None or value == "":
        return True
    if isinstance(value, float) and value != value:
        return True
    return False


def get_recovery_master():
    with SessionLocal() as session:
        result = session.execute(
            select(RecoveryMaster)
        )
        return result.scalars().all()

def get_recovery_for_unit_code(unit_code):
    with SessionLocal() as session:
        result = session.execute(
            select(RecoveryMaster).where(
                RecoveryMaster.unit_code == unit_code
            )
        )
        return result.scalars().first()

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
            if not _is_missing(row.get("id"))
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
                    if not _is_missing(row.get("LPP"))
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

            if not _is_missing(row_id):
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


def get_grade_master():
    with SessionLocal() as session:
        result = session.execute(
            select(Grade).order_by(Grade.grade_name)
        )
        return result.scalars().all()

def get_grade_composition(grade_name):
    with SessionLocal() as session:
        result = session.execute(
            select(Grade)
            .where(Grade.grade_name == grade_name)
            .order_by(Grade.grade_name)
        )
        return result.scalars().first()

def save_grade_master(rows):
    """
    rows: list of dicts, one per grade row from the editor.
    Each dict may contain "id" (None/"" for a new, unsaved row).
    Any existing DB row whose id is NOT present in `rows` is treated
    as user-deleted and removed. No code field — grade_name is the
    only identifier.
    """
    with SessionLocal() as session:

        incoming_ids = {
            int(row["id"])
            for row in rows
            if not _is_missing(row.get("id"))
        }

        existing = session.execute(
            select(Grade)
        ).scalars().all()

        for grade in existing:
            if grade.id not in incoming_ids:
                session.delete(grade)

        for row in rows:
            values = {
                "grade_name": str(row["Grade Name"]).strip(),
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
                "EAF_C": float(row["EAF_C"]) / 100,
                "EAF_Cr": float(row["EAF_Cr"]) / 100,
                "EAF_Ni": float(row["EAF_Ni"]) / 100,
                "EAF_Cu": float(row["EAF_Cu"]) / 100,
            }

            row_id = row.get("id")

            if not _is_missing(row_id):
                grade = session.get(Grade, int(row_id))
                for key, value in values.items():
                    setattr(grade, key, value)
            else:
                grade = Grade(**values)
                session.add(grade)

        session.commit()


def get_eligible_provider_materials():
    """
    Materials selectable as an AOD provider — excludes Bucket Only
    materials, since those aren't meant to be added during AOD.
    """
    with SessionLocal() as session:
        result = session.execute(
            select(MaterialMaster)
            .where(MaterialMaster.bucket_only == False)  # noqa: E712
            .order_by(MaterialMaster.material_name)
        )
        return result.scalars().all()


def get_aod_provider_master():
    with SessionLocal() as session:
        result = session.execute(
            select(AODProvider)
        )
        return result.scalars().all()


def save_aod_provider_master(rows):
    """
    rows: list of dicts, one per fixed element row:
        {"Element": ..., "Primary Material": <name or None>,
         "Alternate Material": <name or None>}
    Element set is fixed (Si, Mn, Cr, Ni, Cu, Nb, Mo) — no add/delete.
    Material names are resolved to ids here. A blank name is allowed
    (primary_material_id may be NULL at the DB level; completeness is
    enforced later at the calculation stage, not here).
    """
    with SessionLocal() as session:

        materials = session.execute(
            select(MaterialMaster)
        ).scalars().all()

        name_to_id = {m.material_name: m.id for m in materials}

        for row in rows:
            element = str(row["Element"]).strip()

            primary_name = row.get("Primary Material")
            alternate_name = row.get("Alternate Material")

            values = {
                "primary_material_id": (
                    name_to_id.get(primary_name)
                    if not _is_missing(primary_name)
                    else None
                ),
                "alternate_material_id": (
                    name_to_id.get(alternate_name)
                    if not _is_missing(alternate_name)
                    else None
                ),
            }

            provider = session.execute(
                select(AODProvider).where(
                    AODProvider.element == element
                )
            ).scalar_one_or_none()

            if provider:
                for key, value in values.items():
                    setattr(provider, key, value)
            else:
                provider = AODProvider(
                    element=element,
                    **values
                )
                session.add(provider)

        session.commit()