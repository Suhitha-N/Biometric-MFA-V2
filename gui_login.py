import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import sys
import database
import dashboard
from datetime import datetime
import os


# ============================================================
# LOGGING
# ============================================================

os.makedirs("logs", exist_ok=True)


def log_event(text):
    with open("logs/auth_logs.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {text}\n")


# ============================================================
# COLORS
# ============================================================

BG = "#F4F7FB"
CARD = "#FFFFFF"
PRIMARY = "#2563EB"
PRIMARY_DARK = "#1D4ED8"
TEXT = "#172033"
SECONDARY = "#64748B"
SUCCESS = "#15803D"
ERROR = "#DC2626"
BORDER = "#D9E1EC"
LIGHT_BLUE = "#EFF6FF"


# ============================================================
# STATUS
# ============================================================

def set_status(text, color=SECONDARY):
    status_label.config(
        text=text,
        fg=color
    )
    root.update_idletasks()


# ============================================================
# LOGIN
# ============================================================

def start_login():

    username = username_entry.get().strip()
    password = password_entry.get()

    if not username or not password:
        messagebox.showerror(
            "Login Required",
            "Please enter username and password."
        )
        return

    login_button.config(
        state="disabled",
        text="AUTHENTICATING..."
    )

    try:

        # ====================================================
        # STEP 1 - PASSWORD
        # ====================================================

        set_status(
            "Checking password...",
            SECONDARY
        )

        valid, role, message = database.verify_user(
            username,
            password
        )

        if not valid:

            log_event(
                f"{username} - {message}"
            )

            set_status(
                "✕ Password verification failed",
                ERROR
            )

            messagebox.showerror(
                "Login Failed",
                message
            )

            return

        log_event(
            f"{username} - {message}"
        )

        set_status(
            "✓ Password verified",
            SUCCESS
        )

        # ====================================================
        # ADMIN LOGIN
        # ====================================================

        if role == "admin":

            log_event(
                f"{username} - Admin Login"
            )

            set_status(
                "✓ Admin authentication successful",
                SUCCESS
            )

            messagebox.showinfo(
                "Admin Login",
                "Administrator authentication successful."
            )

            root.destroy()

            subprocess.Popen(
                [
                    sys.executable,
                    "admin_panel.py",
                    username
                ]
            )

            return

        # ====================================================
        # STEP 2 - FACE
        # ====================================================

        set_status(
            "Starting face recognition...",
            SECONDARY
        )

        root.update()

        process = subprocess.run(
            [
                sys.executable,
                "face_auth.py",
                username
            ]
        )

        if process.returncode != 0:

            log_event(
                f"{username} - Face Verification Failed"
            )

            set_status(
                "✕ Face verification failed",
                ERROR
            )

            messagebox.showerror(
                "Authentication Failed",
                "Face verification failed."
            )

            return

        log_event(
            f"{username} - Face Verified"
        )

        set_status(
            "✓ Face verification successful",
            SUCCESS
        )

        # ====================================================
        # STEP 3 - GESTURE
        # ====================================================

        set_status(
            "Starting secret gesture verification...",
            SECONDARY
        )

        root.update()

        process = subprocess.run(
            [
                sys.executable,
                "app.py",
                username
            ]
        )

        if process.returncode != 0:

            log_event(
                f"{username} - Gesture Verification Failed"
            )

            set_status(
                "✕ Gesture verification failed",
                ERROR
            )

            messagebox.showerror(
                "Authentication Failed",
                "Secret gesture verification failed."
            )

            return

        # ====================================================
        # FINAL SUCCESS
        # ====================================================

        log_event(
            f"{username} - MFA Login Successful"
        )

        set_status(
            "✓ Multifactor authentication successful",
            SUCCESS
        )

        messagebox.showinfo(
            "Access Granted",
            "Multifactor Authentication Successful!"
        )

        root.destroy()

        dashboard.open_dashboard(username)

    except Exception as e:

        log_event(
            f"{username} - System Error - {str(e)}"
        )

        messagebox.showerror(
            "System Error",
            f"An unexpected error occurred:\n\n{e}"
        )

    finally:

        try:
            login_button.config(
                state="normal",
                text="🔐  LOGIN"
            )
        except:
            pass


