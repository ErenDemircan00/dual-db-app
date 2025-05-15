import unittest
import sys
from pathlib import Path

# Flask uygulamasını import et
sys.path.append(str(Path(__file__).parent.parent))
from app import app

class TestFlaskApp(unittest.TestCase):
    def test_app_exists(self):
        """Test if the app instance exists"""
        self.assertIsNotNone(app)
        
    def test_app_is_flask_app(self):
        """Test if app is a Flask app"""
        from flask import Flask
        self.assertIsInstance(app, Flask)

if __name__ == "__main__":
    unittest.main() 