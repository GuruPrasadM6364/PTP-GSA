"""Simple CLI to manage the renewable DB.

Commands:
  init-db    : create database and tables
  seed       : seed sample data
  list-regions: list regions
  list-projects: list projects
  serve      : run web server to view landing page
  collect-user-info: collect user information interactively
  predict    : run the predictive renewable adoption model (plot)

This file uses the ORM in `models.py` and the helper in `db_init.py`.
"""
import argparse
from flask import Flask, render_template_string, request, jsonify, send_file
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from models import Region, Project, CarbonMetric, Measurement, Target, Report, Base, User, Application
import db_init
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import predective


def get_ai_suggestion(units, co2):
    """AI suggestion system for energy-saving tips based on usage and emissions."""
    if units <= 50:
        return "🌿 Excellent! Your consumption is very low. Keep it up by continuing to use efficient LED bulbs and solar charging devices."
    elif units <= 150:
        return "⚙️ Moderate consumption detected. Consider unplugging idle electronics and using smart power strips to reduce standby losses."
    elif units <= 300:
        return "⚡ Your electricity usage is on the higher side. Try scheduling high-power tasks during off-peak hours, and switch to inverter-based appliances."
    elif units <= 600:
        return "🔥 Heavy usage! You might benefit from a partial solar panel setup to offset your grid use. Monitor your cooling/heating appliances — they're often major contributors."
    else:
        return "🚨 Very high energy usage detected! Consider a full renewable energy plan or energy audit. Switching to solar or wind power could reduce over 70% of your CO₂ emissions."


def calculate_savings_data(months_data):
    """Calculate carbon and cost savings from renewable energy."""
    emission_factor = 0.85  # kg CO₂ per kWh (grid)
    renewable_factor = 0.05  # kg CO₂ per kWh (renewable)
    cost_per_unit = 7.0  # ₹7 per kWh
    renewable_cost_per_unit = 2.5  # ₹2.5 per kWh (renewable)
    
    results = []
    total_grid_co2 = 0
    total_renewable_co2 = 0
    total_grid_cost = 0
    total_renewable_cost = 0
    
    for month_name, units in months_data:
        grid_co2 = units * emission_factor
        renewable_co2 = units * renewable_factor
        grid_cost = units * cost_per_unit
        renewable_cost = units * renewable_cost_per_unit
        
        total_grid_co2 += grid_co2
        total_renewable_co2 += renewable_co2
        total_grid_cost += grid_cost
        total_renewable_cost += renewable_cost
        
        results.append({
            'month': month_name,
            'units': units,
            'grid_co2': grid_co2,
            'renewable_co2': renewable_co2,
            'grid_cost': grid_cost,
            'renewable_cost': renewable_cost
        })
    
    return {
        'data': results,
        'total_co2_saving': total_grid_co2 - total_renewable_co2,
        'total_cost_saving': total_grid_cost - total_renewable_cost
    }


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

# Configure static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files from project root."""
    return send_file(os.path.join(os.path.dirname(__file__), filename))


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


