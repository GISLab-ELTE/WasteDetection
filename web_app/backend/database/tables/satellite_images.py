from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Date, Float, Integer, String


Base = declarative_base()


class SatelliteImage(Base):
    __tablename__ = "satellite_image"

    id = Column(Integer, primary_key=True)
    annotations = relationship("Annotation")

    filename = Column(String)
    acquisition_data = Column(Date)
    satellite_type = Column(String)
    src = Column(String)
    min = Column(Float)
    max = Column(Float)
