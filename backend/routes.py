from flask import Blueprint, request, jsonify, send_from_directory, current_app
from backend.models import db, Job
from datetime import datetime
import os

job_routes = Blueprint('job_routes', __name__)


@job_routes.route('/')
def serve_index():
    return send_from_directory(os.path.join(current_app.root_path, 'frontend'), 'index.html')


@job_routes.route('/<path:filename>')
def serve_static_files(filename):
    if filename.startswith("jobs") or filename.startswith("api"):
        return "Not found", 404
    return send_from_directory(os.path.join(current_app.root_path, 'frontend'), filename)


@job_routes.route('/jobs', methods=['GET'])
def get_jobs():
    try:
        jobs = Job.query.order_by(Job.date_posted.desc()).all()
        return jsonify([job_to_dict(job) for job in jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@job_routes.route('/jobs', methods=['POST'])
def add_job():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        if not data.get('title') or not data.get('company'):
            return jsonify({'error': 'Title and company are required'}), 400

        job = Job(
            title=data['title'],
            company=data['company'],
            location=data.get('location', ''),
            job_type=data.get('job_type', ''),
            tags=','.join(data.get('tags', [])) if data.get('tags') else None
        )

        db.session.add(job)
        db.session.commit()
        return jsonify(job_to_dict(job)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@job_routes.route('/jobs/<int:id>', methods=['PUT'])
def update_job(id):
    job = Job.query.get_or_404(id)
    data = request.json

    job.title = data['title']
    job.company = data['company']
    job.location = data.get('location')
    job.job_type = data.get('job_type')
    job.tags = ','.join(data.get('tags', []))

    db.session.commit()
    return jsonify(job_to_dict(job))



@job_routes.route('/jobs/<int:id>', methods=['DELETE'])
def delete_job(id):
    try:
        job = Job.query.get_or_404(id)
        db.session.delete(job)
        db.session.commit()
        return jsonify({'message': 'Job deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def job_to_dict(job):
    return {
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'posting_date': job.date_posted.isoformat(),
        'job_type': job.job_type,
        'tags': job.tags.split(',') if job.tags else []
    }