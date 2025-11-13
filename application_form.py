def collect_application_data():
    print("=== Renewable Energy Application Form ===\n")

    # Collect user inputs
    name = input("Enter your full name: ").strip()
    phone = input("Enter your phone number (10 digits): ").strip()
    pin = input("Enter your PIN code (6 digits): ").strip()
    email = input("Enter your email address: ").strip()

    print("\nSelect the type of renewable source:")
    print("1. Solar")
    print("2. Turbine")
    choice = input("Enter your choice (1 or 2): ").strip()

    # Determine source type
    if choice == "1":
        source = "Solar"
    elif choice == "2":
        source = "Turbine"
    else:
        print("⚠️ Invalid choice. Defaulting to 'Solar'.")
        source = "Solar"

    # Validation
    if not name:
        print("Error: Name cannot be empty.")
        return
    if not phone.isdigit() or len(phone) != 10:
        print("Error: Invalid phone number.")
        return
    if not pin.isdigit() or len(pin) != 6:
        print("Error: Invalid PIN code.")
        return
    if "@" not in email or "." not in email:
        print("Error: Invalid email address.")
        return

    # Display collected info
    print("\n✅ Application Submitted Successfully!")
    print("---------------------------------------")
    print(f"Name: {name}")
    print(f"Phone Number: {phone}")
    print(f"PIN Code: {pin}")
    print(f"Email: {email}")
    print(f"Preferred Renewable Source: {source}")
    print("---------------------------------------")


# Run the function
if __name__ == "__main__":
    collect_application_data()
