from abc import ABC, abstractmethod
from flask_mysqldb import MySQL

class BaseRepository(ABC):
    @abstractmethod
    def save(self, data):
        pass

    @abstractmethod
    def find_by_username(self, username):
        pass

class MySQLUserRepository(BaseRepository):
    def __init__(self, mysql: MySQL):
        self.mysql = mysql

    def save(self, data):
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute("USE user_management")
            cursor.execute(
                "INSERT INTO users (username, password, email, user_type) VALUES (%s, %s, %s, %s)",
                (data['username'], data['password'], data['email'], data['user_type'])
            )
            self.mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Kayıt hatası: {str(e)}")
            return False

    def find_by_username(self, username):
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute("USE user_management")
            cursor.execute(
                "SELECT id, username, password, email, user_type FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'password': user[2],
                    'email': user[3],
                    'user_type': user[4],
                }
            return None
        except Exception as e:
            print(f"Arama hatası: {str(e)}")
            return None
        
    def get_user_mail(self, email):
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute("USE user_management")
            cursor.execute(
                "SELECT id, username, password, email, user_type FROM users WHERE email = %s",  
                (email,)
            )
            user = cursor.fetchone()
            cursor.close()
        
            if user:
                return {
                    'id': user[0],           
                    'username': user[1],
                    'password': user[2],     
                    'email': user[3],
                    'user_type': user[4],
                }
            return None
        except Exception as e:
            print(f"Arama hatası: {str(e)}")
            return None
    def update_password(self, user_id, new_hashed_password):
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute("USE user_management")
            query = "UPDATE users SET password = %s WHERE id = %s"
            cursor.execute(query, (new_hashed_password, user_id))
            self.mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Şifre güncelleme hatası: {str(e)}")
            return False
