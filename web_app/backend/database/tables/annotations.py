from sqlalchemy.orm import declarative_base
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer


Base = declarative_base()


class Annotations(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True)

    satellite_image_id = Column(Integer, ForeignKey("satellite_images.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    coords = Column(Float)
    waste = Column(Boolean)
