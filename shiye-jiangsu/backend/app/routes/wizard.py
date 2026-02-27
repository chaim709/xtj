"""
智能选岗向导路由
"""
from flask import Blueprint, render_template, request, jsonify, session
from app.models.position import Position
from app.services.recommend_service import RecommendService
import json

wizard_bp = Blueprint('wizard', __name__, url_prefix='/wizard')


@wizard_bp.route('/')
def index():
    """选岗向导首页"""
    cities = Position.get_cities()
    
    return render_template('wizard/index.html', cities=cities)


@wizard_bp.route('/result')
def result():
    """选岗向导结果页"""
    # 获取用户输入
    user_profile = {
        'education': request.args.get('education', '本科'),
        'major': request.args.get('major', ''),
        'major_category': request.args.get('major_category', ''),
        'graduation_status': request.args.get('graduation_status', ''),
        'estimated_score': request.args.get('estimated_score', 130, type=int),
        'preferred_cities': request.args.getlist('cities'),
        'special_status': request.args.get('special_status', ''),
        'political_status': request.args.get('political_status', ''),
        'base_layer_willing': request.args.get('base_layer_willing') == 'on'
    }
    
    # 保存到session
    session['user_profile'] = user_profile
    
    # 获取推荐岗位
    recommendations = RecommendService.recommend_positions(user_profile, limit=20)
    
    return render_template('wizard/result.html',
                         user_profile=user_profile,
                         recommendations=recommendations)
