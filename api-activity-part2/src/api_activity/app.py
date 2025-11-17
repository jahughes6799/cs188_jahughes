import os
import pyodbc

from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_talisman import Talisman
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()



# Create the "hello" resource
class Hello(Resource):
    """A simple resource that for returning a hello message."""

    # Get is a special method for a resource.
    def get(self):
        return jsonify({"message": "Hello World!"})


class Square(Resource):
    """A simple resource that calculates the area of a square."""

    def get(self, num):
        return jsonify({"Shape": __class__.__name__, "Area": num * num})


class Echo(Resource):
    """A simple resource that echoes the arguments passed to it."""

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("arg1", type=str, location="args")
        parser.add_argument("arg2", type=str, location="args")

        arguments = parser.parse_args()

        # Return the arguments as JSON
        return jsonify(arguments)
    

class Register(Resource):
    def put(self):
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        if not username or not password:
            return {"message": "username and password are required"}, 400

        cs = os.getenv("SQL_CONNECTIONSTRING", "")
        if not cs:
            return {"message": "server misconfigured: missing SQL_CONNECTIONSTRING"}, 500

        # build ODBC conn string from ADO.NET style
        parts = {}
        for seg in cs.split(";"):
            if "=" in seg:
                k, v = seg.split("=", 1)
                parts[k.strip().lower()] = v.strip()
        server = parts.get("server", "").replace("tcp:", "")
        database = parts.get("initial catalog", "")
        uid = parts.get("user id", "")
        pwd = parts.get("password", "")
        odbc_cs = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={server};DATABASE={database};UID={uid};PWD={pwd};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"
        )

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            import pyodbc
            with pyodbc.connect(odbc_cs) as conn:
                cur = conn.cursor()
                # assumes a table [dbo].[Users] with columns (username NVARCHAR, passwordhash NVARCHAR, created_at DATETIME2 default sysutcdatetime())
                cur.execute(
                    "INSERT INTO dbo.Users (username, passwordhash) VALUES (?, ?)",
                    (username, pw_hash),
                )
                conn.commit()
            return {"message": f"User {username} registered successfully"}
        except Exception as e:
            # 2627 / 2601 are duplicate key/unique constraint
            if "2627" in str(e) or "2601" in str(e):
                return {"message": "username already exists"}, 409
            return {"message": f"db error: {e}"}, 500

    
class ConfigCheck(Resource):
    def get(self):
        cs = os.getenv("SQL_CONNECTIONSTRING", "")
        # mask password in any preview
        parts = []
        for p in cs.split(";"):
            if not p:
                continue
            if p.lower().startswith("password="):
                parts.append("Password=****")
            else:
                parts.append(p)
        return jsonify({
            "has_sql_connectionstring": bool(cs),
            "connection_string_preview": ";".join(parts)[:160]
        })

class DbPing(Resource):
    def get(self):
        cs = os.getenv("SQL_CONNECTIONSTRING", "")
        if not cs:
            return {"ok": False, "error": "SQL_CONNECTIONSTRING missing"}, 500

        # Parse ADO.NET string into a dict
        parts = {}
        for seg in cs.split(";"):
            if "=" in seg:
                k, v = seg.split("=", 1)
                parts[k.strip().lower()] = v.strip()

        server = parts.get("server", "").replace("tcp:", "")
        database = parts.get("initial catalog", "")
        uid = parts.get("user id", "")
        pwd = parts.get("password", "")

        odbc_cs = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={server};DATABASE={database};UID={uid};PWD={pwd};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"
        )

        try:
            with pyodbc.connect(odbc_cs) as conn:
                cur = conn.cursor()
                cur.execute("SELECT TOP 1 GETDATE()")
                row = cur.fetchone()
                return {"ok": True, "server_time": str(row[0])}
        except Exception as e:
            # Helpful message if local ODBC driver isn't installed
            return {"ok": False, "error": str(e)} , 500

def instantiate_app() -> Flask:
    app = Flask(__name__)
    bcrypt.init_app(app)
    # Disable HTTPS redirect during tests so responses are 200 (not 302)
    is_testing = bool(os.getenv("PYTEST_CURRENT_TEST")) or os.getenv("FLASK_TESTING") == "1"
    Talisman(app, force_https=not is_testing)
    return app


def initialize_api(app: Flask) -> Api:
    """Initialize the api for the app and add resources to it"""

    # Create the API object
    api = Api(app)

    # Add the resources we want
    api.add_resource(Hello, "/")
    api.add_resource(Square, "/square/<int:num>")
    api.add_resource(Echo, "/echo")
    api.add_resource(Register, "/register")
    api.add_resource(ConfigCheck, "/config-check")
    api.add_resource(DbPing, "/db-ping")
    return api


def create_and_serve(debug: bool = True):
    app = instantiate_app()
    initialize_api(app)
    app.run(debug=debug, ssl_context=("MyCertificate.crt", "MyKey.pem"))



def run(app, debug=True):
    """Run the app"""


if __name__ == "__main__":
    run(create_and_serve())
