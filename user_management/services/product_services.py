from user_management.repositories.mongo_repository import mongo_repository


class ProductService:
    def __init__(self, product_repository):
        self.product_repository = product_repository

    def get_all_products(self):
        return self.product_repository.find_all()
    
product_service = ProductService(mongo_repository())
