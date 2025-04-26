<h1>dual-db-app</h1>

## Gereksinimler
- Python 3.8+
- MySQL
- MongoDB
- Git

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/ErenDemircan00/dual-db-app.git
cd dual-db-app/user-management
```
### 2. Sanal Ortam Oluşturun
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# veya
source venv/bin/activate  # Linux/macOS
```
### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```
### 4. Çevresel Değişkenleri Ayarlayın
Proje kök dizininde .env dosyasını oluşturun:
```.env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=users
MONGO_URI=mongodb://localhost:27017/ecommerce
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587  #TLS port
MAIL_USERNAME=email adres
MAIL_PASSWORD=Password #google hesap ayarlarından > Güvenlik > Uygulama şifreleri'dan şifre oluştur
MAIL_DEFAULT_SENDER=deafult email adress
```
### 5. MySQL Veritabanını Kurun
MySQL’de users veritabanını ve user tablosunu oluşturun:
```sql
CREATE DATABASE users;
USE users;
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    user_type ENUM('customer', 'supplier') NOT NULL DEFAULT 'customer'
);
```
### 6. MongoDB Veritabanını Kurun

### 7. Uygulamayı Çalıştırın
```bash
python app.py
```
