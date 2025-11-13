"""Simple CLI to manage the renewable DB.

Commands:
  init-db    : create database and tables
  seed       : seed sample data
  list-regions: list regions
  list-projects: list projects
  serve      : run web server to view landing page
  collect-user-info: collect user information interactively

This file uses the ORM in `models.py` and the helper in `db_init.py`.
"""
import argparse
from flask import Flask, render_template_string, request, jsonify
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from models import Region, Project, CarbonMetric, Measurement, Target, Report, Base, User
import db_init
import os
from details_collection import get_user_info, display_user_info, validate_phone, validate_pincode


DB_URL = "sqlite:///renewable.db"

# Initialize Flask app
app = Flask(__name__)


def load_html_template():
    """Load the landing.html file."""
    html_path = os.path.join(os.path.dirname(__file__), 'landing.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return "<h1>Landing page not found</h1>"


@app.route('/')
def index():
    """Serve the landing page."""
    html_content = load_html_template()
    return html_content


@app.route('/api/regions')
def api_regions():
    """API endpoint to get all regions."""
    from flask import jsonify # pyright: ignore[reportMissingImports]
    engine = create_engine(DB_URL, future=True)
    with Session(engine) as session:
        rows = session.query(Region).order_by(Region.region_type, Region.name).all()
        return jsonify([{'id': r.id, 'name': r.name, 'type': r.region_type} for r in rows])


@app.route('/api/projects')
def api_projects():
    """API endpoint to get all projects."""
    from flask import jsonify
    engine = create_engine(DB_URL, future=True)
    with Session(engine) as session:
        rows = session.query(Project).order_by(Project.name).all()
        return jsonify([{'id': p.id, 'name': p.name} for p in rows])


@app.route('/api/users', methods=['GET'])
def api_get_users():
    """API endpoint to get all users."""
    engine = create_engine(DB_URL, future=True)
    with Session(engine) as session:
        rows = session.query(User).order_by(User.id).all()
        return jsonify([{
            'id': u.id,
            'name': u.name,
            'phone': u.phone,
            'pincode': u.pincode,
            'address': u.address,
            'created_at': u.created_at.isoformat()
        } for u in rows])


@app.route('/api/users', methods=['POST'])
def api_submit_user():
    """API endpoint to submit user information."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['name', 'phone', 'pincode', 'address']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate phone and pincode
        if not validate_phone(data['phone']):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        if not validate_pincode(data['pincode']):
            return jsonify({'error': 'Invalid pincode format'}), 400
        
        # Save to database
        engine = create_engine(DB_URL, future=True)
        with Session(engine) as session:
            user = User(
                name=data['name'],
                phone=data['phone'],
                pincode=data['pincode'],
                address=data['address']
            )
            session.add(user)
            session.commit()
            return jsonify({
                'success': True,
                'message': 'User information saved successfully',
                'user_id': user.id
            }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def list_regions(engine_url: str = DB_URL) -> None:
    engine = create_engine(engine_url, future=True)
    with Session(engine) as session:
        rows = session.query(Region).order_by(Region.region_type, Region.name).all()
        for r in rows:
            print(r)


def list_projects(engine_url: str = DB_URL) -> None:
    engine = create_engine(engine_url, future=True)
    with Session(engine) as session:
        rows = session.query(Project).order_by(Project.name).all()
        for p in rows:
            print(p)


def main():
	parser = argparse.ArgumentParser(description="Manage renewable database")
	parser.add_argument("command", choices=["init-db", "seed", "list-regions", "list-projects", "serve", "collect-user-info"], help="command to run")
	args = parser.parse_args()

	if args.command == "init-db":
		db_init.init_db(DB_URL)
	elif args.command == "seed":
		db_init.seed_sample(DB_URL)
	elif args.command == "list-regions":
		list_regions(DB_URL)
	elif args.command == "list-projects":
		list_projects(DB_URL)
	elif args.command == "serve":
		print("Starting web server at http://localhost:5000")
		app.run(debug=True, host='0.0.0.0', port=5000)
	elif args.command == "collect-user-info":
		user_info = get_user_info()
		display_user_info(user_info)
		try:
			engine = create_engine(DB_URL, future=True)
			with Session(engine) as session:
				user = User(
					name=user_info['name'],
					phone=user_info['phone'],
					pincode=user_info['pincode'],
					address=user_info['address']
				)
				session.add(user)
				session.commit()
				print(f"\n✅ User information saved to database with ID: {user.id}")
		except Exception as e:
			print(f"\n❌ Error saving to database: {str(e)}")


if __name__ == "__main__":
	main()

