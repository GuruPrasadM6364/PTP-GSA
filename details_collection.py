import re
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import User

DB_URL = "sqlite:///renewable.db"

def validate_phone(phone):
    """Validate 10-digit phone number"""
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_pincode(pincode):
    """Validate 6-digit pincode"""
    pattern = r'^\d{6}$'
    return bool(re.match(pattern, pincode))

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
        'pincode': pincode,
        'address': address
    }
    
    return user_data

def display_user_info(user_data):
    """Display collected user information"""
    print("\n" + "=" * 50)
    print("COLLECTED INFORMATION")
    print("=" * 50)
    print(f"Name:     {user_data['name']}")
    print(f"Phone:    {user_data['phone']}")
    print(f"Pincode:  {user_data['pincode']}")
    print(f"Address:  {user_data['address']}")
    print("=" * 50)

if __name__ == "__main__":
    user_info = get_user_info()
    display_user_info(user_info)
    
    # Save to database
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