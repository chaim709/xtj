"""
路由模块 - 事业单位选岗系统
"""
from app.routes.index import index_bp
from app.routes.positions import positions_bp
from app.routes.wizard import wizard_bp
from app.routes.api import api_bp
from app.routes.evaluation import evaluation_bp
from app.routes.comparison import comparison_bp

__all__ = ['index_bp', 'positions_bp', 'wizard_bp', 'api_bp', 'evaluation_bp', 'comparison_bp']
