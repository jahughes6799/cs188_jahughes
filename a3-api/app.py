from flask import Flask, request
from flask_restful import Api, Resource

class Hello(Resource):
    def get(self):
        return {"message": "Hello from A3"}, 200

class Echo(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        return {"you_sent": data}, 201

def create_app():
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(Hello, "/")
    api.add_resource(Echo, "/echo")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
