from flask import Flask, request, render_template, redirect, url_for
from flask_mysql import MySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Bcrypt için ayar
bcrypt = Bcrypt(app)



mysql = MySQL(app)

# Anasayfa
@app.route('/')
def index():
    return 'Welcome to the User Management App'

# Kayıt Sayfası
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Şifreyi hash'le
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Veritabanına ekle
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

# Giriş Sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Kullanıcıyı veritabanında ara
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cursor.fetchone()
        cursor.close()
        
        if user and bcrypt.check_password_hash(user['password'], password):
            return 'Login successful!'
        else:
            return 'Invalid credentials'

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
