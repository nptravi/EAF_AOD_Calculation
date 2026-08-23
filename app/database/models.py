from sqlalchemy import Column, Integer, String, Float, CheckConstraint, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True)
    unit_code = Column(
        Integer,
        ForeignKey("units.unit_code"),
        nullable=False,
        unique=True
    )
    unit_name = Column(String(50), nullable=False)


class RecoveryMaster(Base):
    __tablename__ = "recovery_master"

    id = Column(Integer, primary_key=True)
    unit_code = Column(Integer, nullable=False, unique=True)

    Fe = Column(Float, nullable=False, default=0)
    C = Column(Float, nullable=False, default=0)
    Si = Column(Float, nullable=False, default=0)
    Mn = Column(Float, nullable=False, default=0)
    Cr = Column(Float, nullable=False, default=0)
    Ni = Column(Float, nullable=False, default=0)
    Cu = Column(Float, nullable=False, default=0)
    Ti = Column(Float, nullable=False, default=0)
    Nb = Column(Float, nullable=False, default=0)
    Mo = Column(Float, nullable=False, default=0)
    P = Column(Float, nullable=False, default=0)
    S = Column(Float, nullable=False, default=0)
    N = Column(Float, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("Fe >= 0 AND Fe <= 1", name="ck_recovery_fe"),
        CheckConstraint("C >= 0 AND C <= 1", name="ck_recovery_c"),
        CheckConstraint("Si >= 0 AND Si <= 1", name="ck_recovery_si"),
        CheckConstraint("Mn >= 0 AND Mn <= 1", name="ck_recovery_mn"),
        CheckConstraint("Cr >= 0 AND Cr <= 1", name="ck_recovery_cr"),
        CheckConstraint("Ni >= 0 AND Ni <= 1", name="ck_recovery_ni"),
        CheckConstraint("Cu >= 0 AND Cu <= 1", name="ck_recovery_cu"),
        CheckConstraint("Ti >= 0 AND Ti <= 1", name="ck_recovery_ti"),
        CheckConstraint("Nb >= 0 AND Nb <= 1", name="ck_recovery_nb"),
        CheckConstraint("Mo >= 0 AND Mo <= 1", name="ck_recovery_mo"),
        CheckConstraint("P >= 0 AND P <= 1", name="ck_recovery_p"),
        CheckConstraint("S >= 0 AND S <= 1", name="ck_recovery_s"),
        CheckConstraint("N >= 0 AND N <= 1", name="ck_recovery_n"),
    )


class MaterialMaster(Base):
    __tablename__ = "material_master"

    id = Column(Integer, primary_key=True)

    # Internal only — user never sees or enters this.
    material_code = Column(Integer, nullable=False, unique=True)

    material_name = Column(String(100), nullable=False, unique=True)

    bucket_only = Column(Boolean, nullable=False, default=False)

    lpp = Column(Float, nullable=True)

    # Fe is intentionally NOT stored — always calculated as
    # balance (1 - sum of the others) wherever needed.
    C = Column(Float, nullable=False, default=0)
    Si = Column(Float, nullable=False, default=0)
    Mn = Column(Float, nullable=False, default=0)
    Cr = Column(Float, nullable=False, default=0)
    Ni = Column(Float, nullable=False, default=0)
    Cu = Column(Float, nullable=False, default=0)
    Ti = Column(Float, nullable=False, default=0)
    Nb = Column(Float, nullable=False, default=0)
    Mo = Column(Float, nullable=False, default=0)
    P = Column(Float, nullable=False, default=0)
    S = Column(Float, nullable=False, default=0)
    N = Column(Float, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("C >= 0 AND C <= 1", name="ck_material_c"),
        CheckConstraint("Si >= 0 AND Si <= 1", name="ck_material_si"),
        CheckConstraint("Mn >= 0 AND Mn <= 1", name="ck_material_mn"),
        CheckConstraint("Cr >= 0 AND Cr <= 1", name="ck_material_cr"),
        CheckConstraint("Ni >= 0 AND Ni <= 1", name="ck_material_ni"),
        CheckConstraint("Cu >= 0 AND Cu <= 1", name="ck_material_cu"),
        CheckConstraint("Ti >= 0 AND Ti <= 1", name="ck_material_ti"),
        CheckConstraint("Nb >= 0 AND Nb <= 1", name="ck_material_nb"),
        CheckConstraint("Mo >= 0 AND Mo <= 1", name="ck_material_mo"),
        CheckConstraint("P >= 0 AND P <= 1", name="ck_material_p"),
        CheckConstraint("S >= 0 AND S <= 1", name="ck_material_s"),
        CheckConstraint("N >= 0 AND N <= 1", name="ck_material_n"),
    )


