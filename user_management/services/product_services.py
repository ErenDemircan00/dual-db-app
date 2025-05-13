from user_management.repositories.mongo_repository import MongoProductRepository
from flask_pymongo import PyMongo


class ProductService:
    def __init__(self, product_repository):
        self.product_repository = product_repository

    def get_all_products(self):
        return self.product_repository.find_all()
