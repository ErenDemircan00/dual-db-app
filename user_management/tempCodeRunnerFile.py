from flask import Flask, request, render_template, redirect, url_for, jsonify, make_response, session, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from functools import wraps
from flask_mail import Mail, Message


from user_management.repositories.mysql_repository import MySQLUserRepository
from user_management.repositories.mongo_repository import MongoProductRepository
from user_management.services.auth_service import AuthService
from user_management.services.product_services import ProductService
from user_management.utils.email_service import send_cart_update_email

import os 
import jwt
import datetime
import sys
import subprocess
from user_management.config import Config

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__, template_folder='templates')

app.config.from_object(Config)
bcrypt = Bcrypt(app)
mysql = MySQL(app)
mail = Mail(app)
# MongoDB bağlantısı
client = MongoClient(os.getenv('MONGO_URI'))
db = client['shop'] 
products_collection = db['products']
cart_collection = db['cart']  


user_repository = MySQLUserRepository(mysql)
product_repository = MongoProductRepository(client)
auth_service = AuthService(user_repository, bcrypt, mail)
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

def create_token(user):
    return jwt.encode({
        'user_id': user['id'],
        'username': user['username'],
        'user_type': user['user_type'],
        'exp': datetime.datetime.today() + datetime.timedelta(hours=2)
    }, app.secret_key, algorithm='HS256')
    
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

        if auth_service.register(username, hashed_password, email, user_type):
            return redirect(url_for('login'))
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
            
            session['username'] = user['username']
            session['user_type'] = user['user_type']

            token = create_token(user)
            
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
    # Filtreleme ve sıralama parametrelerini al
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'price_asc')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Temel sorgu
    query = {}
    
    # Arama filtresi ekle
    if search_query:
        query['name'] = {'$regex': search_query, '$options': 'i'}  # case-insensitive arama
    
    # Fiyat filtresi ekle
    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter['$gte'] = min_price
        if max_price is not None:
            price_filter['$lte'] = max_price
        if price_filter:
            query['price'] = price_filter
    
    # Sıralama
    sort_direction = 1 if sort_by == 'price_asc' else -1
    products = list(products_collection.find(query).sort('price', sort_direction))
    
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

# E-posta gönderme fonksiyonu
def send_cart_update_email(user_email, action_type, product_name=None):
    try:
        subject = 'Sepet Güncellemesi'
        
        if action_type == 'add':
            body = f'"{product_name}" ürünü sepetinize eklendi. Alışverişinizi tamamlamak için sitemizi ziyaret edebilirsiniz.'
        elif action_type == 'remove':
            body = f'"{product_name}" ürünü sepetinizden çıkarıldı.'
        elif action_type == 'update':
            body = f'"{product_name}" ürününün sepetinizdeki miktarı güncellendi.'
        else:
            body = 'Sepetinizde bir değişiklik yapıldı. Lütfen kontrol edin.'
        
        msg = Message(subject, recipients=[user_email])
        msg.body = body
        mail.send(msg)
        print(f"E-posta başarıyla gönderildi: {user_email}")
        return True
    except Exception as e:
        print(f"E-posta gönderim hatası: {str(e)}")
        return False

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
        
        # Kullanıcıya e-posta gönder
        user = user_repository.find_by_id(current_user['id'])
        if user and 'email' in user:
            send_cart_update_email(user['email'], 'add', product['name'])
        
        return redirect(url_for('view_cart'))
    
    return redirect(url_for('list_products'))

