import logging
import os

from config import Config
from flask_cors import CORS
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from flask import Flask, jsonify, request
from models import db, User, SatelliteImage, Annotation
from flask_login import LoginManager, login_user, logout_user, login_required, current_user


# Create app
app = Flask(__name__)

# Configure application and logger
Config.check_env_variables()
app.config.from_object(Config)
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
gunicorn_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# Enable CORS override when debugging
if os.getenv("FLASK_DEBUG") == "True":
    CORS(app, supports_credentials=True, origins=[os.getenv("FLASK_CORS_ORIGIN")])

# Initialize db communication
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def log_request_info():
    app.logger.info("Request: %s %s", request.method, request.url)


@app.after_request
def log_response_info(response):
    app.logger.info("Response: %s %s %s", request.method, request.url, response.status)
    return response


@app.route("/users", methods=["POST"])
@login_required
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
        next_page = request.args.get("next")
        if next_page:
            return jsonify({"message": "Logged in successfully", "next": next_page}), 200
        else:
            return jsonify({"message": "Logged in successfully"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/check-login", methods=["GET"])
def check_login():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "user_id": current_user.id, "email": current_user.email}), 200
    else:
        return jsonify({"logged_in": False}), 200


@app.route("/current-user", methods=["GET"])
@login_required
def get_current_user():
    return jsonify(current_user.to_dict()), 200


@app.route("/satellite-images", methods=["POST"])
@login_required
def create_satellite_image():
    data = request.get_json()
    image = SatelliteImage(
        filename=data["filename"],
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
        geom=f'SRID=3857;{data["geom"]}',
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


@app.route("/satellite-images/<int:image_id>", methods=["DELETE"])
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


@app.route("/satellite-images", methods=["GET"])
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


@app.route("/satellite-images/<int:image_id>", methods=["GET"])
@login_required
def get_satellite_image(image_id):
    image = SatelliteImage.query.get_or_404(image_id)
    return jsonify(image.to_dict()), 200


@app.route("/annotations/<int:annotation_id>", methods=["GET"])
@login_required
def get_annotation(annotation_id):
    annotation = Annotation.query.get_or_404(annotation_id)
    return jsonify(annotation.to_dict()), 200


@app.route("/get-annotations-for-current-user-and-current-satellite-image", methods=["POST"])
@login_required
def get_annotations_for_current_user_and_current_satellite_image():
    user_id = current_user.id
    satellite_image_id = request.get_json()["satellite_image_id"]

    annotations = Annotation.query.filter_by(user_id=user_id, satellite_image_id=satellite_image_id).all()

    coordinates_query = [
        f"SELECT ST_AsGeoJSON(geom) FROM annotation WHERE id = {annotation.id}" for annotation in annotations
    ]
    coordinates = [db.session.execute(query).fetchone()[0] for query in coordinates_query]

    return jsonify(coordinates), 200


@app.route("/get-satellite-image-id", methods=["POST"])
@login_required
def get_satellite_image_id():
    filename = request.get_json()["filename"]

    if not filename:
        return jsonify({"error": "Missing filename parameter"}), 400

    satellite_image = SatelliteImage.query.filter_by(filename=filename).first()

    if satellite_image:
        return jsonify({"satellite_image_id": satellite_image.id}), 200
    else:
        return jsonify({"error": "Satellite image not found"}), 404