@app.route('/live-data-tracking.html')
def live_data_tracking_page():
    """Serve live data tracking page."""
    html_path = os.path.join(os.path.dirname(__file__), 'live-data-tracking.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return "<h1>Live Data Tracking page not found</h1>"


@app.route('/carbon-calculator')
def carbon_calculator_page():
    """Serve the carbon calculator page."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Carbon Calculator - Renewable Energy Tracker</title>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <link rel="stylesheet" href="/static/styles.css" />
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; max-width: 700px; margin: auto; }
        .calculator-container { background: #f1f8e9; border-radius: 12px; padding: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .calculator-container h1 { color: #2e7d32; text-align: center; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 0.5rem; color: #333; }
        .form-group input { padding: 0.8rem; font-size: 16px; width: 100%; box-sizing: border-box; border: 1px solid #cfd8dc; border-radius: 6px; }
        .form-group input:focus { outline: none; border-color: #388e3c; box-shadow: 0 0 6px rgba(56, 142, 60, 0.3); }
        button { padding: 0.8rem 2rem; font-size: 16px; background: #388e3c; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; }
        button:hover { background: #2e7d32; }
        .result-container { margin-top: 2rem; padding: 1.5rem; background: #e8f5e9; border-radius: 8px; border-left: 4px solid #388e3c; display: none; }
        .result-container.show { display: block; }
        .consumption-text { font-size: 18px; font-weight: bold; color: #2e7d32; margin-bottom: 0.5rem; }
        .emission-text { font-size: 18px; font-weight: bold; color: #d32f2f; margin-bottom: 1rem; }
        .suggestion-text { font-size: 15px; line-height: 1.6; color: #555; }
        .error { color: #b00020; text-align: center; margin-top: 1rem; }
        .back-button { display: inline-block; margin-bottom: 1rem; padding: 0.6rem 1.2rem; background: #666; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .back-button:hover { background: #555; }
      </style>
    </head>
    <body>
      <a href="/" class="back-button">← Back to Home</a>
      
      <div class="calculator-container">
        <h1>⚡ Carbon Emission Calculator</h1>
        <p style="text-align: center; color: #666; margin-bottom: 1.5rem;">Calculate your electricity consumption and CO₂ emissions</p>
        
        <form id="calculatorForm">
          <div class="form-group">
            <label for="units">Electricity Consumed (kWh)</label>
            <input type="number" id="units" name="units" min="0" step="0.1" placeholder="Enter units consumed" required />
          </div>
          <button type="submit">Calculate CO₂ Emissions</button>
        </form>
        
        <div id="resultContainer" class="result-container">
          <div class="consumption-text">📊 You consumed <span id="consumedUnits">0</span> kWh of electricity</div>
          <div class="emission-text">💨 Estimated CO₂ emitted: <span id="emissionValue">0</span> kg</div>
          <div class="suggestion-text"><strong>🤖 AI Energy Advisor:</strong><br><span id="suggestion"></span></div>
        </div>
        
        <div id="errorMsg" class="error"></div>
      </div>
      
      <script>
        const form = document.getElementById('calculatorForm');
        const resultContainer = document.getElementById('resultContainer');
        const errorMsg = document.getElementById('errorMsg');
        
        const suggestions = {
          low: "🌿 Excellent! Your consumption is very low. Keep it up by continuing to use efficient LED bulbs and solar charging devices.",
          moderate: "⚙️ Moderate consumption detected. Consider unplugging idle electronics and using smart power strips to reduce standby losses.",
          medium: "⚡ Your electricity usage is on the higher side. Try scheduling high-power tasks during off-peak hours, and switch to inverter-based appliances.",
          high: "🔥 Heavy usage! You might benefit from a partial solar panel setup to offset your grid use. Monitor your cooling/heating appliances — they're often major contributors.",
          veryHigh: "🚨 Very high energy usage detected! Consider a full renewable energy plan or energy audit. Switching to solar or wind power could reduce over 70% of your CO₂ emissions."
        };
        
        function getAISuggestion(units) {
          if (units <= 50) return suggestions.low;
          if (units <= 150) return suggestions.moderate;
          if (units <= 300) return suggestions.medium;
          if (units <= 600) return suggestions.high;
          return suggestions.veryHigh;
        }
        
        form.addEventListener('submit', (e) => {
          e.preventDefault();
          
          const units = parseFloat(document.getElementById('units').value);
          
          if (isNaN(units) || units < 0) {
            errorMsg.textContent = '❌ Please enter a valid number for electricity units';
            resultContainer.classList.remove('show');
            return;
          }
          
          errorMsg.textContent = '';
          
          const emissionFactor = 0.85; // kg CO2 per kWh
          const totalCO2 = (units * emissionFactor).toFixed(2);
          
          document.getElementById('consumedUnits').textContent = units.toFixed(2);
          document.getElementById('emissionValue').textContent = totalCO2;
          document.getElementById('suggestion').textContent = getAISuggestion(units);
          
          resultContainer.classList.add('show');
        });
      </script>
    </body>
    </html>
    """
    return html_content


@app.route('/impact-visualization.html')
def impact_visualization_page():
    """Serve impact visualization page with savings calculator."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Impact Visualization - Renewable Energy Tracker</title>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <link rel="stylesheet" href="/static/styles.css" />
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; max-width: 1000px; margin: auto; background: #f5f5f5; }
        .impact-container { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        h1 { color: #2e7d32; text-align: center; margin-bottom: 1.5rem; }
        .form-section { background: #f1f8e9; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; }
        .month-input { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; padding: 1rem; background: white; border-radius: 6px; border: 1px solid #cfd8dc; }
        .month-input input { padding: 0.6rem; border: 1px solid #cfd8dc; border-radius: 4px; font-size: 14px; }
        .month-input input:focus { outline: none; border-color: #388e3c; }
        .add-btn { padding: 0.6rem 1.2rem; background: #388e3c; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .add-btn:hover { background: #2e7d32; }
        .calc-btn { padding: 1rem 2rem; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; width: 100%; }
        .calc-btn:hover { background: #1565c0; }
        .results-section { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem; }
        .result-card { background: #e8f5e9; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #388e3c; text-align: center; }
        .result-card h3 { color: #2e7d32; margin-bottom: 0.5rem; }
        .result-value { font-size: 28px; font-weight: bold; color: #d32f2f; }
        .chart-container { background: white; padding: 2rem; border-radius: 8px; margin-top: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .back-btn { display: inline-block; margin-bottom: 1rem; padding: 0.6rem 1.2rem; background: #666; color: white; text-decoration: none; border-radius: 6px; }
        .back-btn:hover { background: #555; }
        .months-list { max-height: 300px; overflow-y: auto; background: white; padding: 1rem; border-radius: 6px; margin-top: 1rem; }
        .month-item { display: flex; justify-content: space-between; padding: 0.8rem; border-bottom: 1px solid #eee; }
        .month-item .remove-btn { background: #d32f2f; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 12px; }
      </style>
    </head>
    <body>
      <a href="/" class="back-btn">← Back to Home</a>
      
      <div class="impact-container">
        <h1>🌍 Impact Visualization & Carbon Savings</h1>
        
        <div class="form-section">
          <h3 style="color: #2e7d32; margin-bottom: 1rem;">📊 Track Your Electricity Usage</h3>
          
          <div class="month-input">
            <div>
              <label>Month Name</label>
              <input type="text" id="monthName" placeholder="e.g., January" />
            </div>
            <div>
              <label>Units (kWh)</label>
              <input type="number" id="monthUnits" placeholder="e.g., 150" min="0" step="0.1" />
            </div>
          </div>
          
          <button class="add-btn" onclick="addMonth()">+ Add Month</button>
          
          <div class="months-list" id="monthsList" style="display:none;">
            <h4>Added Months:</h4>
            <div id="monthsContainer"></div>
          </div>
          
          <button class="calc-btn" onclick="calculateImpact()" style="margin-top: 1rem;">🔥 Calculate Impact & Savings</button>
        </div>
        
        <div id="resultsDiv" style="display: none;">
          <div class="results-section">
            <div class="result-card">
              <h3>💨 CO₂ Reduction</h3>
              <div class="result-value" id="co2Saving">0</div>
              <p>kg CO₂ saved per year</p>
            </div>
            <div class="result-card">
              <h3>💰 Cost Savings</h3>
              <div class="result-value" id="costSaving">₹0</div>
              <p>saved per year with renewable energy</p>
            </div>
          </div>
          
          <div class="chart-container">
            <canvas id="impactChart"></canvas>
          </div>
        </div>
      </div>
      
      <script>
        let monthsData = [];
        let chart = null;
        
        function addMonth() {
          const name = document.getElementById('monthName').value.trim();
          const units = parseFloat(document.getElementById('monthUnits').value);
          
          if (!name || isNaN(units) || units < 0) {
            alert('Please enter valid month name and units');
            return;
          }
          
          monthsData.push({ name, units });
          document.getElementById('monthName').value = '';
          document.getElementById('monthUnits').value = '';
          
          displayMonths();
        }
        
        function displayMonths() {
          const list = document.getElementById('monthsList');
          const container = document.getElementById('monthsContainer');
          
          if (monthsData.length === 0) {
            list.style.display = 'none';
            return;
          }
          
          list.style.display = 'block';
          container.innerHTML = monthsData.map((m, i) => `
            <div class="month-item">
              <span>${m.name}: ${m.units} kWh</span>
              <button class="remove-btn" onclick="removeMonth(${i})">Remove</button>
            </div>
          `).join('');
        }
        
        function removeMonth(index) {
          monthsData.splice(index, 1);
          displayMonths();
        }
        
        function calculateImpact() {
          if (monthsData.length === 0) {
            alert('Please add at least one month of data');
            return;
          }
          
          const emissionFactor = 0.85;
          const renewableFactor = 0.05;
          const costPerUnit = 7.0;
          const renewableCostPerUnit = 2.5;
          
          let gridCO2 = 0, renewableCO2 = 0, gridCost = 0, renewableCost = 0;
          const labels = [];
          const gridData = [];
          const renewableData = [];
          
          monthsData.forEach(m => {
            const gco2 = m.units * emissionFactor;
            const rco2 = m.units * renewableFactor;
            
            gridCO2 += gco2;
            renewableCO2 += rco2;
            gridCost += m.units * costPerUnit;
            renewableCost += m.units * renewableCostPerUnit;
            
            labels.push(m.name);
            gridData.push(gco2.toFixed(2));
            renewableData.push(rco2.toFixed(2));
          });
          
          const co2Saving = (gridCO2 - renewableCO2).toFixed(2);
          const costSaving = (gridCost - renewableCost).toFixed(2);
          
          document.getElementById('co2Saving').textContent = co2Saving;
          document.getElementById('costSaving').textContent = '₹' + costSaving;
          document.getElementById('resultsDiv').style.display = 'block';
          
          drawChart(labels, gridData, renewableData);
        }
        
        function drawChart(labels, gridData, renewableData) {
          const ctx = document.getElementById('impactChart').getContext('2d');
          
          if (chart) chart.destroy();
          
          chart = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: labels,
              datasets: [
                {
                  label: 'Grid CO₂ (kg)',
                  data: gridData,
                  backgroundColor: '#d32f2f',
                  borderRadius: 4
                },
                {
                  label: 'Renewable CO₂ (kg)',
                  data: renewableData,
                  backgroundColor: '#388e3c',
                  borderRadius: 4
                }
              ]
            },
            options: {
              responsive: true,
              plugins: {
                title: {
                  display: true,
                  text: 'CO₂ Emissions: Grid vs Renewable Energy'
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: { display: true, text: 'CO₂ (kg)' }
                }
              }
            }
          });
        }
      </script>
    </body>
    </html>
    """
    return html_content


@app.route('/community-comparison.html')
def community_comparison_page():
    """Serve community comparison page."""
    html_path = os.path.join(os.path.dirname(__file__), 'community-comparison.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return "<h1>Community Comparison page not found</h1>"


@app.route('/insights-trends.html')
def insights_trends_page():
    """Serve insights and trends page."""
    html_path = os.path.join(os.path.dirname(__file__), 'insights-trends.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return "<h1>Insights & Trends page not found</h1>"


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
    elif args.command == "predict":
        # Run the predictive model and show plots (this will open a matplotlib window in a GUI environment)
        try:
            predective.auto_renewable_prediction()
        except Exception as e:
            print(f"❌ Error running predictive model: {e}")


if __name__ == "__main__":
	main()

