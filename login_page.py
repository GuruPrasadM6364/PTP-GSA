import re
import hashlib
import json
import os

class LoginSystem:
    def __init__(self, data_file='users.json'):
        self.data_file = data_file
        self.users = self.load_users()
    
    def load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_users(self):
        """Save users to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.users, f, indent=4)
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_phone(self, phone):
        """Validate 10-digit phone number"""
        pattern = r'^[6-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    def register(self, email, phone, password):
        """Register a new user"""
        if not self.validate_email(email):
            return False, "Invalid email format"
        
        if not self.validate_phone(phone):
            return False, "Invalid phone number (must be 10 digits starting with 6-9)"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Check if email or phone already exists
        for user_id, user_data in self.users.items():
            if user_data['email'] == email:
                return False, "Email already registered"
            if user_data['phone'] == phone:
                return False, "Phone number already registered"
        
        # Create new user
        user_id = f"user_{len(self.users) + 1}"
        self.users[user_id] = {
            'email': email,
            'phone': phone,
            'password': self.hash_password(password)
        }
        self.save_users()
        return True, "Registration successful!"
    
    def login(self, identifier, password):
        """Login using email or phone number with password"""
        hashed_password = self.hash_password(password)
        
        # Check if identifier is email or phone
        is_email = '@' in identifier
        
        # Search for user
        for user_id, user_data in self.users.items():
            if is_email:
                if user_data['email'] == identifier and user_data['password'] == hashed_password:
                    return True, f"Login successful! Welcome {user_data['email']}"
            else:
                if user_data['phone'] == identifier and user_data['password'] == hashed_password:
                    return True, f"Login successful! Welcome (Phone: {user_data['phone']})"
        
        return False, "Invalid credentials. Please check your email/phone and password."

def main():
    system = LoginSystem()
    
    while True:
        print("\n" + "=" * 50)
        print("LOGIN SYSTEM")
        print("=" * 50)
        print("1. Register")
        print("2. Login with Email")
        print("3. Login with Phone Number")
        print("4. Exit")
        print("=" * 50)
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            print("\n--- REGISTRATION ---")
            email = input("Enter Email: ").strip()
            phone = input("Enter Phone Number: ").strip()
            password = input("Enter Password (min 6 characters): ").strip()
            confirm_password = input("Confirm Password: ").strip()
            
            if password != confirm_password:
                print("❌ Passwords do not match!")
                continue
            
            success, message = system.register(email, phone, password)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
        
        elif choice == '2':
            print("\n--- LOGIN WITH EMAIL ---")
            email = input("Enter Email: ").strip()
            password = input("Enter Password: ").strip()
            
            success, message = system.login(email, password)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
        
        elif choice == '3':
            print("\n--- LOGIN WITH PHONE NUMBER ---")
            phone = input("Enter Phone Number: ").strip()
            password = input("Enter Password: ").strip()
            
            success, message = system.login(phone, password)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
        
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()