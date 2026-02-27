"""
配置文件 - 事业单位选岗系统
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

class Config:
    """基础配置"""
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'shiye-system-secret-key-2026')
    
    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100
    
    # 上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 静态文件
    STATIC_FOLDER = BASE_DIR / 'app' / 'static'
    TEMPLATE_FOLDER = BASE_DIR / 'app' / 'templates'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    
    # SQLite数据库
    DATABASE_PATH = PROJECT_ROOT / 'data' / 'database' / 'shiye_dev.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    
    # 数据文件路径
    DATA_DIR = PROJECT_ROOT / 'data'
    RAW_DATA_DIR = DATA_DIR / 'raw'
    PROCESSED_DATA_DIR = DATA_DIR / 'processed'
    
    # CSV文件路径
    POSITIONS_CSV = PROJECT_ROOT.parent / '安徽省事业单位' / '整合后总表_2026年安徽省事业单位岗位.csv'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # PostgreSQL数据库
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost/shiye_db'
    )
    
    # 数据目录
    DATA_DIR = Path('/var/data/shiye')
    RAW_DATA_DIR = DATA_DIR / 'raw'
    PROCESSED_DATA_DIR = DATA_DIR / 'processed'


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    
    # 测试数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
