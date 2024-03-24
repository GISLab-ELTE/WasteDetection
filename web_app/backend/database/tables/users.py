from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    annotations = relationship("Annotations")

    name = Column(String)
    email = Column(String)
    password = Column(String)
    roles = Column(String)
