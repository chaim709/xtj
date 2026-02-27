"""
首页路由
"""
from flask import Blueprint, render_template
from app.models.position import Position
from app import db

index_bp = Blueprint('index', __name__)


@index_bp.route('/')
def home():
    """首页"""
    # 统计数据
    total_positions = Position.query.count()
    total_recruit = db.session.query(db.func.sum(Position.recruit_count)).scalar() or 0
    
    # 城市列表
    cities = Position.get_cities()
    
    # 热门岗位
    hot_positions = Position.query.order_by(
        Position.recommendation_score.desc().nullslast()
    ).limit(10).all()
    
    return render_template('index.html',
                         total_positions=total_positions,
                         total_recruit=total_recruit,
                         cities=cities,
                         hot_positions=hot_positions)
