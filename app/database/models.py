from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True)
    unit_code = Column(Integer, unique=True, nullable=False)
    unit_name = Column(String(50), nullable=False)