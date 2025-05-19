from user_management.repositories.mongo_repository import MongoProductRepository
from flask_pymongo import PyMongo


class ProductService:
    def __init__(self, product_repository):
        self.product_repository = product_repository

    def get_all_products(self):
        return self.product_repository.find_all()
    
    def get_product_by_id(self, product_id):
        return self.product_repository.find_by_id(product_id)
    
product_service = None 
