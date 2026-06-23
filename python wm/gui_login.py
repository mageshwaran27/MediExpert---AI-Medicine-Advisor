import cx_Oracle
import tkinter as tk
from tkinter import messagebox
from user_service import register_user, login_user
from gui_report import open_report_window  # Make sure gui_report.py exists

def login():
    email = entry_email.get()
    password = entry_pass.get()
    if not email or not password:
        messagebox.showwarning("Login", "Please enter email and password")
        return
    user_id = login_user(email, password)
    if user_id:
        messagebox.showinfo("Login", "Login successful!")
        root.destroy()
        open_report_window(user_id)
    else:
        messagebox.showerror("Login", "Invalid email or password")

def register():
    name = entry_name.get()
    email = entry_email.get()
    password = entry_pass.get()
    if not name or not email or not password:
        messagebox.showwarning("Register", "Please fill all fields")
        return
    success = register_user(name, email, password)
    if success:
        messagebox.showinfo("Register", "Registration successful!")
    else:
        messagebox.showerror("Register", "Email already exists or error during registration")

root = tk.Tk()
root.title("WM App Login")
root.geometry("300x350")

tk.Label(root, text="Name:").pack(pady=5)
entry_name = tk.Entry(root)
entry_name.pack(pady=5)

tk.Label(root, text="Email:").pack(pady=5)
entry_email = tk.Entry(root)
entry_email.pack(pady=5)

tk.Label(root, text="Password:").pack(pady=5)
entry_pass = tk.Entry(root, show="*")
entry_pass.pack(pady=5)

tk.Button(root, text="Login", width=10, command=login).pack(pady=10)
tk.Button(root, text="Register", width=10, command=register).pack(pady=5)

root.mainloop()
