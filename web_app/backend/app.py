import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from config import Config
from flask_cors import CORS
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from flask import Flask, jsonify, request
from model.model import FloodPrediction
from models import db, User, SatelliteImage, Annotation
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import math
import requests
import geopandas as gpd
import rasterio
from shapely.geometry import Point
from pyproj import Transformer
from models import db

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
            return (
                jsonify({"message": "Logged in successfully", "next": next_page}),
                200,
            )
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
        return (
            jsonify(
                {
                    "logged_in": True,
                    "user_id": current_user.id,
                    "email": current_user.email,
                }
            ),
            200,
        )
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


## Flood Forecast API

data_folder = os.getenv("DATA_FOLDER")
if not data_folder:
    raise EnvironmentError("DATA_FOLDER environment variable is not set")

API_URL = os.getenv("API_URL")
if not API_URL:
    raise EnvironmentError("API_URL environment variable is not set")

OVSZ_TOKEN = os.getenv("OVSZ_TOKEN")
if not OVSZ_TOKEN:
    raise EnvironmentError("OVSZ_TOKEN environment variable is not set")

VARID = os.getenv("VARID")
if not VARID:
    raise EnvironmentError("VARID environment variable is not set")
VARID = int(VARID)

HUNGARY_ELEVATION_MODEL = os.getenv("HUNGARY_ELEVATION_MODEL")
if not HUNGARY_ELEVATION_MODEL:
    raise EnvironmentError("HUNGARY_ELEVATION_MODEL environment variable is not set")
HUNGARY_ELEVATION_MODEL = os.path.join(data_folder, HUNGARY_ELEVATION_MODEL)

DISTANCE_LIMIT = os.getenv("STATIONS_DISTANCE_LIMIT")
if not DISTANCE_LIMIT:
    raise EnvironmentError("STATIONS_DISTANCE_LIMIT environment variable is not set")
DISTANCE_LIMIT = int(DISTANCE_LIMIT)

POINT_CRS = os.getenv("POINT_CRS")
if not POINT_CRS:
    raise EnvironmentError("POINT_CRS environment variable is not set")

DEM_CRS = os.getenv("DEM_CRS")
if not DEM_CRS:
    raise EnvironmentError("DEM_CRS environment variable is not set")

FLOOD_ZONES = {
    "medium": os.path.join(
        data_folder,
        (
            os.getenv("FLOOD_ZONE_MEDIUM")
            if os.getenv("FLOOD_ZONE_MEDIUM")
            else (_ for _ in ()).throw(EnvironmentError("FLOOD_ZONE_MEDIUM environment variable is not set"))
        ),
    ),
    "low": os.path.join(
        data_folder,
        (
            os.getenv("FLOOD_ZONE_LOW")
            if os.getenv("FLOOD_ZONE_LOW")
            else (_ for _ in ()).throw(EnvironmentError("FLOOD_ZONE_LOW environment variable is not set"))
        ),
    ),
    "high": os.path.join(
        data_folder,
        (
            os.getenv("FLOOD_ZONE_HIGH")
            if os.getenv("FLOOD_ZONE_HIGH")
            else (_ for _ in ()).throw(EnvironmentError("FLOOD_ZONE_HIGH environment variable is not set"))
        ),
    ),
    "nagyviz": os.path.join(
        data_folder,
        (
            os.getenv("FLOOD_ZONE_NAGYVIZ")
            if os.getenv("FLOOD_ZONE_NAGYVIZ")
            else (_ for _ in ()).throw(EnvironmentError("FLOOD_ZONE_NAGYVIZ environment variable is not set"))
        ),
    ),
}


def get_stations():
    return requests.get(API_URL, params={"view": "getstations", "token": OVSZ_TOKEN}).json()


def get_forecasts(station_id):
    return requests.get(
        API_URL,
        params={
            "view": "getfc",
            "token": OVSZ_TOKEN,
            "varid": VARID,
            "statid": station_id,
            "extended": 1,
        },
    ).json()


def transform_coordinates(lon, lat, source_crs="EPSG:4326", target_crs="EPSG:23700"):
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    ex, ey = transformer.transform(lon, lat)
    return Point(ex, ey)


def get_deposit_elevation(deposit_point):
    return FloodPrediction.get_elevation_from_dem(HUNGARY_ELEVATION_MODEL, deposit_point, POINT_CRS, DEM_CRS)


def find_closest_station(lat, lon, stations):
    closest_station = None
    min_distance = float("inf")
    for station in stations:
        try:
            s_lat = float(station["lat"])
            s_lon = float(station["lon"])
        except (ValueError, KeyError) as e:
            logging.warning(f"Error parsing station coordinates: {e}")
            continue
        distance = FloodPrediction.haversine_distance(lat, lon, s_lat, s_lon)
        if distance < min_distance:
            min_distance = distance
            closest_station = station
    return closest_station


