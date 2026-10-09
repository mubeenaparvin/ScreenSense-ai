import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "database/screensense.db"

connection = sqlite3.connect(DATABASE)

connection.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

admin_name = "Admin"
admin_email = "admin@screensense.com"
admin_password = "admin123"

hashed_password = generate_password_hash(admin_password)

try:
    connection.execute(
        """
        INSERT INTO admins (name, email, password)
        VALUES (?, ?, ?)
        """,
        (admin_name, admin_email, hashed_password)
    )

    connection.commit()
    print("Admin account created successfully!")

except sqlite3.IntegrityError:
    print("Admin account already exists.")

connection.close()