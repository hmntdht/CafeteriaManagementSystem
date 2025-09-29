import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Config:
    SECRET_KEY = "C13F578AAC81D41D8FA5C4B95BBE5" 
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/CafeteriaManagementSystem"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Mail configuration
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "nasteat31@gmail.com"
    MAIL_PASSWORD = "clkbveitxmrpqihg"
    MAIL_DEFAULT_SENDER = "nasteat31@gmail.com"
