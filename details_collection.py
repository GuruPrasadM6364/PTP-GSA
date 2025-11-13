import re

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
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
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
    print(f"Email:    {user_data['email']}")
    print(f"Pincode:  {user_data['pincode']}")
    print(f"Address:  {user_data['address']}")
    print(f"Password: {'*' * len(user_data['password'])}")
    print("=" * 50)

if __name__ == "__main__":
    user_info = get_user_info()
    display_user_info(user_info)
    
    # You can save to file, database, or process further
    print("\n✅ Information collected successfully!")