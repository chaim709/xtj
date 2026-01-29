# -*- coding: utf-8 -*-
"""配置文件"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cuoti-system-secret-key-2026'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 每页题目数量（生成PDF时）
    QUESTIONS_PER_PAGE = 5
    
    # 二维码基础URL（部署时需要修改）
    BASE_URL = os.environ.get('BASE_URL') or 'https://xtxtj.chaim.top'
    
    # 上传文件目录
    UPLOAD_FOLDER = os.path.join(basedir, 'data', 'uploads')
    
    # 生成文件目录
    OUTPUT_FOLDER = os.path.join(basedir, 'data', 'output')
    
    # 督学系统数据库（用于同步学员）
    DUXUE_DB_PATH = os.path.join(os.path.dirname(basedir), 'gongkao-system', 'data', 'dev.db')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'cuoti_dev.db')


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'cuoti.db')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
