import sqlite3

connection = sqlite3.connect("database/users.db")

cursor = connection.cursor()

cursor.execute("""
SELECT username, email, password_hash
FROM users
""")

users = cursor.fetchall()

print("Number of users:", len(users))

for user in users:
    print("Username:", user[0])
    print("Email:", user[1])
    print("Password Hash:", user[2])
    print("-" * 50)

connection.close()