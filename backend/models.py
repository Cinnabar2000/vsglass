from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class GlassType(Base):
    __tablename__ = 'glass_type'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    length = Column(Float)
    width = Column(Float)

    remnants = relationship("GlassRemnant", back_populates="glass_type")


class GlassRemnant(Base):
    __tablename__ = 'glass_remnants'

    id = Column(Integer, primary_key=True)
    glass_type_id = Column(Integer, ForeignKey('glass_type.id'))
    length = Column(Float)
    width = Column(Float)

    glass_type = relationship("GlassType", back_populates="remnants")
