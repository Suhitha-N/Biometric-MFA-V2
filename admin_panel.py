import tkinter as tk
from tkinter import messagebox, ttk
import database
import subprocess
import sys


def refresh_users():
    for item in user_tree.get_children():
        user_tree.delete(item)

    users = database.get_users()

    for u in users:
        user_tree.insert("", "end", values=(u[0], "Registered"))


def get_selected_user():
    selected = user_tree.selection()
    if not selected:
        return None

    values = user_tree.item(selected[0], "values")
    return values[0] if values else None


def add_user():
    username = username_entry.get().strip()
    password = password_entry.get()

    if username == "" or password == "":
        messagebox.showwarning(
            "Missing Details",
            "Enter both username and password."
        )
        return

    if database.register_user(username, password):
        messagebox.showinfo("User Created", "User created successfully.")

        subprocess.run([sys.executable, "register_face.py"])
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        refresh_users()

    else:
        messagebox.showerror(
            "User Exists",
            "That username already exists."
        )


def delete_user():
    selected = get_selected_user()

    if not selected:
        messagebox.showwarning(
            "Select User",
            "Please select a user first."
        )
        return

    if not messagebox.askyesno(
        "Delete User",
        f"Delete user '{selected}'?"
    ):
        return

    database.delete_user(selected)
    refresh_users()


# -------------------- WINDOW --------------------
root = tk.Tk()
root.title("Biometric MFA - Admin Panel")
root.geometry("700x620")
root.minsize(650, 560)
root.configure(bg="#eef3f8")

style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure(
    "Admin.TButton",
    font=("Segoe UI", 10, "bold"),
    padding=(14, 9)
)

# -------------------- HEADER --------------------
header = tk.Frame(root, bg="#14283d", height=120)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="⚙  ADMIN CONTROL PANEL",
    font=("Segoe UI", 21, "bold"),
    bg="#14283d",
    fg="white"
).pack(pady=(25, 4))

tk.Label(
    header,
    text="Manage registered users and biometric enrollment",
    font=("Segoe UI", 10),
    bg="#14283d",
    fg="#c9d7e5"
).pack()

# -------------------- MAIN --------------------
card = tk.Frame(
    root,
    bg="white",
    highlightbackground="#d6dee8",
    highlightthickness=1
)
card.pack(fill="both", expand=True, padx=35, pady=25)

tk.Label(
    card,
    text="Create New User",
    font=("Segoe UI", 16, "bold"),
    bg="white",
    fg="#14283d"
).pack(anchor="w", padx=30, pady=(25, 15))

form = tk.Frame(card, bg="white")
form.pack(fill="x", padx=30)

tk.Label(
    form,
    text="USERNAME",
    font=("Segoe UI", 9, "bold"),
    bg="white",
    fg="#445466"
).grid(row=0, column=0, sticky="w", padx=(0, 15))

username_entry = ttk.Entry(form, font=("Segoe UI", 10))
username_entry.grid(row=1, column=0, sticky="ew", padx=(0, 15), ipady=6)

tk.Label(
    form,
    text="PASSWORD",
    font=("Segoe UI", 9, "bold"),
    bg="white",
    fg="#445466"
).grid(row=0, column=1, sticky="w", padx=15)

password_entry = ttk.Entry(form, show="•", font=("Segoe UI", 10))
password_entry.grid(row=1, column=1, sticky="ew", padx=15, ipady=6)

form.columnconfigure(0, weight=1)
form.columnconfigure(1, weight=1)

ttk.Button(
    card,
    text="＋  Add User & Register Face",
    command=add_user,
    style="Admin.TButton"
).pack(anchor="w", padx=30, pady=18)

# -------------------- USER TABLE --------------------
tk.Label(
    card,
    text="Registered Users",
    font=("Segoe UI", 15, "bold"),
    bg="white",
    fg="#14283d"
).pack(anchor="w", padx=30, pady=(10, 10))

table_frame = tk.Frame(card, bg="white")
table_frame.pack(fill="both", expand=True, padx=30)

style.configure(
    "Admin.Treeview",
    font=("Segoe UI", 10),
    rowheight=32
)
style.configure(
    "Admin.Treeview.Heading",
    font=("Segoe UI", 9, "bold"),
    padding=8
)

user_tree = ttk.Treeview(
    table_frame,
    columns=("username", "status"),
    show="headings",
    style="Admin.Treeview",
    selectmode="browse"
)

user_tree.heading("username", text="USERNAME")
user_tree.heading("status", text="STATUS")

user_tree.column("username", width=300, anchor="w")
user_tree.column("status", width=180, anchor="center")

scroll = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=user_tree.yview
)
user_tree.configure(yscrollcommand=scroll.set)

user_tree.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

actions = tk.Frame(card, bg="white")
actions.pack(fill="x", padx=30, pady=18)

ttk.Button(
    actions,
    text="Delete Selected User",
    command=delete_user,
    style="Admin.TButton"
).pack(side="left")

ttk.Button(
    actions,
    text="Refresh",
    command=refresh_users,
    style="Admin.TButton"
).pack(side="left", padx=10)

ttk.Button(
    actions,
    text="Close",
    command=root.destroy,
    style="Admin.TButton"
).pack(side="right")

refresh_users()
username_entry.focus_set()
root.mainloop()
