"""
数据分析路由 - 第三阶段新增
提供数据统计和可视化看板
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/')
@login_required
def index():
    """
    数据分析看板主页面
    
    Returns:
        渲染分析看板页面
    """
    return render_template('analytics/index.html')


@analytics_bp.route('/api/overview')
@login_required
def get_overview():
    """
    获取概览统计（卡片数据）
    
    Query Params:
        days: 统计天数（默认30）
    
    Returns:
        JSON: 统计卡片数据
    """
    from app.services.analytics_service import AnalyticsService
    
    days = request.args.get('days', 30, type=int)
    stats = AnalyticsService.get_overview_stats(days)
    
    return jsonify({
        'success': True,
        'data': stats
    })


@analytics_bp.route('/api/student-trend')
@login_required
def get_student_trend():
    """
    获取学员增长趋势
    
    Query Params:
        days: 统计天数（默认30）
    
    Returns:
        JSON: 日期和数量数组
    """
    from app.services.analytics_service import AnalyticsService
    
    days = request.args.get('days', 30, type=int)
    trend = AnalyticsService.get_student_trend(days)
    
    return jsonify({
        'success': True,
        'data': trend
    })


@analytics_bp.route('/api/student-status')
@login_required
def get_student_status():
    """
    获取学员状态分布
    
    Returns:
        JSON: 饼图数据
    """
    from app.services.analytics_service import AnalyticsService
    
    distribution = AnalyticsService.get_student_status_distribution()
    
    return jsonify({
        'success': True,
        'data': distribution
    })


@analytics_bp.route('/api/supervision-ranking')
@login_required
def get_supervision_ranking():
    """
    获取督学工作量排行
    
    Query Params:
        days: 统计天数（默认30）
        limit: 返回数量（默认10）
    
    Returns:
        JSON: 柱状图数据
    """
    from app.services.analytics_service import AnalyticsService
    
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 10, type=int)
    ranking = AnalyticsService.get_supervision_ranking(days, limit)
    
    return jsonify({
        'success': True,
        'data': ranking
    })


@analytics_bp.route('/api/weakness-distribution')
@login_required
def get_weakness_distribution():
    """
    获取薄弱知识点分布（Top N）
    
    Query Params:
        limit: 返回数量（默认10）
    
    Returns:
        JSON: 柱状图数据
    """
    from app.services.analytics_service import AnalyticsService
    
    limit = request.args.get('limit', 10, type=int)
    distribution = AnalyticsService.get_weakness_distribution(limit)
    
    return jsonify({
        'success': True,
        'data': distribution
    })


@analytics_bp.route('/api/batch-progress')
@login_required
def get_batch_progress():
    """
    获取班次课程进度
    
    Returns:
        JSON: 进度数据
    """
    from app.services.analytics_service import AnalyticsService
    
    progress = AnalyticsService.get_batch_progress()
    
    return jsonify({
        'success': True,
        'data': progress
    })


@analytics_bp.route('/api/attendance-stats')
@login_required
def get_attendance_stats():
    """
    获取考勤统计
    
    Query Params:
        batch_id: 班次ID（可选）
    
    Returns:
        JSON: 考勤统计数据
    """
    from app.services.analytics_service import AnalyticsService
    
    batch_id = request.args.get('batch_id', type=int)
    stats = AnalyticsService.get_attendance_summary(batch_id)
    
    return jsonify({
        'success': True,
        'data': stats
    })
