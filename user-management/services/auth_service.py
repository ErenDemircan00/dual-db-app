import os
from models.user import User

class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register(self, username, password, email, user_type='customer'):
        user_data = User(username, password, email, user_type).to_dict()
        return self.user_repository.save(user_data)

    def login(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user:
            if password == user['password']:
                return user
        return None