import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import platform
import subprocess
import tempfile
from cryptography.fernet import Fernet, InvalidToken
import database


def open_dashboard(username):

    root = tk.Tk()

    root.title("Secure Biometric Vault")

    # =========================================================
    # MAXIMIZED WINDOW
    # =========================================================

    try:
        root.state("zoomed")
    except:
        try:
            root.attributes("-zoomed", True)
        except:
            pass

    root.resizable(True, True)
    root.minsize(850, 600)
    root.configure(bg="#eef3f8")

    # =========================================================
    # USER SECURE DIRECTORY
    # =========================================================

    user_path = os.path.join("secure_files", username)
    os.makedirs(user_path, exist_ok=True)

    key_path = os.path.join(user_path, "key.key")

    # =========================================================
    # SECURITY / ENCRYPTION
    # =========================================================

    if not os.path.exists(key_path):

        with open(key_path, "wb") as f:
            f.write(Fernet.generate_key())

    try:

        with open(key_path, "rb") as f:
            cipher = Fernet(f.read())

    except Exception:

        messagebox.showerror(
            "Vault Error",
            "Vault encryption key is invalid."
        )

        root.destroy()
        return

    # Keep track of temporary decrypted files
    temp_files = []

    # =========================================================
    # TEMP FILE CLEANUP
    # =========================================================

    def safe_remove(path):

        try:

            if os.path.exists(path):
                os.remove(path)

            if path in temp_files:
                temp_files.remove(path)

        except OSError:
            pass

    # =========================================================
    # REFRESH FILE LIST
    # =========================================================

    def refresh():

        for item in file_tree.get_children():
            file_tree.delete(item)

        files = []

        try:

            for name in os.listdir(user_path):

                if name == "key.key":
                    continue

                path = os.path.join(user_path, name)

                if (
                    os.path.isfile(path)
                    and name.endswith(".enc")
                ):

                    files.append(
                        (name, os.path.getsize(path))
                    )

        except OSError:
            files = []

        for name, size in sorted(files):

            file_tree.insert(
                "",
                "end",
                values=(
                    name,
                    f"{size:,} bytes",
                    "🔒 Encrypted"
                )
            )

        count_var.set(
            f"{len(files)} encrypted file(s)"
        )

    # =========================================================
    # GET SELECTED FILE
    # =========================================================

    def selected_name():

        selection = file_tree.selection()

        if not selection:

            messagebox.showwarning(
                "Select File",
                "Please select an encrypted file first."
            )

            return None

        values = file_tree.item(
            selection[0],
            "values"
        )

        if not values:
            return None

        return values[0]

    # =========================================================
    # UPLOAD / ENCRYPT
    # =========================================================

    def upload():

        source = filedialog.askopenfilename(
            title="Select file to encrypt"
        )

        if not source:
            return

        try:

            name = os.path.basename(source)

            target = os.path.join(
                user_path,
                name + ".enc"
            )

            if os.path.exists(target):

                overwrite = messagebox.askyesno(
                    "Overwrite File",
                    f"{name} already exists.\n\n"
                    "Do you want to overwrite it?"
                )

                if not overwrite:
                    return

            with open(source, "rb") as f:
                encrypted = cipher.encrypt(f.read())

            with open(target, "wb") as f:
                f.write(encrypted)

            database.log_auth(
                username,
                "VAULT",
                "SUCCESS",
                f"Uploaded {name}"
            )

            refresh()

            messagebox.showinfo(
                "File Secured",
                f"{name}\n\n"
                "The file was encrypted and stored securely."
            )

        except OSError as exc:

            database.log_auth(
                username,
                "VAULT",
                "FAILED",
                f"Upload error: {exc}"
            )

            messagebox.showerror(
                "Upload Error",
                str(exc)
            )

    # =========================================================
    # OPEN / DECRYPT
    # =========================================================

    def open_file():

        name = selected_name()

        if not name:
            return

        path = os.path.join(
            user_path,
            name
        )

        try:

            with open(path, "rb") as f:
                encrypted_data = f.read()

            decrypted = cipher.decrypt(
                encrypted_data
            )

            original = (
                name[:-4]
                if name.endswith(".enc")
                else name
            )

            extension = os.path.splitext(
                original
            )[1]

            fd, temp_path = tempfile.mkstemp(
                prefix="mfa_",
                suffix=extension
            )

            os.close(fd)

            with open(temp_path, "wb") as f:
                f.write(decrypted)

            temp_files.append(temp_path)

            # Open decrypted file
            if platform.system() == "Windows":

                os.startfile(temp_path)

            elif platform.system() == "Darwin":

                subprocess.Popen(
                    ["open", temp_path]
                )

            else:

                subprocess.Popen(
                    ["xdg-open", temp_path]
                )

            database.log_auth(
                username,
                "VAULT",
                "SUCCESS",
                f"Opened {original}"
            )

            # Remove plaintext temporary copy
            # after 10 minutes
            root.after(
                10 * 60 * 1000,
                lambda p=temp_path: safe_remove(p)
            )

        except (
            InvalidToken,
            OSError
        ) as exc:

            database.log_auth(
                username,
                "VAULT",
                "FAILED",
                f"Open error: {exc}"
            )

            messagebox.showerror(
                "Open Error",
                "Unable to decrypt/open this file."
            )

    # =========================================================
    # DELETE
    # =========================================================

    def delete():

        name = selected_name()

        if not name:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{name}' permanently?"
        )

        if not confirm:
            return

        try:

            os.remove(
                os.path.join(
                    user_path,
                    name
                )
            )

            database.log_auth(
                username,
                "VAULT",
                "SUCCESS",
                f"Deleted {name}"
            )

            refresh()

        except OSError as exc:

            database.log_auth(
                username,
                "VAULT",
                "FAILED",
                f"Delete error: {exc}"
            )

            messagebox.showerror(
                "Delete Error",
                str(exc)
            )

    # =========================================================
    # CLOSE VAULT
    # =========================================================

    def close():

        # Remove any temporary decrypted files
        for path in list(temp_files):
            safe_remove(path)

        root.destroy()

    # =========================================================
    # HEADER
    # =========================================================

    header = tk.Frame(
        root,
        bg="#14283d",
        height=135
    )

    header.pack(
        fill="x"
    )

    header.pack_propagate(False)

    # Title row
    title_row = tk.Frame(
        header,
        bg="#14283d"
    )

    title_row.pack(
        pady=(22, 2)
    )

    tk.Label(
        title_row,
        text="🔐",
        font=("Segoe UI Emoji", 28),
        bg="#14283d",
        fg="white"
    ).pack(
        side="left",
        padx=(0, 10)
    )

    tk.Label(
        title_row,
        text="SECURE BIOMETRIC VAULT",
        font=("Segoe UI", 22, "bold"),
        bg="#14283d",
        fg="white"
    ).pack(
        side="left"
    )

    tk.Label(
        header,
        text=f"Authenticated user: {username}",
        font=("Segoe UI", 10),
        bg="#14283d",
        fg="#c9d7e5"
    ).pack()

    tk.Label(
        header,
        text="●  MFA STATUS: VERIFIED",
        font=("Segoe UI", 10, "bold"),
        bg="#14283d",
        fg="#65d391"
    ).pack(
        pady=(4, 8)
    )

    # =========================================================
    # MAIN CARD
    # =========================================================

    card = tk.Frame(
        root,
        bg="white",
        highlightbackground="#d6dee8",
        highlightthickness=1
    )

    card.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=30
    )

    # =========================================================
    # TOP SECTION
    # =========================================================

    top = tk.Frame(
        card,
        bg="white"
    )

    top.pack(
        fill="x",
        padx=25,
        pady=(22, 10)
    )

    tk.Label(
        top,
        text="Encrypted Files",
        font=("Segoe UI", 17, "bold"),
        bg="white",
        fg="#14283d"
    ).pack(
        side="left"
    )

    count_var = tk.StringVar(
        value="0 encrypted file(s)"
    )

    tk.Label(
        top,
        textvariable=count_var,
        font=("Segoe UI", 9),
        bg="white",
        fg="#718096"
    ).pack(
        side="right"
    )

    # =========================================================
    # TABLE
    # =========================================================

    table_frame = tk.Frame(
        card,
        bg="white"
    )

    table_frame.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=8
    )

    style = ttk.Style()

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "Vault.Treeview",
        font=("Segoe UI", 10),
        rowheight=36,
        background="white",
        fieldbackground="white"
    )

    style.configure(
        "Vault.Treeview.Heading",
        font=("Segoe UI", 9, "bold"),
        padding=10
    )

    style.map(
        "Vault.Treeview",
        background=[
            ("selected", "#dbeafe")
        ],
        foreground=[
            ("selected", "#14283d")
        ]
    )

    file_tree = ttk.Treeview(
        table_frame,
        columns=(
            "file",
            "size",
            "status"
        ),
        show="headings",
        style="Vault.Treeview",
        selectmode="browse"
    )

    file_tree.heading(
        "file",
        text="FILE NAME"
    )

    file_tree.heading(
        "size",
        text="SIZE"
    )

    file_tree.heading(
        "status",
        text="SECURITY"
    )

    file_tree.column(
        "file",
        width=500,
        anchor="w"
    )

    file_tree.column(
        "size",
        width=160,
        anchor="center"
    )

    file_tree.column(
        "status",
        width=180,
        anchor="center"
    )

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=file_tree.yview
    )

    file_tree.configure(
        yscrollcommand=scrollbar.set
    )

    file_tree.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    # =========================================================
    # BUTTON STYLE
    # =========================================================

    style.configure(
        "Vault.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=(16, 10)
    )

    # =========================================================
    # BUTTONS
    # =========================================================

    buttons = tk.Frame(
        card,
        bg="white"
    )

    buttons.pack(
        fill="x",
        padx=25,
        pady=(12, 20)
    )

    ttk.Button(
        buttons,
        text="⬆  Upload / Encrypt",
        command=upload,
        style="Vault.TButton"
    ).pack(
        side="left",
        padx=(0, 8)
    )

    ttk.Button(
        buttons,
        text="🔓  Open / Decrypt",
        command=open_file,
        style="Vault.TButton"
    ).pack(
        side="left",
        padx=8
    )

    ttk.Button(
        buttons,
        text="Delete",
        command=delete,
        style="Vault.TButton"
    ).pack(
        side="left",
        padx=8
    )

    ttk.Button(
        buttons,
        text="Refresh",
        command=refresh,
        style="Vault.TButton"
    ).pack(
        side="left",
        padx=8
    )

    ttk.Button(
        buttons,
        text="Exit",
        command=close,
        style="Vault.TButton"
    ).pack(
        side="right"
    )

    # =========================================================
    # FOOTER
    # =========================================================

    tk.Label(
        card,
        text="🔒  Files are stored in encrypted form.",
        font=("Segoe UI", 9),
        bg="white",
        fg="#718096"
    ).pack(
        pady=(0, 15)
    )

    # =========================================================
    # INITIAL REFRESH
    # =========================================================

    refresh()

    root.protocol(
        "WM_DELETE_WINDOW",
        close
    )

    root.mainloop()