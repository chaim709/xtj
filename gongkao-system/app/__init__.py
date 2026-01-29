"""
Flask应用初始化 - 公考培训机构管理系统
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'


def create_app(config_name='default'):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称 (development/production/testing)
    
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # 导入模型（确保user_loader被注册）
    with app.app_context():
        from app.models import user  # noqa: F401
    
    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.supervision import supervision_bp
    from app.routes.homework import homework_bp
    from app.routes.courses import courses_bp  # 第二阶段新增
    # 第三阶段新增蓝图
    from app.routes.calendar import calendar_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api_v1 import api_v1_bp
    # 学习计划蓝图
    from app.routes.plans import plans_bp
    # 智能选岗蓝图（第四阶段）
    from app.routes.positions import positions_bp
    # 题库与错题蓝图（从cuoti-system合并）
    from app.routes.questions import questions_bp
    from app.routes.workbooks import workbooks_bp
    from app.routes.h5 import h5_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(supervision_bp, url_prefix='/supervision')
    app.register_blueprint(homework_bp, url_prefix='/homework')
    app.register_blueprint(courses_bp, url_prefix='/courses')  # 第二阶段新增
    # 第三阶段新增蓝图注册
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    # 学习计划蓝图注册
    app.register_blueprint(plans_bp)
    # 智能选岗蓝图注册
    app.register_blueprint(positions_bp)
    # 题库与错题蓝图注册
    app.register_blueprint(questions_bp)
    app.register_blueprint(workbooks_bp)
    app.register_blueprint(h5_bp)
    app.register_blueprint(admin_bp)
    
    # 根路由重定向到工作台
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('dashboard.index'))
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        from flask import render_template
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    # 注册CLI命令
    from app.migrate.commands import init_app as init_migrate_commands
    init_migrate_commands(app)
    
    # 上下文处理器 - 注入全局变量
    @app.context_processor
    def inject_config():
        return {
            'common_phrases': app.config.get('COMMON_PHRASES', []),
            'mood_options': app.config.get('MOOD_OPTIONS', []),
            'status_options': app.config.get('STATUS_OPTIONS', []),
            'contact_options': app.config.get('CONTACT_OPTIONS', []),
            'class_options': app.config.get('CLASS_OPTIONS', []),
            'exam_type_options': app.config.get('EXAM_TYPE_OPTIONS', []),
        }
    
    return app
