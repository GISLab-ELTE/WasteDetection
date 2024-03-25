from geoalchemy2 import Geometry
from sqlalchemy.orm import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer


Base = declarative_base()


class Annotation(Base):
    __tablename__ = "annotation"

    id = Column(Integer, primary_key=True)

    satellite_image_id = Column(Integer, ForeignKey("satellite_image.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

    geom = Column(Geometry("POLYGON"))
    waste = Column(Boolean)
