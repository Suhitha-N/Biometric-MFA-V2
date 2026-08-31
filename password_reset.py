import tkinter as tk
from tkinter import messagebox
import secrets
import time
import database

OTP_LIFETIME = 300
MAX_OTP_ATTEMPTS = 3
otp_code = None
otp_expiry = 0
otp_attempts = 0
otp_user = None


def send_otp():
    global otp_code, otp_expiry, otp_attempts, otp_user
    username = username_entry.get().strip()
    if not username:
        messagebox.showwarning("Error", "Enter username")
        return
    if not database.get_user(username):
        messagebox.showerror("Error", "Username not found")
        return
    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    otp_expiry = time.time() + OTP_LIFETIME
    otp_attempts = 0
    otp_user = username
    database.log_auth(username, "PASSWORD_RESET", "OTP_ISSUED", "Demo OTP generated")
    print(f"DEMO OTP for {username}: {otp_code}")
    messagebox.showinfo("OTP Generated", "Demo OTP is printed in the terminal. It expires in 5 minutes.")


def reset_password():
    global otp_code, otp_expiry, otp_attempts, otp_user
    username = username_entry.get().strip()
    otp = otp_entry.get().strip()
    new_password = newpass_entry.get()

    if not otp_code or username != otp_user:
        messagebox.showerror("Error", "Generate a new OTP for this username first")
        return
    if time.time() > otp_expiry:
        otp_code = None
        messagebox.showerror("Error", "OTP expired. Request a new OTP.")
        return
    if otp != otp_code:
        otp_attempts += 1
        if otp_attempts >= MAX_OTP_ATTEMPTS:
            database.log_auth(username, "PASSWORD_RESET", "FAILED", "Too many wrong OTP attempts")
            otp_code = None
            messagebox.showerror("Error", "Too many wrong OTP attempts. Request a new OTP.")
        else:
            messagebox.showerror("Error", f"Invalid OTP. Attempts left: {MAX_OTP_ATTEMPTS - otp_attempts}")
        return

    ok, msg = database.password_policy(new_password)
    if not ok:
        messagebox.showerror("Weak Password", msg)
        return
    if database.reset_password(username, new_password):
        database.log_auth(username, "PASSWORD_RESET", "SUCCESS", "Password reset using OTP")
        otp_code = None
        messagebox.showinfo("Success", "Password updated successfully")
        root.destroy()
    else:
        messagebox.showerror("Error", "Password reset failed")


root = tk.Tk()
root.title("Secure Password Reset")
root.geometry("460x410")
root.resizable(False, False)
tk.Label(root, text="PASSWORD RESET", font=("Arial", 18, "bold")).pack(pady=22)
tk.Label(root, text="Username").pack()
username_entry = tk.Entry(root, width=34)
username_entry.pack(pady=5)
tk.Button(root, text="Generate Demo OTP", command=send_otp, width=24).pack(pady=10)
tk.Label(root, text="OTP").pack()
otp_entry = tk.Entry(root, width=34)
otp_entry.pack(pady=5)
tk.Label(root, text="New Password").pack()
newpass_entry = tk.Entry(root, show="*", width=34)
newpass_entry.pack(pady=5)
tk.Label(root, text="8+ chars, uppercase, lowercase, number, special character", font=("Arial", 8)).pack(pady=6)
tk.Button(root, text="RESET PASSWORD", command=reset_password, width=24).pack(pady=18)
root.mainloop()
