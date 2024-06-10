from datetime import datetime
from flask_bcrypt import Bcrypt
from geoalchemy2 import Geometry
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    annotations = db.relationship("Annotation", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}


class SatelliteImage(db.Model):
    __tablename__ = "satellite_image"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    acquisition_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    satellite_type = db.Column(db.String(64), nullable=False)
    src = db.Column(db.String(256), nullable=False)
    min = db.Column(db.Float, nullable=False)
    max = db.Column(db.Float, nullable=False)
    annotations = db.relationship("Annotation", backref="satellite_image", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "acquisition_date": self.acquisition_date.isoformat(),
            "satellite_type": self.satellite_type,
            "src": self.src,
            "min": self.min,
            "max": self.max,
        }


class Annotation(db.Model):
    __tablename__ = "annotation"
    id = db.Column(db.Integer, primary_key=True)
    satellite_image_id = db.Column(db.Integer, db.ForeignKey("satellite_image.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    geom = db.Column(Geometry("POLYGON"), nullable=False)
    waste = db.Column(db.Boolean, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "satellite_image_id": self.satellite_image_id,
            "user_id": self.user_id,
            "geom": str(self.geom),
            "waste": self.waste,
        }
