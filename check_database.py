import sqlite3

connection = sqlite3.connect("database/screensense.db")

cursor = connection.cursor()

# Show tables
cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""")

tables = cursor.fetchall()

print("Tables:")

for table in tables:
    print("-", table[0])

# Show predictions table structure
print("\nPredictions table structure:")

cursor.execute("PRAGMA table_info(predictions)")

columns = cursor.fetchall()

for column in columns:
    print(column)

connection.close()