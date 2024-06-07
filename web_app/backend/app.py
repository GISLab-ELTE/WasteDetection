from flask import Flask, jsonify, request
from flask_migrate import Migrate
from config import Config
from models import db, User, SatelliteImage, Annotation
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from flask import Flask, jsonify, request, redirect, url_for, session
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from config import Config
from models import db, User, SatelliteImage, Annotation

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    user = User(name=data["name"], email=data["email"], role=data["role"])
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()
    if user and user.check_password(data["password"]):
        login_user(user)
        return jsonify({"message": "Logged in successfully"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/protected", methods=["GET"])
@login_required
def protected():
    return jsonify(current_user.to_dict()), 200


@app.route("/current_user", methods=["GET"])
@login_required
def get_current_user():
    return jsonify(current_user.to_dict()), 200


@app.route("/satellite_images", methods=["POST"])
@login_required
def create_satellite_image():
    data = request.get_json()
    image = SatelliteImage(
        filename=data["filename"],
        # acquisition_date=data['acquisition_date'],
        acquisition_date=datetime.strptime(data["acquisition_date"], "%Y-%m-%d"),
        satellite_type=data["satellite_type"],
        src=data["src"],
        min=data["min"],
        max=data["max"],
    )
    db.session.add(image)
    db.session.commit()
    return jsonify({"id": image.id}), 201


@app.route("/annotations", methods=["POST"])
@login_required
def create_annotation():
    data = request.get_json()
    annotation = Annotation(
        satellite_image_id=data["satellite_image_id"],
        user_id=data["user_id"],
        # geom=data['geom'],
        waste=data["waste"],
    )
    try:
        db.session.add(annotation)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Foreign key constraint violation"}), 400
    return jsonify({"id": annotation.id}), 201


@app.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"result": "success"}), 200


@app.route("/satellite_images/<int:image_id>", methods=["DELETE"])
@login_required
def delete_satellite_image(image_id):
    image = SatelliteImage.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    return jsonify({"result": "success"}), 200


@app.route("/annotations/<int:annotation_id>", methods=["DELETE"])
@login_required
def delete_annotation(annotation_id):
    annotation = Annotation.query.get_or_404(annotation_id)
    db.session.delete(annotation)
    db.session.commit()
    return jsonify({"result": "success"}), 200


@app.route("/users", methods=["GET"])
@login_required
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@app.route("/satellite_images", methods=["GET"])
@login_required
def get_satellite_images():
    images = SatelliteImage.query.all()
    return jsonify([image.to_dict() for image in images]), 200


@app.route("/annotations", methods=["GET"])
@login_required
def get_annotations():
    annotations = Annotation.query.all()
    return jsonify([annotation.to_dict() for annotation in annotations]), 200


@app.route("/users/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


@app.route("/satellite_images/<int:image_id>", methods=["GET"])
@login_required
def get_satellite_image(image_id):
    image = SatelliteImage.query.get_or_404(image_id)
    return jsonify(image.to_dict()), 200


@app.route("/annotations/<int:annotation_id>", methods=["GET"])
@login_required
def get_annotation(annotation_id):
    annotation = Annotation.query.get_or_404(annotation_id)
    return jsonify(annotation.to_dict()), 200


if __name__ == "__main__":
    app.run(debug=True)
