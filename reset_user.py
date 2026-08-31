import getpass
import database

username = input("Enter username: ").strip()
new_password = getpass.getpass("Enter new password: ")

ok, msg = database.password_policy(new_password)
if not ok:
    print(msg)
else:
    print("Password reset successful" if database.reset_password(username, new_password) else "User not found")