# ============================================================
# FORGOT PASSWORD
# ============================================================

def forgot_password():

    username = simpledialog.askstring(
        "Forgot Password",
        "Enter your username:"
    )

    if not username:
        return

    username = username.strip()

    if not username:
        return

    set_status(
        "Starting identity verification...",
        SECONDARY
    )

    messagebox.showinfo(
        "Identity Verification",
        "Face verification is required to reset your password."
    )

    process = subprocess.run(
        [
            sys.executable,
            "face_auth.py",
            username
        ]
    )

    if process.returncode != 0:

        log_event(
            f"{username} - Password Reset Face Verification Failed"
        )

        set_status(
            "✕ Identity verification failed",
            ERROR
        )

        messagebox.showerror(
            "Reset Failed",
            "Face verification failed."
        )

        return

    new_password = simpledialog.askstring(
        "Reset Password",
        "Enter your new password:",
        show="*"
    )

    if not new_password:
        return

    if len(new_password) < 6:

        messagebox.showerror(
            "Weak Password",
            "Password must contain at least 6 characters."
        )

        return

    try:

        success = database.reset_password(
            username,
            new_password
        )

        if success:

            log_event(
                f"{username} - Password Reset Successful"
            )

            set_status(
                "✓ Password reset successful",
                SUCCESS
            )

            messagebox.showinfo(
                "Success",
                "Password reset successful."
            )

        else:

            messagebox.showerror(
                "Error",
                "User not found."
            )

    except Exception as e:

        messagebox.showerror(
            "Error",
            f"Password reset failed:\n\n{e}"
        )


# ============================================================
# EXIT
# ============================================================

def exit_app():
    root.destroy()


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "Biometric Multifactor Authentication"
)

# Open maximized
try:
    root.state("zoomed")
except:
    root.attributes("-zoomed", True)

root.configure(
    bg=BG
)


# ============================================================
# MAIN CONTAINER
# ============================================================

main = tk.Frame(
    root,
    bg=BG
)

main.pack(
    fill="both",
    expand=True
)


# ============================================================
# TOP BLUE HEADER
# ============================================================

header = tk.Frame(
    main,
    bg=PRIMARY,
    height=210
)

header.pack(
    fill="x"
)

header.pack_propagate(False)


# Lock icon
tk.Label(
    header,
    text="🔐",
    font=("Segoe UI Emoji", 42),
    bg=PRIMARY,
    fg="white"
).pack(
    pady=(28, 0)
)


tk.Label(
    header,
    text="BIOMETRIC MFA",
    font=("Segoe UI", 32, "bold"),
    bg=PRIMARY,
    fg="white"
).pack(
    pady=(0, 4)
)


tk.Label(
    header,
    text="Secure Multifactor Authentication System",
    font=("Segoe UI", 13),
    bg=PRIMARY,
    fg="#E0EAFF"
).pack()


# ============================================================
# CENTER AREA
# ============================================================

center = tk.Frame(
    main,
    bg=BG
)

center.pack(
    fill="both",
    expand=True
)


# ============================================================
# LOGIN CARD
# ============================================================

