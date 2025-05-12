from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # .env dosyasını yükle

client = MongoClient(os.getenv("MONGO_URI"))
db = client["shop"]  # veya istediğin isim, örneğin "ecommerce"
products_collection = db["products"]  # koleksiyon: ürünler
