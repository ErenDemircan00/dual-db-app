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
    
    def find_by_id(self, user_id):
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute("USE user_management")
            cursor.execute(
                "SELECT id, username, password, email, user_type FROM users WHERE id = %s",
                (user_id,)
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
            print(f"ID ile arama hatası: {str(e)}")
            return None
    
    def find_by_email(self, email):
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
            print(f"E-posta ile arama hatası: {str(e)}")
            return None
    
    def update_user(self, user_id, update_data):
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute("USE user_management")
            
            # Dinamik SQL oluştur
            set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
            values = list(update_data.values())
            values.append(user_id)  # WHERE koşulu için
            
            sql = f"UPDATE users SET {set_clause} WHERE id = %s"
            cursor.execute(sql, values)
            
            self.mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Kullanıcı güncelleme hatası: {str(e)}")
            return False