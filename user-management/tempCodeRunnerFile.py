from flask import Flask, request, render_template, redirect, url_for, jsonify, make_response,session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from functools import wraps

from repositories.mysql_repository import MySQLUserRepository
from repositories.mongo_repository import MongoProductRepository
from services.auth_service import AuthService
from services.product_service import ProductService

import os
import jwt
import datetime

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__, template_folder='templates')

# Bcrypt ve JWT ayarları
bcrypt = Bcrypt(app)
app.secret_key = os.getenv('SECRET_KEY')  # Session ve JWT için

# MySQL bağlantısı için ayar
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

# MongoDB bağlantısı
client = MongoClient(os.getenv('MONGO_URI'))
db = client['shop']  # veya os.getenv('MONGO_DB_NAME')
products_collection = db['products']
cart_collection = db['cart']  # Sepet için yeni koleksiyon

user_repository = MySQLUserRepository(mysql)
product_repository = MongoProductRepository(mongo)
auth_service = AuthService(user_repository  , bcrypt)
product_service = ProductService(product_repository)

# Token doğrulama dekoratörü
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Cookie'den veya Authorization header'dan token alınması
        if 'token' in request.cookies:
            token = request.cookies.get('token')
        elif 'Authorization' in request.headers:
            auth_header = request.headers.get('Authorization')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # 'Bearer ' kısmını kaldır
        
        if not token:
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'message': 'Token eksik!'}), 403
            return redirect(url_for('login'))
        
        try:
            # Token'ı doğrula
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            current_user = {'id': data['user_id'], 'username': data['username']}
        except:
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'message': 'Geçersiz token!'}), 403
            return redirect(url_for('login'))
            
        return f(current_user, *args, **kwargs)
    
    return decorated

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
        user_type = request.form['user_type']
        # Şifre hash'leniyor
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if auth_service.register(username,hashed_password,email, user_type):
            return redirect(url_for('index'))
        else:
            return jsonify({"error": "Kayit basarisiz"}), 500

    return render_template('signup.html')

# Kullanıcı Giriş Sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        is_api = request.headers.get('Content-Type') == 'application/json'

        if is_api:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
        else:
            username = request.form['username'].strip()
            password = request.form['password'].strip()

        user = auth_service.login(username, password)
        if user:

            session['user_logged_in'] = True
            session['username'] = user['username']
            session['id'] = user['id']
            session['user_type'] = user['user_type']

            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }, app.secret_key, algorithm='HS256')

            if is_api:
                return jsonify({'message': 'Giriş başarılı', 'token': token})

            response = make_response(redirect(url_for('list_products')))
            response.set_cookie('token', token, httponly=True, max_age=7200)
            return response
        else:
            if is_api:
                return jsonify({'message': 'Kullanıcı adı veya şifre hatalı'}), 401
            return render_template('login.html', error='Geçersiz kullanıcı adı veya şifre')

    return render_template('login.html')
# Ürün Ekleme Sayfası
@app.route('/add-product', methods=['GET', 'POST'])
@token_required
def add_product(current_user):
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        
        product = {
            "name": name, 
            "price": price, 
            "description": description,
            "user_id": current_user['id'],
            "created_by": current_user['username'],
            "created_at": datetime.datetime.utcnow()
        }
        
        products_collection.insert_one(product)
        return redirect(url_for('list_products'))
    
    return render_template('add_product.html')

# Ürün Listesi
@app.route('/products', methods=['GET'])
@token_required
def list_products(current_user):
    product_list = product_service.get_all_products()
    return render_template('product_list.html', products=products)

# API Endpoint - Ürün Ekleme
@app.route('/api/products', methods=['POST'])
@token_required
def api_add_product(current_user):
    data = request.get_json()
    
    if not data or 'name' not in data or 'price' not in data or 'description' not in data:
        return jsonify({'message': 'Ürün detayları eksik!'}), 400
    
    product = {
        "name": data['name'], 
        "price": float(data['price']), 
        "description": data['description'],
        "user_id": current_user['id'],
        "created_by": current_user['username'],
        "created_at": datetime.datetime.utcnow()
    }
    
    result = products_collection.insert_one(product)
    
    return jsonify({
        'message': 'Ürün başarıyla eklendi',
        'product_id': str(result.inserted_id)
    }), 201

# Sepete ürün ekleme
@app.route('/add-to-cart/<product_id>', methods=['POST'])
@token_required
def add_to_cart(current_user, product_id):
    # Ürünü veritabanından bul
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    
    if product:
        # Ürün sepette var mı kontrol et
        cart_item = cart_collection.find_one({
            'user_id': current_user['id'],
            'product_id': str(product['_id'])
        })
        
        if cart_item:
            # Ürün zaten sepette, miktarını artır
            cart_collection.update_one(
                {'_id': cart_item['_id']},
                {'$inc': {'quantity': 1}}
            )
        else:
            # Ürünü sepete ekle
            cart_item = {
                'user_id': current_user['id'],
                'product_id': str(product['_id']),
                'name': product['name'],
                'price': product['price'],
                'quantity': 1,
                'added_at': datetime.datetime.utcnow()
            }
            cart_collection.insert_one(cart_item)
        
        return redirect(url_for('view_cart'))
    
    return redirect(url_for('list_products'))

# Sepeti görüntüle
@app.route('/cart', methods=['GET'])
@token_required
def view_cart(current_user):
    # Kullanıcının sepetindeki ürünleri bul
    cart_items = list(cart_collection.find({'user_id': current_user['id']}))
    
    # Toplam tutarı hesapla
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)

# Sepetten ürün kaldırma
@app.route('/remove-from-cart/<item_id>', methods=['POST'])
@token_required
def remove_from_cart(current_user, item_id):
    cart_collection.delete_one({'_id': ObjectId(item_id), 'user_id': current_user['id']})
    
    return redirect(url_for('view_cart'))

# Sepetteki ürün miktarını güncelleme
@app.route('/update-cart/<item_id>', methods=['POST'])
@token_required
def update_cart(current_user, item_id):
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > 0:
        cart_collection.update_one(
            {'_id': ObjectId(item_id), 'user_id': current_user['id']},
            {'$set': {'quantity': quantity}}
        )
    else:
        # Miktar 0 veya negatifse ürünü sepetten kaldır
        cart_collection.delete_one({'_id': ObjectId(item_id), 'user_id': current_user['id']})
    
    return redirect(url_for('view_cart'))

# Çıkış Yap
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('token', '', expires=0)  # Token cookie'sini sil
    return response

if __name__ == '__main__':
    app.run(debug=True)