card = tk.Frame(
    center,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

card.place(
    relx=0.5,
    rely=0.48,
    anchor="center",
    relwidth=0.42,
    relheight=0.82
)


# ============================================================
# CARD TITLE
# ============================================================

tk.Label(
    card,
    text="Welcome Back",
    font=("Segoe UI", 24, "bold"),
    bg=CARD,
    fg=TEXT
).pack(
    pady=(28, 4)
)


tk.Label(
    card,
    text="Sign in to access your secure biometric vault",
    font=("Segoe UI", 11),
    bg=CARD,
    fg=SECONDARY
).pack(
    pady=(0, 24)
)


# ============================================================
# USERNAME
# ============================================================

tk.Label(
    card,
    text="USERNAME",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=TEXT
).pack(
    anchor="w",
    padx=55
)


username_entry = tk.Entry(
    card,
    font=("Segoe UI", 12),
    bg="#F8FAFC",
    fg=TEXT,
    relief="flat",
    highlightbackground=BORDER,
    highlightcolor=PRIMARY,
    highlightthickness=1
)

username_entry.pack(
    fill="x",
    padx=55,
    ipady=9,
    pady=(6, 18)
)


# ============================================================
# PASSWORD
# ============================================================

tk.Label(
    card,
    text="PASSWORD",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=TEXT
).pack(
    anchor="w",
    padx=55
)


password_entry = tk.Entry(
    card,
    font=("Segoe UI", 12),
    bg="#F8FAFC",
    fg=TEXT,
    relief="flat",
    show="•",
    highlightbackground=BORDER,
    highlightcolor=PRIMARY,
    highlightthickness=1
)

password_entry.pack(
    fill="x",
    padx=55,
    ipady=9,
    pady=(6, 20)
)


# ============================================================
# LOGIN BUTTON
# ============================================================

login_button = tk.Button(
    card,
    text="🔐  LOGIN",
    command=start_login,
    font=("Segoe UI", 12, "bold"),
    bg=PRIMARY,
    fg="white",
    activebackground=PRIMARY_DARK,
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    bd=0
)

login_button.pack(
    fill="x",
    padx=55,
    ipady=10,
    pady=(0, 12)
)


# Hover effect
def login_enter(event):
    if login_button["state"] != "disabled":
        login_button.config(
            bg=PRIMARY_DARK
        )


def login_leave(event):
    if login_button["state"] != "disabled":
        login_button.config(
            bg=PRIMARY
        )


login_button.bind(
    "<Enter>",
    login_enter
)

login_button.bind(
    "<Leave>",
    login_leave
)


# ============================================================
# FORGOT PASSWORD
# ============================================================

forgot_button = tk.Button(
    card,
    text="Forgot Password?",
    command=forgot_password,
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=PRIMARY,
    activeforeground=PRIMARY_DARK,
    relief="flat",
    bd=0,
    cursor="hand2"
)

forgot_button.pack(
    pady=(0, 20)
)


# ============================================================
# STATUS BOX
# ============================================================

status_frame = tk.Frame(
    card,
    bg=LIGHT_BLUE,
    highlightbackground="#BFDBFE",
    highlightthickness=1
)

status_frame.pack(
    fill="x",
    padx=55,
    pady=(0, 18)
)


tk.Label(
    status_frame,
    text="AUTHENTICATION STATUS",
    font=("Segoe UI", 9, "bold"),
    bg=LIGHT_BLUE,
    fg=SECONDARY
).pack(
    pady=(10, 2)
)


status_label = tk.Label(
    status_frame,
    text="Ready for authentication",
    font=("Segoe UI", 10, "bold"),
    bg=LIGHT_BLUE,
    fg=SECONDARY
)

status_label.pack(
    pady=(0, 10)
)


# ============================================================
# MFA SECURITY INFORMATION
# ============================================================

tk.Label(
    card,
    text="MULTIFACTOR SECURITY",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=TEXT
).pack(
    pady=(0, 8)
)


mfa_frame = tk.Frame(
    card,
    bg=CARD
)

mfa_frame.pack()


security_items = [
    ("✓", "Password Authentication"),
    ("✓", "Face Recognition"),
    ("✓", "Liveness Detection"),
    ("✓", "Secret Hand Gesture")
]


for symbol, text in security_items:

    row = tk.Frame(
        mfa_frame,
        bg=CARD
    )

    row.pack(
        anchor="w",
        pady=2
    )

    tk.Label(
        row,
        text=symbol,
        font=("Segoe UI", 10, "bold"),
        bg=CARD,
        fg=SUCCESS
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Label(
        row,
        text=text,
        font=("Segoe UI", 10),
        bg=CARD,
        fg=SECONDARY
    ).pack(
        side="left"
    )


# ============================================================
# FOOTER
# ============================================================

footer = tk.Frame(
    main,
    bg=BG
)

footer.pack(
    fill="x",
    pady=(0, 12)
)


tk.Label(
    footer,
    text="Protected by Multi-Factor Biometric Authentication",
    font=("Segoe UI", 9),
    bg=BG,
    fg=SECONDARY
).pack()


# ============================================================
# KEYBOARD SHORTCUTS
# ============================================================

root.bind(
    "<Return>",
    lambda event: start_login()
)

root.bind(
    "<Escape>",
    lambda event: exit_app()
)


# ============================================================
# START
# ============================================================

username_entry.focus()

root.mainloop()