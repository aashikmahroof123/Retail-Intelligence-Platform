
from getpass import getpass

from database import get_connection
from auth import password_hash


username = input("Enter administrator username: ").strip()
password = getpass("Enter administrator password: ")
confirm_password = getpass("Confirm administrator password: ")

if not username:
    raise ValueError("Username cannot be empty")

if len(password) < 4:
    raise ValueError("Use a password with at least 4 characters")

if password != confirm_password:
    raise ValueError("Passwords do not match")

hashed_password = password_hash.hash(password)

connection = get_connection()

try:
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO admins (username, password_hash)
        VALUES (%s, %s)
        """,
        (username, hashed_password),
    )

    connection.commit()
    print("Administrator account created successfully.")

except Exception:
    connection.rollback()
    raise

finally:
    cursor.close()
    connection.close()
