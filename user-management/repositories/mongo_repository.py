from abc import ABC, abstractmethod
from flask_pymongo import PyMongo

class MongoBaseRepository(ABC):
    @abstractmethod
    def find_all(self):
        pass

class MongoProductRepository(MongoBaseRepository):
    def __init__(self, mongo: PyMongo):
        self.collection = mongo.db.products

    def find_all(self):
        try:
            return list(self.collection.find({}, {'_id': 0}))
        except Exception as e:
            print(f"Ürün listeleme hatası: {str(e)}")
            return []