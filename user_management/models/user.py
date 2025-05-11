class User:
    def __init__(self, username, password, email, user_type='customer', id=None):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.user_type = user_type

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'user_type': self.user_type,
        }