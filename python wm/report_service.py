from db_helper import get_connection

def submit_report(user_id, lat, lng, type_hint, description, image_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reports (user_id, lat, lng, type_hint, description, image_path)
        VALUES (:u,:lat,:lng,:t,:d,:img)
    """, {'u': user_id, 'lat': lat, 'lng': lng, 't': type_hint, 'd': description, 'img': image_path})
    conn.commit()
    conn.close()
