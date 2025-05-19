import os
from user_management.models.user import User
from flask_mail import Message

class AuthService:
    def __init__(self, user_repository, bcrypt, mail):
        self.user_repository = user_repository
        self.bcrypt = bcrypt
        self.mail = mail

    def register(self, username, password, email, user_type='customer'):
        user_data = User(username, password, email, user_type).to_dict()
        return self.user_repository.save(user_data)
    
    def login(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user:
            if self.bcrypt.check_password_hash(user['password'], password):
                return user
        return None
    
    def update_profile(self, user_id, username=None, email=None, current_password=None, new_password=None):
        # Önce kullanıcıyı ID ile bulalım
        user = self.user_repository.find_by_id(user_id)
        
        if not user:
            return False, "Kullanıcı bulunamadı."
        
        # Şifre değişikliği istenmişse, mevcut şifreyi kontrol et
        if new_password:
            if not current_password or not self.bcrypt.check_password_hash(user['password'], current_password):
                return False, "Mevcut şifre yanlış."
            # Yeni şifreyi hashle
            hashed_password = self.bcrypt.generate_password_hash(new_password).decode('utf-8')
        else:
            hashed_password = None
        
        # Kullanıcı adı veya email değişikliği istenmişse, bu değerlerin başka kullanıcılarda
        # kullanılmadığından emin olmalıyız
        if username and username != user['username']:
            existing_user = self.user_repository.find_by_username(username)
            if existing_user:
                return False, "Bu kullanıcı adı zaten kullanılıyor."
        
        if email and email != user['email']:
            existing_user = self.user_repository.find_by_email(email)
            if existing_user:
                return False, "Bu e-posta adresi zaten kullanılıyor."
        
        # Profili güncelle
        update_data = {}
        if username:
            update_data['username'] = username
        if email:
            update_data['email'] = email
        if hashed_password:
            update_data['password'] = hashed_password
        
        if update_data:
            success = self.user_repository.update_user(user_id, update_data)
            if success:
                return True, "Profil başarıyla güncellendi."
            else:
                return False, "Profil güncellenirken bir hata oluştu."
        
        return False, "Değişiklik yapılmadı."
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
