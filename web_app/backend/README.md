# Dockerized Flask Application Backend

## `ENV` variables

In the [`Dockerfile`](../../Dockerfile), several environment variables (`ENV`) are configured, each serving a specific purpose:

- Required `ENV` variables for `docker run`:
  - `FLASK_SECRET_KEY`: It is used to secure sessions, protect against CSRF attacks, and ensure data integrity through cryptographic signing.
  - `PSQL_DATABASE_URL`: URL for PosgreSQL database.
    - Example: `postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}`
- Optional `ENV` variables for `docker run`:
  - `FLASK_APP`: Specifies the relative path to the `app.py` file that contains the Flask application.
    - Default: `app.py`
  - `FLASK_APP_HOST`: Defines the host address for the Flask application within the container.
    - Default: `0.0.0.0`
  - `FLASK_APP_PORT`: Determines the port on which the Flask application will run inside the container.
    - Default: `5000`
  - `FLASK_DEBUG`: Enables CORS override if set to `True`.
    - Default: `False`
  - `FLASK_CORS_ORIGIN`: Specifies the origin allowed for requests when `FLASK_DEBUG` is set to `True`.
    - Default: `http://localhost:5173`
  - `GUNICORN_WORKERS`: Specifies the number of worker processes to handle multiple requests concurrently.
    - Default: `5`

## Running the container

1. **Open CMD:** navigate to repository folder.
2. **Build image:**

   ```bash
      docker build . --target web_app_backend -t web_app_backend
   ```

3. **Run container:**

   ```bash
      docker run -d --name web_app_backend_container \
        -e FLASK_SECRET_KEY={SECRET_KEY} \
        -e PSQL_DATABASE_URL=postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME} \
        --net=host \
        --restart always \
        gitlab.inf.elte.hu:5050/gislab/waste-detection/web_app_backend
   ```

4. **Run container locally (development only):**

- **Create PostgreSQL Database with PostGIS Extension:**

  ```bash
     psql -U postgres

     CREATE DATABASE waste_detection_database;

     \c waste_detection_database;

     CREATE EXTENSION postgis;

     \q

     # DROP DATABASE waste_detection_database;
  ```

- **Run container:**

  Be sure to verify the values of the other `ENV` variables listed above.

  ```bash
     docker run --rm -it --name web_app_backend_container \
       -e FLASK_SECRET_KEY=secret_key \
       -e PSQL_DATABASE_URL=postgresql://postgres:admin@192.168.1.118:5432/waste_detection_database \
       -p 5000:5000 \
       web_app_backend
  ```

## `curl` commands for endpoints:

- Login:
  ```bash
    curl -c cookies.txt -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d "{\"email\": \"john@example.com\", \"password\": \"password123\"}"
  ```
- Add user:
  ```bash
    curl -X POST http://127.0.0.1:5000/users -H "Content-Type: application/json" -d "{\"name\": \"John Doe\", \"email\": \"john@example.com\", \"password\": \"password123\", \"role\": \"admin\"}"
  ```
- Add satellite image:
  ```bash
    curl -b cookies.txt -X POST http://127.0.0.1:5000/satellite-images -H "Content-Type: application/json" -d "{\"filename\": \"image1.tif\", \"acquisition_date\": \"2023-06-01\", \"satellite_type\": \"Landsat\", \"src\": \"NASA\", \"min\": 0.0, \"max\": 255.0}"
  ```
