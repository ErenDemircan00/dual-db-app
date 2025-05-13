from setuptools import setup, find_packages

setup(
    name="dual-db-app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-mysqldb',
        'flask-bcrypt',
        'pymongo',
        'python-dotenv',
        'flask-mail',
        'PyJWT',
        'selenium',
        'webdriver-manager',
    ],
) 