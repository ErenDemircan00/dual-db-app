import os
from flask_mail import Message

class MailServices:
    def __init__(self, user_repository, mail):
        self.user_repository = user_repository
        self.mail = mail

    def send_reset_password_email(self, email, token):
        pass
