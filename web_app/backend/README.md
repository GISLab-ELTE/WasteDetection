1. `set FLASK_APP=app.py`
2. `flask db init`
3. `flask db migrate -m "Initial migration."`
4. `flask db upgrade`
5. `flask run`

- `CREATE DATABASE waste_detection_database;`
- `\c waste_detection_database;`
- `CREATE EXTENSION postgis;`

- `psql -U postgres`
- `\q`
- `DROP DATABASE waste_detection_database;`
