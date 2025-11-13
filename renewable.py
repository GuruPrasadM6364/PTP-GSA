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
from models import Region, Project, CarbonMetric, Measurement, Target, Report, Base, User, Application
import db_init
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


def validate_phone(phone):
    """Validate 10-digit phone number"""
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_pincode(pincode):
    """Validate 6-digit pincode"""
    pattern = r'^\d{6}$'
    return bool(re.match(pattern, pincode))


def validate_email(email):
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """Validate password (min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit, 1 special char)"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, "Valid password"


def get_user_info():
    """Collect user information with validation"""
    print("=" * 50)
    print("USER INFORMATION FORM")
    print("=" * 50)
    
    # Collect Name
    while True:
        name = input("\nEnter Full Name: ").strip()
        if name:
            break
        print("❌ Name cannot be empty. Please try again.")
    
    # Collect Phone Number
    while True:
        phone = input("Enter Phone Number (10 digits): ").strip()
        if validate_phone(phone):
            break
        print("❌ Invalid phone number. Please enter a valid 10-digit number starting with 6-9.")
    
    # Collect Email
    while True:
        email = input("Enter Email Address: ").strip()
        if validate_email(email):
            break
        print("❌ Invalid email address. Please enter a valid email (e.g., user@example.com).")

    # Collect Password
    while True:
        password = input("Enter Password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char): ").strip()
        is_valid, message = validate_password(password)
        if is_valid:
            break
        print(f"❌ {message}")
    
    # Collect Pincode
    while True:
        pincode = input("Enter Pincode (6 digits): ").strip()
        if validate_pincode(pincode):
            break
        print("❌ Invalid pincode. Please enter a valid 6-digit pincode.")
    
    # Collect Address
    while True:
        address = input("Enter Address: ").strip()
        if address:
            break
        print("❌ Address cannot be empty. Please try again.")
    
    # Store user data
    user_data = {
        'name': name,
        'phone': phone,
        'email': email,
        'pincode': pincode,
        'address': address,
        'password': password,
    }
    
    return user_data


def display_user_info(user_data):
    """Display collected user information"""
    print("\n" + "=" * 50)
    print("COLLECTED INFORMATION")
    print("=" * 50)
    print(f"Name:     {user_data['name']}")
    print(f"Phone:    {user_data['phone']}")
    print(f"Email:    {user_data.get('email', '')}")
    print(f"Pincode:  {user_data['pincode']}")
    print(f"Address:  {user_data['address']}")
    print(f"Password: {'*' * len(user_data['password'])}")
    print("=" * 50)


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


@app.route('/login')
def login_page():
    """Serve the login / user-info HTML page."""
    html_path = os.path.join(os.path.dirname(__file__), 'login.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return "<h1>Login page not found</h1>"


@app.route('/signup')
def signup_page():
    """Serve the signup HTML page."""
    html_path = os.path.join(os.path.dirname(__file__), 'signup.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return "<h1>Signup page not found</h1>"


@app.route('/application')
def application_page():
    """Serve the application form HTML page."""
    html_path = os.path.join(os.path.dirname(__file__), 'application.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return "<h1>Application form not found</h1>"


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


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint for user login with email or phone."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['identifier', 'password', 'login_method']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        identifier = data.get('identifier', '').strip()
        password = data.get('password', '')
        login_method = data.get('login_method')

        if login_method not in ['email', 'phone']:
            return jsonify({'error': 'Invalid login method'}), 400

        if not identifier or not password:
            return jsonify({'error': 'Identifier and password are required'}), 400

        # Validate identifier format
        if login_method == 'email':
            if not validate_email(identifier):
                return jsonify({'error': 'Invalid email format'}), 400
        elif login_method == 'phone':
            if not validate_phone(identifier):
                return jsonify({'error': 'Invalid phone format'}), 400

        # Find user by email or phone
        engine = create_engine(DB_URL, future=True)
        with Session(engine) as session:
            if login_method == 'email':
                user = session.query(User).filter(User.email == identifier).first()
                if not user:
                    return jsonify({'error': 'User not found with this email'}), 401
            else:  # phone
                user = session.query(User).filter(User.phone == identifier).first()
                if not user:
                    return jsonify({'error': 'User not found with this phone number'}), 401

            # Verify password
            if not user.password_hash or not check_password_hash(user.password_hash, password):
                return jsonify({'error': 'Invalid password'}), 401

            # Successful login
            return jsonify({
                'success': True,
                'message': f'Login successful! Welcome, {user.name}',
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

        # Optional: validate email and password if provided
        email = data.get('email')
        password = data.get('password')
        if email and not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        if password:
            ok, msg = validate_password(password)
            if not ok:
                return jsonify({'error': f'Password invalid: {msg}'}), 400
        
        # Save to database
        engine = create_engine(DB_URL, future=True)
        with Session(engine) as session:
            user = User(
                name=data['name'],
                phone=data['phone'],
                email=email,
                password_hash=generate_password_hash(password) if password else None,
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


@app.route('/api/applications', methods=['POST'])
def api_submit_application():
    """API endpoint to submit an application."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['name', 'phone', 'pincode', 'email', 'source']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate fields
        if not validate_phone(data['phone']):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        if not validate_pincode(data['pincode']):
            return jsonify({'error': 'Invalid pincode format'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        source = data['source']
        if source not in ['Solar', 'Wind', 'Hydro']:
            return jsonify({'error': 'Invalid renewable source'}), 400
        
        # Save to database
        engine = create_engine(DB_URL, future=True)
        with Session(engine) as session:
            application = Application(
                name=data['name'],
                phone=data['phone'],
                pincode=data['pincode'],
                email=data['email'],
                source=source
            )
            session.add(application)
            session.commit()
            return jsonify({
                'success': True,
                'message': 'Application submitted successfully!',
                'application_id': application.id
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
    parser.add_argument(
        "command",
        choices=["init-db", "seed", "list-regions", "list-projects", "serve", "collect-user-info"],
        help="command to run",
    )
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
                    email=user_info.get('email'),
                    password_hash=generate_password_hash(user_info['password']) if user_info.get('password') else None,
                    pincode=user_info['pincode'],
                    address=user_info['address'],
                )
                session.add(user)
                session.commit()
                print(f"\n✅ User information saved to database with ID: {user.id}")
        except Exception as e:
            print(f"\n❌ Error saving to database: {str(e)}")


if __name__ == "__main__":
	main()

