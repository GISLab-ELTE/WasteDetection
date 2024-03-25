from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    annotations = relationship("Annotation")

    name = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(String)
