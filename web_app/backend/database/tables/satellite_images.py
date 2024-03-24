from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Date, Float, Integer, String


Base = declarative_base()


class SatelliteImages(Base):
    __tablename__ = "satellite_images"

    id = Column(Integer, primary_key=True)
    annotations = relationship("Annotations")

    filename = Column(String)
    acquisition_data = Column(Date)
    satellite_type = Column(String)
    src = Column(String)
    min = Column(Float)
    max = Column(Float)