@app.route("/delete-product/<product_id>", methods=["POST"])
def delete_product(product_id):
    if session.get("user_type") == "admin":
        products_collection.delete_one({"_id": ObjectId(product_id)})
        return redirect(url_for("list_products"))
    else:
        if "username" not in session or session.get("user_type") != "supplier" and session.get("user_type") != "admin":
            return "Yetkiniz yok!", 403
    
        # burada ürünü sadece bu kullanıcı eklediyse silsin (opsiyonel güvenlik)
        product = products_collection.find_one({"_id": ObjectId(product_id)})
    
        if product["created_by"] != session["username"]:
            return "Bu ürünü silme yetkiniz yok!", 403
    
        products_collection.delete_one({"_id": ObjectId(product_id)})
        return redirect(url_for("list_products"))



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
    # Ürün adını bul (e-posta için)
    cart_item = cart_collection.find_one({'_id': ObjectId(item_id), 'user_id': current_user['id']})
    product_name = cart_item['name'] if cart_item else "Ürün"
    
    # Ürünü sepetten kaldır
    cart_collection.delete_one({'_id': ObjectId(item_id), 'user_id': current_user['id']})
    
    # Kullanıcıya e-posta gönder
    user = user_repository.find_by_id(current_user['id'])
    if user and 'email' in user:
        send_cart_update_email(user['email'], 'remove', product_name)
    
    return redirect(url_for('view_cart'))

# Sepetteki ürün miktarını güncelleme
@app.route('/update-cart/<item_id>', methods=['POST'])
@token_required
def update_cart(current_user, item_id):
    # Ürün adını bul (e-posta için)
    cart_item = cart_collection.find_one({'_id': ObjectId(item_id), 'user_id': current_user['id']})
    product_name = cart_item['name'] if cart_item else "Ürün"
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > 0:
        cart_collection.update_one(
            {'_id': ObjectId(item_id), 'user_id': current_user['id']},
            {'$set': {'quantity': quantity}}
        )
        
        # Kullanıcıya e-posta gönder
        user = user_repository.find_by_id(current_user['id'])
        if user and 'email' in user:
            send_cart_update_email(user['email'], 'update', product_name)
    else:
        # Miktar 0 veya negatifse ürünü sepetten kaldır
        cart_collection.delete_one({'_id': ObjectId(item_id), 'user_id': current_user['id']})
        
        # Kullanıcıya e-posta gönder
        user = user_repository.find_by_id(current_user['id'])
        if user and 'email' in user:
            send_cart_update_email(user['email'], 'remove', product_name)
    
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
@token_required
def checkout(current_user):
    # Kullanıcının sepetindeki ürünleri bul
    cart_items = list(cart_collection.find({'user_id': current_user['id']}))
    
    if not cart_items:
        flash('Sepetiniz boş!', 'error')
        return redirect(url_for('view_cart'))

    # Her bir sepet öğesi için ürün sahibine e-posta gönder
    for item in cart_items:
        # Ürünü MongoDB'den bul
        product = products_collection.find_one({'_id': ObjectId(item['product_id'])})
        if product and 'user_id' in product:
            # Ürün sahibinin bilgilerini MySQL'den al
            owner = user_repository.find_by_id(product['user_id'])
            if owner and 'email' in owner:
                try:
                    msg = Message(
                        subject='Ürününüz Satıldı!',
                        recipients=[owner['email']],
                        body=f"""
                        Merhaba {owner['username']},

                        '{item['name']}' adlı ürününüz satılmıştır!
                        Detaylar:
                        - Ürün: {item['name']}
                        - Fiyat: {item['price']} TL
                        - Adet: {item['quantity']}
                        - Toplam: {item['price'] * item['quantity']} TL
                        """
                    )
                    mail.send(msg)
                except Exception as e:
                    flash(f'E-posta gönderim hatası: {str(e)}', 'error')
                    return redirect(url_for('view_cart'))
            else:
                flash(f'Ürün sahibi ({product["created_by"]}) için e-posta adresi bulunamadı.', 'warning')

    # Sepeti temizleme
    cart_collection.delete_many({'user_id': current_user['id']})
    flash('Satın alma başarılı! Ürün sahiplerine e-posta gönderildi.', 'success')
    return redirect(url_for('list_products'))