class Grade(Base):
    __tablename__ = "grade_master"

    id = Column(Integer, primary_key=True)

    grade_name = Column(
        String(100),
        nullable=False,
        unique=True
    )

    C = Column(Float, nullable=False, default=0)
    Si = Column(Float, nullable=False, default=0)
    Mn = Column(Float, nullable=False, default=0)
    Cr = Column(Float, nullable=False, default=0)
    Ni = Column(Float, nullable=False, default=0)
    Cu = Column(Float, nullable=False, default=0)
    Ti = Column(Float, nullable=False, default=0)
    Nb = Column(Float, nullable=False, default=0)
    Mo = Column(Float, nullable=False, default=0)
    P = Column(Float, nullable=False, default=0)
    S = Column(Float, nullable=False, default=0)
    N = Column(Float, nullable=False, default=0)

    EAF_C = Column(Float, nullable=False, default=0)
    EAF_Cr = Column(Float, nullable=False, default=0)
    EAF_Ni = Column(Float, nullable=False, default=0)
    EAF_Cu = Column(Float, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("C >= 0 AND C <= 1", name="ck_grade_c"),
        CheckConstraint("Si >= 0 AND Si <= 1", name="ck_grade_si"),
        CheckConstraint("Mn >= 0 AND Mn <= 1", name="ck_grade_mn"),
        CheckConstraint("Cr >= 0 AND Cr <= 1", name="ck_grade_cr"),
        CheckConstraint("Ni >= 0 AND Ni <= 1", name="ck_grade_ni"),
        CheckConstraint("Cu >= 0 AND Cu <= 1", name="ck_grade_cu"),
        CheckConstraint("Ti >= 0 AND Ti <= 1", name="ck_grade_ti"),
        CheckConstraint("Nb >= 0 AND Nb <= 1", name="ck_grade_nb"),
        CheckConstraint("Mo >= 0 AND Mo <= 1", name="ck_grade_mo"),
        CheckConstraint("P >= 0 AND P <= 1", name="ck_grade_p"),
        CheckConstraint("S >= 0 AND S <= 1", name="ck_grade_s"),
        CheckConstraint("N >= 0 AND N <= 1", name="ck_grade_n"),
        CheckConstraint("EAF_C >= 0 AND EAF_C <= 1", name="ck_grade_eaf_c"),
        CheckConstraint("EAF_Cr >= 0 AND EAF_Cr <= 1", name="ck_grade_eaf_cr"),
        CheckConstraint("EAF_Ni >= 0 AND EAF_Ni <= 1", name="ck_grade_eaf_ni"),
        CheckConstraint("EAF_Cu >= 0 AND EAF_Cu <= 1", name="ck_grade_eaf_cu"),
    )


class AODProvider(Base):
    __tablename__ = "aod_provider_master"

    id = Column(Integer, primary_key=True)

    element = Column(
        String(10),
        nullable=False,
        unique=True
    )

    primary_material_id = Column(
        Integer,
        ForeignKey("material_master.id"),
        nullable=True
    )

    alternate_material_id = Column(
        Integer,
        ForeignKey("material_master.id"),
        nullable=True
    )