import database
from auth import add_user
import getpass

print("☁️ Welcome to the HomeDrive Setup Wizard. ☁️\n")
print("[*] Checking/creating database tables...")
database

print("[*] The system is ready. Please create the top-level authorized (Founder/Host) account.\n")
username = input("HOST Username: ")
password = getpass.getpass("HOST Password: ")

try:
    add_user(username, password, 2)
    print(f"\n[+] Success! The HOST account named '{username}' has been created.")
    print("[+] Installation is complete. You can start the server with the command 'python main.py'.")
except Exception as e:
    print(f"\n[-] ERROR: {e}")