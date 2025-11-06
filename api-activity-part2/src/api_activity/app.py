import os

from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_talisman import Talisman


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
            return jsonify({"message": "username and password are required"}), 400
        return jsonify({"message": f"User {username} registered successfully"})


def instantiate_app() -> Flask:
    """Instantiate a new flask app"""
    # Create the flask app
    app = Flask(__name__)
    Talisman(app, force_https=True)
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
    return api


def create_and_serve(debug: bool = True):
    app = instantiate_app()
    initialize_api(app)
    app.run(debug=debug, ssl_context=("MyCertificate.crt", "MyKey.pem"))



def run(app, debug=True):
    """Run the app"""


if __name__ == "__main__":
    run(create_and_serve())
