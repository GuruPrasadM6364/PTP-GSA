import tkinter as tk
from tkinter import messagebox

def submit_form():
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()
    pincode = pin_entry.get().strip()
    email = email_entry.get().strip()
    source = source_var.get()
    
    if not name or not phone or not pincode or not email or not source:
        messagebox.showwarning("Incomplete Form", "Please fill all the fields.")
        return
    
    # Basic validation examples
    if not phone.isdigit() or len(phone) != 10:
        messagebox.showerror("Invalid Input", "Phone number must be 10 digits.")
        return
    if not pincode.isdigit() or len(pincode) != 6:
        messagebox.showerror("Invalid Input", "PIN code must be 6 digits.")
        return
    if "@" not in email or "." not in email:
        messagebox.showerror("Invalid Email", "Please enter a valid email address.")
        return
    
    # Display the collected information
    info = f"""
    ✅ Application Submitted Successfully!

    Name: {name}
    Phone: {phone}
    PIN Code: {pincode}
    Email: {email}
    Preferred Renewable Source: {source}
    """
    messagebox.showinfo("Submission Successful", info)

# GUI window setup
root = tk.Tk()
root.title("Renewable Energy Application Form")
root.geometry("400x400")
root.resizable(False, False)

# Labels and Entry Fields
tk.Label(root, text="Renewable Energy Application Form", font=("Arial", 14, "bold")).pack(pady=10)

tk.Label(root, text="Full Name:").pack(anchor="w", padx=20)
name_entry = tk.Entry(root, width=40)
name_entry.pack(padx=20, pady=5)

tk.Label(root, text="Phone Number:").pack(anchor="w", padx=20)
phone_entry = tk.Entry(root, width=40)
phone_entry.pack(padx=20, pady=5)

tk.Label(root, text="PIN Code:").pack(anchor="w", padx=20)
pin_entry = tk.Entry(root, width=40)
pin_entry.pack(padx=20, pady=5)

tk.Label(root, text="Email Address:").pack(anchor="w", padx=20)
email_entry = tk.Entry(root, width=40)
email_entry.pack(padx=20, pady=5)

tk.Label(root, text="Type of Renewable Source:").pack(anchor="w", padx=20)
source_var = tk.StringVar()
tk.Radiobutton(root, text="Solar", variable=source_var, value="Solar").pack(anchor="w", padx=40)
tk.Radiobutton(root, text="Turbine", variable=source_var, value="Turbine").pack(anchor="w", padx=40)

tk.Button(root, text="Submit", command=submit_form, bg="#4CAF50", fg="white", width=15).pack(pady=20)

root.mainloop()
