from flask import Flask, request, render_template, redirect, url_for
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)

# Bcrypt için ayar
bcrypt = Bcrypt(app)

# MySQL bağlantısı için ayar
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')  # .env dosyasındaki MYSQL_HOST kullanılır
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')  # .env dosyasındaki MYSQL_USER kullanılır
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')  # .env dosyasındaki MYSQL_PASSWORD kullanılır
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')  # .env dosyasındaki MYSQL_DB kullanılır
app.secret_key = os.getenv('SECRET_KEY')  # Session için secret key

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
        
        # Şifreyi olduğu gibi alıyoruz (hash'lemiyoruz)
        plain_password = password  # Şifreyi düz haliyle kaydediyoruz

        # Veritabanına ekle
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, plain_password, email))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

# Kullanıcı Giriş Sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()  # Boşlukları temizle
        password = request.form['password'].strip()  # Boşlukları temizle
        
        # Kullanıcıyı veritabanında ara
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Kullanıcı ve şifreyi kontrol et
            if user[2] == password:  # Şifreyi olduğu gibi karşılaştırıyoruz
                return 'Login successful!'
            else:
                return 'Invalid credentials'
        else:
            return 'Invalid credentials'

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
