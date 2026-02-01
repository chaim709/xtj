"""
配置文件 - 公考培训机构管理系统
"""
import os
from datetime import timedelta

# 获取项目根目录
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""
    # 安全密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-gongkao-2026'
    
    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login配置
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # 分页配置
    STUDENTS_PER_PAGE = 20
    LOGS_PER_PAGE = 10
    HOMEWORK_PER_PAGE = 10
    
    # 常用短语（督学日志）
    COMMON_PHRASES = [
        "今天情绪不错，学习积极",
        "作业完成良好，正确率有提升",
        "数量关系仍然薄弱，需要加强",
        "需要多鼓励，增强自信心",
        "学习态度认真，继续保持",
        "言语理解进步明显",
        "判断推理需要多练习",
        "资料分析计算速度需提升",
        "申论写作思路清晰",
        "常识积累需要加强",
    ]
    
    # 心态选项
    MOOD_OPTIONS = ['积极', '平稳', '焦虑', '低落']
    
    # 学习状态选项
    STATUS_OPTIONS = ['优秀', '良好', '一般', '较差']
    
    # 沟通方式选项
    CONTACT_OPTIONS = ['电话', '微信', '面谈']
    
    # 班次选项
    CLASS_OPTIONS = ['全程班', '暑假班', '冲刺班', '周末班']
    
    # 报考类型选项
    EXAM_TYPE_OPTIONS = ['2026年江苏国省考', '2026年江苏事业编', '2026年江苏国省考,2026年江苏事业编']
    
    # ============ 第三阶段新增配置 ============
    
    # API配置（供外部系统调用）
    API_KEY = os.environ.get('API_KEY') or 'default-api-key-change-in-production'
    API_KEY_HEADER = 'X-API-Key'
    API_RATE_LIMIT = 100  # 每分钟请求限制
    
    # 微信小程序配置
    WX_APPID = os.environ.get('WX_APPID', '')
    WX_SECRET = os.environ.get('WX_SECRET', '')
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_EXPIRES_DAYS = int(os.environ.get('JWT_EXPIRES_DAYS', 7))
    
    # 跟进提醒配置
    FOLLOW_UP_REMINDER_DAYS = 7  # 超过N天未跟进则提醒
    
    # 分析看板配置
    ANALYTICS_DEFAULT_DAYS = 30  # 默认统计天数
    ANALYTICS_TREND_DAYS = 30    # 趋势图默认天数
    ANALYTICS_RANKING_LIMIT = 10 # 排行榜显示数量


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data', 'dev.db')


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data', 'prod.db')


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
