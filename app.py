from flask import Flask
from flask_cors import CORS
from backend.database import db
from backend.config import Config
from backend.routes import job_routes
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)
app.register_blueprint(job_routes)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)