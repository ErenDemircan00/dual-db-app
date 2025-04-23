from flask import Flask, request, render_template,jsonify, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_pymongo import PyMongo
import pymysql
import os


load_dotenv()

app = Flask(__name__)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)


# Bcrypt için ayar
bcrypt = Bcrypt(app)

# MySQL bağlantısı için ayar
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')  # .env dosyasındaki MYSQL_HOST kullanılır
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')  # .env dosyasındaki MYSQL_USER kullanılır
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')  # .env dosyasındaki MYSQL_PASSWORD kullanılır
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')  # .env dosyasındaki MYSQL_DB kullanılır
app.secret_key = os.getenv('SECRET_KEY') or "12345"  # Session için secret key

mysql = MySQL(app)

all_product = mongo.db.products

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
        cursor.execute("USE users")
        cursor.execute("INSERT INTO user (username, password, email) VALUES (%s, %s, %s)", (username, plain_password, email))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('index'))

    return render_template('signup.html')

# Kullanıcı Giriş Sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()  # Boşlukları temizle
        password = request.form['password'].strip()  # Boşlukları temizle
        
        # Kullanıcıyı veritabanında ara
        cursor = mysql.connection.cursor()
        cursor.execute("USE users")
        cursor.execute("SELECT * FROM user WHERE username = %s", [username])
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Kullanıcı ve şifreyi kontrol et
            if user[2] == password:  # Şifreyi olduğu gibi karşılaştırıyoruz
                session["user_logged_in"] = True
                session["username"] = username
                return redirect(url_for('products'))
                
            else:
                session["user_logged_in"] = False
                return 'Invalid credentials'
        else:
            session["user_logged_in"] = False
            return 'Invalid credentials'

    return render_template('login.html')

@app.route('/products',methods=['GET'])
def products():
    try:
        product_list = list(all_product.find({}, {'_id': 0}))  # _id hariç tüm alanları döndür
        return render_template('products.html', products=product_list)
    except Exception as e:
        return jsonify({"error": f"Ürünler listelenirken hata: {str(e)}"}), 500
    

if __name__ == '__main__':
    app.run(debug=True)
