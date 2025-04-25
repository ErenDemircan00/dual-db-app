import os
from models.user import User
from flask_mail import Message

class AuthService:
    def __init__(self, user_repository, bcrypt, mail):
        self.user_repository = user_repository
        self.bcrypt = bcrypt
        self.mail = mail

    def register(self, username, password, email, user_type='customer'):
        user_data = User(username, password, email,user_type).to_dict()
        return self.user_repository.save(user_data)

    def login(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user:
            if self.bcrypt.check_password_hash(user['password'], password):
                return user
        return None
    
    def send_verification_email(self, to_email, verify_link):
        try:
            print(f"✅ send_verification_email çağrıldı: {to_email}")
            print(f"🔗 Link: {verify_link}")
            msg = Message(
                'Şifre Sıfırlama Doğrulama',
                recipients=[to_email]
            )
            msg.body = f"Şifre sıfırlamak için bu bağlantıya tıklayın: {verify_link}\nBu bağlantı 15 dakika geçerlidir."
            self.mail.send(msg)
            print("📤 Mail başarıyla gönderildi.")
        except Exception as e:
            print(f"❌ E-posta gönderme hatası: {str(e)}")
