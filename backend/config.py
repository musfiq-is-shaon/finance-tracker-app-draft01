import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MySQL Database Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '12345root')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'finance_tracker')
    
    # JWT Configuration
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = int(os.getenv('FLASK_DEBUG', 1))

