import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        storage_limit INTEGER DEFAULT 5368709120,
        role INTEGER DEFAULT 0
    )
''')

cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            file_path TEXT NOT NULL,
            UNIQUE(username, file_path)
        )
    ''')

conn.commit()
conn.close()