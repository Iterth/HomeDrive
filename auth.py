import sqlite3
from werkzeug import security

def add_user(username, password, is_admin):

    name = username
    passw = password
    admin_panel = is_admin

    hashed_passw = security.generate_password_hash(passw)

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute(
    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
    (name, hashed_passw, admin_panel)
)
    
    conn.commit()
    conn.close()


def check_user(username, password):

    name = username
    passw = password

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ?', (name,))
    result = cursor.fetchone()

    if result and security.check_password_hash(result[2], passw):
        return True
    return False

def get_storage_limit(username):

    name = username

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT storage_limit FROM users WHERE username = ?', (name,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return 5368709120

def set_storage_limit(username, limit_bytes):

    name = username
    new_limit = limit_bytes

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET storage_limit = ? WHERE username = ?', (new_limit, name))
    
    conn.commit()
    conn.close()


def toggle_favorite(username, file_path):

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM favorites WHERE username = ? AND file_path = ?", (username, file_path))
    result = cursor.fetchone()
    
    if result:
        cursor.execute("DELETE FROM favorites WHERE id = ?", (result['id'],))
        is_added = False
    else:
        cursor.execute("INSERT INTO favorites (username, file_path) VALUES (?, ?)", (username, file_path))
        is_added = True
        
    conn.commit()
    conn.close()
    return is_added

def get_user_favorites(username):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM favorites WHERE username = ?", (username,))
    results = cursor.fetchall()
    conn.close()
    return [row['file_path'] for row in results]

def role_check(username):
    name = username

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT role FROM users WHERE username = ?', (name,))
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        return False

def get_all_users():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role, storage_limit FROM users')
    results = cursor.fetchall()
    conn.close()
    return results

def delete_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def get_admin_count():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE role >= 1')
    result = cursor.fetchone()
    conn.close()
    return result[0]

def toggle_admin(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET role = CASE WHEN role = 1 THEN 0 ELSE 1 END WHERE username = ?',
        (username,)
    )
    conn.commit()
    conn.close()