from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
import jwt
import datetime

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)

# Bcrypt ve JWT ayarları
bcrypt = Bcrypt(app)
app.secret_key = os.getenv('SECRET_KEY')  # Session ve JWT için

# MySQL bağlantısı için ayar
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

# Anasayfa
@app.route('/')
def index():
    return render_template('index.html')

# Kullanıcı Kayıt Sayfası
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Şifre hash’leniyor
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

# Kullanıcı Giriş Sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", [username])
        user = cursor.fetchone()
        cursor.close()
        
        # Debug için
        print(f"Kullanıcı: {user}")
        
        if user:
            # User[0] = id, User[1] = username, User[2] = password olduğunu doğrulayalım
            user_id, user_name, hashed_password = user
            
            print(f"Şifre kontrolü: {password}, Hash: {hashed_password}")
            
            try:
                # Şifreyi doğrulamayı dene
                if bcrypt.check_password_hash(hashed_password, password):
                    # JWT Token oluştur
                    token = jwt.encode({
                        'user_id': user_id,
                        'username': user_name,
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
                    }, app.secret_key, algorithm='HS256')
                    
                    return jsonify({'message': 'Giriş başarılı', 'token': token})
                else:
                    return jsonify({'message': 'Geçersiz şifre'}), 401
            except ValueError as e:
                # Hata detayını kaydet
                print(f"Şifre doğrulama hatası: {e}, Hash: {hashed_password}")
                return jsonify({'message': f'Şifre doğrulama hatası: {e}'}), 500
            except Exception as e:
                print(f"Beklenmeyen hata: {e}")
                return jsonify({'message': 'Bir hata oluştu'}), 500
        
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 401
    
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
