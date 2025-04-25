import os
from models.user import User
from flask_bcrypt import Bcrypt

class AuthService:
    def __init__(self, user_repository, bcrypt):
        self.user_repository = user_repository
        self.bcrypt = bcrypt

    def register(self, username, password, email, user_type='customer'):
        user_data = User(username, password, email,user_type).to_dict()
        return self.user_repository.save(user_data)

    def login(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user:
            if self.bcrypt.check_password_hash(user['password'], password):
                return user
        return None

