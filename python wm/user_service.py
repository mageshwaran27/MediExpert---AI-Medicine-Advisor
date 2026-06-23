from db_helper import get_connection

def register_user(name, email, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name,email,password) VALUES (:n,:e,:p)",
                    {'n': name, 'e': email, 'p': password})
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE email=:e AND password=:p", {'e': email, 'p': password})
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
