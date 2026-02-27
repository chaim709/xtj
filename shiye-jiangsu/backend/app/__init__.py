"""
Flask应用工厂 - 事业单位选岗系统
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# 扩展实例
db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='default'):
    """
    创建Flask应用实例
    
    Args:
        config_name: 配置名称 (development/production/testing)
    
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 设置JSON编码为UTF-8
    app.config['JSON_AS_ASCII'] = False
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 创建数据目录
    os.makedirs(app.config.get('DATA_DIR', 'data'), exist_ok=True)
    os.makedirs(app.config.get('RAW_DATA_DIR', 'data/raw'), exist_ok=True)
    os.makedirs(app.config.get('PROCESSED_DATA_DIR', 'data/processed'), exist_ok=True)
    
    # 创建数据库目录
    db_dir = app.config.get('DATABASE_PATH')
    if db_dir:
        os.makedirs(os.path.dirname(db_dir), exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'index.home'
    login_manager.login_message = '请先登录'
    
    # 配置user_loader（暂时返回None，V1.1实现用户系统）
    @login_manager.user_loader
    def load_user(user_id):
        return None
    
    # 注册蓝图
    with app.app_context():
        # 导入并注册路由
        from app.routes.index import index_bp
        from app.routes.positions import positions_bp
        from app.routes.wizard import wizard_bp
        from app.routes.api import api_bp
        from app.routes.evaluation import evaluation_bp
        from app.routes.comparison import comparison_bp
        from app.routes.policy import policy_bp
        from app.routes.exam import exam_bp
        
        app.register_blueprint(index_bp)
        app.register_blueprint(positions_bp)
        app.register_blueprint(wizard_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(evaluation_bp)
        app.register_blueprint(comparison_bp)
        app.register_blueprint(policy_bp)
        app.register_blueprint(exam_bp)
        
        # 创建数据库表
        db.create_all()
    
    return app
