from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
from repositories.mysql_repository import MySQLUserRepository
from repositories.mongo_repository import MongoProductRepository
from services.auth_service import AuthService
from services.product_service import ProductService

load_dotenv()

app = Flask(__name__)

# Flask yapılandırmaları
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.secret_key = os.getenv('SECRET_KEY') or '12345'

mysql = MySQL(app)
mongo = PyMongo(app)

user_repository = MySQLUserRepository(mysql)
product_repository = MongoProductRepository(mongo)
auth_service = AuthService(user_repository)
product_service = ProductService(product_repository)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        email = request.form['email'].strip()
        user_type = request.form['user_type'].strip()

        if user_type not in ['customer', 'supplier']:
            return jsonify({"error": "Geçersiz kullanıcı tipi"}), 400

        if auth_service.register(username, password, email, user_type):
            return redirect(url_for('index'))
        else:
            return jsonify({"error": "Kayıt başarısız"}), 500

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        user = auth_service.login(username, password)
        if user:
            session['user_logged_in'] = True
            session['username'] = user['username']
            session['user_id'] = user['user_id']
            session['user_type'] = user['user_type']
            return redirect(url_for('products'))
        else:
            session['user_logged_in'] = False
            return 'Geçersiz kimlik bilgileri'

    return render_template('login.html')

@app.route('/products', methods=['GET'])
def products():
    try:
        product_list = product_service.get_all_products()
        return render_template('products.html', products=product_list)
    except Exception as e:
        return jsonify({"error": f"Ürünler listelenirken hata: {str(e)}"}), 500

@app.route('/api/products', methods=['GET'])
def api_products():
    try:
        product_list = product_service.get_all_products()
        return jsonify(product_list), 200
    except Exception as e:
        return jsonify({"error": f"Ürünler listelenirken hata: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)