<<<<<<< Updated upstream
from user_management.repositories.mongo_repository import MongoProductRepository
=======
from repositories.mongo_repository import MongoProductRepository
>>>>>>> Stashed changes
from flask_pymongo import PyMongo


class ProductService:
    def __init__(self, product_repository):
        self.product_repository = product_repository

    def get_all_products(self):
        return self.product_repository.find_all()
<<<<<<< Updated upstream
=======
    
    def get_product_by_id(self, product_id):
        return self.product_repository.find_by_id(product_id)
    
# MongoDB bağlantısı test sırasında mock'lanacak
product_service = None  # Bu değişken app.py'de initialize edilecek
>>>>>>> Stashed changes