# Profil görüntüleme ve düzenleme
@app.route('/profile', methods=['GET', 'POST'])
@token_required
def profile(current_user):
    message = None
    success = None
    
    # Kullanıcının güncel bilgilerini alalım
    user = user_repository.find_by_id(current_user['id'])
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        success, message = auth_service.update_profile(
            current_user['id'], 
            username, 
            email, 
            current_password, 
            new_password
        )
        
        if success and username and username != current_user['username']:
            # Kullanıcı adı değiştiyse yeni token oluştur
            token = jwt.encode({
                'user_id': current_user['id'],
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }, app.secret_key, algorithm='HS256')
            
            # Session bilgilerini güncelle
            session['username'] = username
            
            response = make_response(render_template('profile.html', 
                                                    user=user_repository.find_by_id(current_user['id']),
                                                    message=message,
                                                    success=success))
            response.set_cookie('token', token, httponly=True, max_age=7200)
            return response
    
    return render_template('profile.html', user=user, message=message, success=success)


@app.route("/forget_password", methods=['POST'])
def forget_password():
    email = request.form['email']
    user = user_repository.get_user_mail(email) 
    
    if not user:
        return jsonify({'message': 'Bu e-posta adresine ait kullanici bulunamadı'}), 404
    
    reset_token = create_token(user)
    verify_link = url_for('verify_reset_token', token=reset_token, _external=True)
    auth_service.send_verification_email(user['email'], verify_link)  

    return jsonify({'message': 'Sifre sifirlama linki e-posta adresinize gonderildi.'})

@app.route("/verify_reset/<token>")
def verify_reset_token(token):
    try:
        jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return redirect(f"/reset-password?token={token}")
    except jwt.ExpiredSignatureError:
        return "Baglantı suresi dolmus. Lütfen tekrar deneyin.", 400
    except jwt.InvalidTokenError:
        return "Geçersiz bağlantı.", 400
    
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get('token')
    if not token:
        return "Token bulunamadı", 400
    
    try:
        user_data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        
        if request.method == "GET":
            return render_template("reset_password.html", token=token)
        
        elif request.method == "POST":
            data = request.get_json()
            if not data or 'new_password' not in data:
                return jsonify({"message": "Yeni şifre gönderilmedi."}), 400
                
            new_password = data['new_password']
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user_repository.update_password(user_data['user_id'], hashed_password)
            
            return jsonify({"message": "Şifreniz başarıyla güncellendi."}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Bağlantı süresi dolmuş. Lütfen tekrar deneyin."}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Geçersiz bağlantı."}), 400
    except Exception as e:
        return jsonify({"message": f"Bir hata oluştu: {str(e)}"}), 500


    
@app.route('/forget_password', methods=['GET'])
def show_forget_password_form():
        return render_template('forget_password.html')
    
# Çıkış Yap
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('token', '', expires=0)  # Token cookie'sini sil
    return response


@app.route('/test-email')
def test_email():
    try:
        msg = Message('Test Email', recipients=['akyolalper88@gmail.com'])
        msg.body = 'Bu bir test e-postasıdır.'
        mail.send(msg)
        return 'E-posta gönderildi!'
    except Exception as e:
        return f"E-posta gönderme hatası: {str(e)}"
    
    
@app.route('/admin')
@token_required
def admin_dashboard(current_user):
    if current_user['user_type'] != 'admin':
        return redirect(url_for('list_products'))
    
    # Tüm kullanıcıları getir
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.close()
    
    return render_template('admin.html', users=users)
    
    
if __name__ == '__main__':
    print("Testler çalışıyor...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/unit/test_app.py test_user_repository.py"], capture_output=False)
    result2 = subprocess.run([sys.executable, "-m", "pytest", "tests/unit/"], capture_output=False)
    #result3 = subprocess.run([sys.executable, "-m", "pytest", "tests/ui/test_auth_with_supplier.py tests/ui/test_product_supplier.py tests/ui/test_logout.py -v -s"], capture_output=False)
    #result4 = subprocess.run([sys.executable, "-m", "pytest", "pytest ui/test_auth.py ui/test_cart.py ui/test_profile.py ui/test_logout.py -v -s"], capture_output=False)
    if result.returncode != 0:
        print("Testler başarısız oldu, uygulama başlatılmıyor.")
        sys.exit(result.returncode)
    
    print("Testler başarılı, uygulama başlatılıyor...")
    app.run(debug=True)