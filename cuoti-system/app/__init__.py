# -*- coding: utf-8 -*-
"""应用工厂"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'admin.login'


def create_app(config_name='default'):
    """创建应用实例"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    
    # 注册蓝图
    from app.routes.admin import admin_bp
    from app.routes.h5 import h5_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(h5_bp, url_prefix='/h5')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
