"""
岗位相关路由
"""
from flask import Blueprint, render_template, request, jsonify
from app.models.position import Position
from app.services.position_service import PositionService
from app.services.analysis_service import AnalysisService

positions_bp = Blueprint('positions', __name__, url_prefix='/positions')


@positions_bp.route('/')
def list_positions():
    """岗位列表页"""
    # 获取筛选参数（江苏版默认 2025 年）
    filters = {
        'year': request.args.get('year', 2025, type=int),
        'city': request.args.get('city', ''),
        'system_type': request.args.get('system_type', ''),
        'education': request.args.get('education', ''),
        'exam_category': request.args.get('exam_category', ''),
        'department_name': request.args.get('department_name', ''),
        'position_name': request.args.get('position_name', ''),
        'major': request.args.get('major', ''),
        'keyword': request.args.get('keyword', ''),
        'difficulty': request.args.get('difficulty', ''),
        'sort_by': request.args.get('sort_by', 'recommendation_score'),
        'sort_order': request.args.get('sort_order', 'desc')
    }
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 搜索岗位
    positions, total = PositionService.search_positions(filters, page, per_page)
    
    # 获取筛选选项
    cities = Position.get_cities()
    system_types = Position.get_system_types()
    
    # 统计数据
    stats = PositionService.get_statistics()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('positions/list.html',
                         positions=positions,
                         filters=filters,
                         cities=cities,
                         system_types=system_types,
                         stats=stats,
                         page=page,
                         per_page=per_page,
                         total=total,
                         total_pages=total_pages)


@positions_bp.route('/<int:position_id>')
def position_detail(position_id):
    """岗位详情页"""
    position = PositionService.get_position_detail(position_id)
    
    # TODO: 从session获取用户画像
    user_profile = {
        'education': '本科',
        'major': '计算机科学与技术',
        'estimated_score': 135,
        'preferred_cities': [position.city] if position.city else []
    }
    
    # 分析岗位
    analysis = AnalysisService.analyze_position_for_user(position, user_profile)
    
    # 相似岗位
    similar_positions = Position.query.filter(
        Position.city == position.city,
        Position.id != position.id
    ).limit(5).all()
    
    return render_template('positions/detail.html',
                         position=position,
                         analysis=analysis,
                         similar_positions=similar_positions)


@positions_bp.route('/dashboard')
def dashboard():
    """数据仪表盘"""
    year = request.args.get('year', 2025, type=int)
    city = request.args.get('city', '')
    
    # 统计数据
    stats = PositionService.get_statistics()
    city_stats = PositionService.get_city_statistics()
    education_stats = PositionService.get_education_statistics()
    exam_stats = PositionService.get_exam_category_statistics()
    
    return render_template('positions/dashboard.html',
                         year=year,
                         city=city,
                         stats=stats,
                         city_stats=city_stats,
                         education_stats=education_stats,
                         exam_stats=exam_stats)
