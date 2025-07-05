from datetime import datetime
from backend.database import db

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)  # Make sure this matches in your HTML/JS
    job_type = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.String(255), nullable=True)
