class User:
    def __init__(self, username, password, email, user_type='customer', user_id=None):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.user_type = user_type

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'user_type': self.user_type,
        }