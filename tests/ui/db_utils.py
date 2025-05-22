import MySQLdb

def cleanup_test_users():
    conn = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="1234",
        db="user_management",
    )
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE is_test_user = TRUE")
    conn.commit()
    cursor.close()
    conn.close()