def filter_stations(stations, disable_filtering, target_river, lat, lon, distance_limit=DISTANCE_LIMIT):
    if disable_filtering:
        logging.info("Filtering disabled")
        return stations

    filtered = []
    for station in stations:
        if station.get("water") == target_river:
            try:
                s_lat = float(station["lat"])
                s_lon = float(station["lon"])
            except (ValueError, KeyError) as e:
                logging.warning(f"Error parsing station coordinates: {e}")
                continue
            distance = FloodPrediction.haversine_distance(lat, lon, s_lat, s_lon)
            if distance <= distance_limit:
                filtered.append(station)
    return filtered


def process_station_forecasts(station, lat, lon):
    station_id = station["statid"]
    forecast_data = get_forecasts(station_id)
    nullpoint = float(station.get("nullpoint", 0.0))
    lkv_value = station.get("lkv")
    lnv_value = station.get("lnv")
    lkv_cm = float(lkv_value) if lkv_value is not None else 0.0
    lnv_cm = float(lnv_value) if lnv_value is not None else 0.0

    station_forecasts = []
    abs_levels = []

    if forecast_data.get("entries"):
        for entry in forecast_data["entries"]:
            for forecast in entry.get("forecasts", []):
                value_cm = forecast.get("value")
                if value_cm is not None:
                    abs_level = nullpoint + float(value_cm)
                    abs_levels.append(abs_level)
                    station_forecasts.append(
                        {
                            "date": str(forecast.get("date")),
                            "value_cm": str(round(float(forecast.get("value", 0)))),
                            "abs_level_m": str(round(abs_level, 2)),
                            "conf": f"{round(float(forecast.get('conf', 0)))}",
                        }
                    )

    station_feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [station["lon"], station["lat"]]},
        "properties": {
            "type": "station",
            "statid": station_id,
            "name": station.get("name"),
            "water": station.get("water"),
            "nullpoint_m": nullpoint,
            "lowest_level_cm": lkv_cm,
            "highest_level_cm": lnv_cm,
            "forecasts": station_forecasts,
        },
    }
    return station_feature, abs_levels


def build_deposit_feature(lon, lat, deposit_elevation, avg_abs_level, zones, river):
    risk_status = "FLOODED" if avg_abs_level >= deposit_elevation else "SAFE"
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "type": "waste_deposit",
            "elevation_m": deposit_elevation,
            "avg_abs_water_m": avg_abs_level,
            "flood_zone": zones,
            "flood_risk_status": risk_status,
            "closest_station_river": river,
        },
    }


# --------------------
#  endpoint for flood prediction
# --------------------


@app.route("/flood-forecast", methods=["GET"])
def flood_forecast():
    """
    Endpoint to forecast flood risk for a given deposit location.
    This function performs coordinate transformation, retrieves elevation data,
    finds and filters station data, processes forecast information, and finally
    returns a GeoJSON FeatureCollection.
    """
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        app.logger.error("Invalid latitude or longitude provided.")
        return jsonify({"error": "Invalid latitude or longitude"}), 400

    disable_filtering = request.args.get("disable_filtering", "false").lower() == "true"

    # Transform coordinates and get deposit elevation
    deposit_point = transform_coordinates(lon, lat)
    deposit_elevation = get_deposit_elevation(deposit_point)

    # Retrieve stations
    stations_json = get_stations()
    if not stations_json.get("entries"):
        app.logger.warning("No station data available: %s", stations_json.get("error", "Unknown error"))
        return jsonify({"error": "No station data"}), 404

    stations = stations_json["entries"]

    # Identify the closest station
    closest_station = find_closest_station(lat, lon, stations)
    if not closest_station:
        app.logger.warning("No valid station found near the given location.")
        return jsonify({"error": "No valid station found"}), 404

    river = closest_station.get("water")
    if not river:
        app.logger.warning("Closest station found but it has no associated river.")
        return jsonify({"error": "Closest station has no river"}), 500

    # Filter stations based on the river and distance
    filtered_stations = filter_stations(stations, disable_filtering, river, lat, lon)

    all_levels = []
    station_features = []
    for station in filtered_stations:
        feature, levels = process_station_forecasts(station, lat, lon)
        station_features.append(feature)
        all_levels.extend(levels)

    avg_abs_level = sum(all_levels) / len(all_levels) if all_levels else 0.0

    # Determine flood zones
    zones = FloodPrediction.check_flood_zone(deposit_point, FLOOD_ZONES, DEM_CRS)
    deposit_feature = build_deposit_feature(lon, lat, deposit_elevation, avg_abs_level, zones, river)

    # Combine deposit and station features to geosjon
    features = [deposit_feature] + station_features
    return jsonify({"type": "FeatureCollection", "features": features})
