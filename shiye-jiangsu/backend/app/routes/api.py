"""
API路由
"""
from flask import Blueprint, jsonify, request
from app.models.position import Position
from app.services.position_service import PositionService
from app.services.analysis_service import AnalysisService

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/cities')
def get_cities():
    """获取城市列表（江苏版默认 2025 年）"""
    year = request.args.get('year', 2025, type=int)
    cities = Position.get_cities(year=year)
    return jsonify({'cities': cities})


@api_bp.route('/statistics/overview')
def get_overview_stats():
    """获取概览统计"""
    stats = PositionService.get_statistics()
    return jsonify(stats)


@api_bp.route('/statistics/cities')
def get_city_stats():
    """获取城市统计"""
    stats = PositionService.get_city_statistics()
    return jsonify({'data': stats})


@api_bp.route('/statistics/education')
def get_education_stats():
    """获取学历统计"""
    stats = PositionService.get_education_statistics()
    return jsonify({'data': stats})


@api_bp.route('/statistics/exam-categories')
def get_exam_category_stats():
    """获取考试类别统计"""
    stats = PositionService.get_exam_category_statistics()
    return jsonify({'data': stats})


@api_bp.route('/city-comparison')
def get_city_comparison():
    """获取城市对比数据"""
    data = AnalysisService.get_city_comparison_data()
    return jsonify({'data': data})
