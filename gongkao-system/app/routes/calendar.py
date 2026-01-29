"""
课程日历路由 - 第三阶段新增
提供日历视图展示课程安排
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from datetime import datetime, date

calendar_bp = Blueprint('calendar', __name__)


@calendar_bp.route('/yearly')
@login_required
def yearly_plan():
    """
    全年排课计划页面
    
    Returns:
        渲染全年排课计划页面
    """
    year = request.args.get('year', date.today().year, type=int)
    return render_template('calendar/yearly.html', year=year)


@calendar_bp.route('/api/yearly/heatmap')
@login_required
def get_yearly_heatmap():
    """
    获取全年热力图数据
    
    Query Params:
        year: 年份
    
    Returns:
        JSON: 热力图数据
    """
    from app.services.calendar_service import CalendarService
    
    year = request.args.get('year', date.today().year, type=int)
    data = CalendarService.get_yearly_heatmap_data(year)
    
    return jsonify({
        'success': True,
        'data': data
    })


@calendar_bp.route('/api/yearly/monthly-stats')
@login_required
def get_yearly_monthly_stats():
    """
    获取按月统计数据
    
    Query Params:
        year: 年份
    
    Returns:
        JSON: 月度统计数据
    """
    from app.services.calendar_service import CalendarService
    
    year = request.args.get('year', date.today().year, type=int)
    stats = CalendarService.get_yearly_monthly_stats(year)
    
    return jsonify({
        'success': True,
        'data': stats
    })


@calendar_bp.route('/api/yearly/batch-timeline')
@login_required
def get_yearly_batch_timeline():
    """
    获取班次时间线数据
    
    Query Params:
        year: 年份
    
    Returns:
        JSON: 班次时间线数据
    """
    from app.services.calendar_service import CalendarService
    
    year = request.args.get('year', date.today().year, type=int)
    timeline = CalendarService.get_yearly_batch_timeline(year)
    
    return jsonify({
        'success': True,
        'data': timeline
    })


@calendar_bp.route('/api/yearly/subject-distribution')
@login_required
def get_yearly_subject_distribution():
    """
    获取科目分布统计
    
    Query Params:
        year: 年份
    
    Returns:
        JSON: 科目分布数据
    """
    from app.services.calendar_service import CalendarService
    
    year = request.args.get('year', date.today().year, type=int)
    distribution = CalendarService.get_yearly_subject_distribution(year)
    
    return jsonify({
        'success': True,
        'data': distribution
    })


@calendar_bp.route('/')
@login_required
def index():
    """
    日历主页面
    
    Returns:
        渲染日历页面
    """
    return render_template('calendar/index.html')


@calendar_bp.route('/api/events')
@login_required
def get_events():
    """
    获取日历事件（FullCalendar格式）
    
    Query Params:
        start: 开始日期 (YYYY-MM-DD)
        end: 结束日期 (YYYY-MM-DD)
        batch_id: 班次ID（可选）
        teacher_id: 老师ID（可选）
        subject_id: 科目ID（可选）
    
    Returns:
        JSON: FullCalendar事件列表
    """
    from app.services.calendar_service import CalendarService
    
    start_str = request.args.get('start', '')
    end_str = request.args.get('end', '')
    batch_id = request.args.get('batch_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    
    # 解析日期
    try:
        start_date = datetime.strptime(start_str[:10], '%Y-%m-%d').date() if start_str else date.today().replace(day=1)
        end_date = datetime.strptime(end_str[:10], '%Y-%m-%d').date() if end_str else date.today()
    except ValueError:
        start_date = date.today().replace(day=1)
        end_date = date.today()
    
    events = CalendarService.get_calendar_events(
        start_date=start_date,
        end_date=end_date,
        batch_id=batch_id,
        teacher_id=teacher_id,
        subject_id=subject_id
    )
    
    return jsonify(events)


@calendar_bp.route('/api/day-detail/<date_str>')
@login_required
def get_day_detail(date_str):
    """
    获取指定日期的课程详情
    
    Args:
        date_str: 日期字符串 (YYYY-MM-DD)
    
    Returns:
        JSON: 当日课程详情列表
    """
    from app.services.calendar_service import CalendarService
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': '日期格式错误'}), 400
    
    schedules = CalendarService.get_day_schedules(target_date)
    
    return jsonify({
        'success': True,
        'date': date_str,
        'schedules': schedules
    })


@calendar_bp.route('/api/filters')
@login_required
def get_filters():
    """
    获取筛选选项（班次/老师/科目列表）
    
    Returns:
        JSON: 筛选选项
    """
    from app.models.course import ClassBatch, Subject
    from app.models.teacher import Teacher
    
    # 获取所有进行中和招生中的班次
    batches = ClassBatch.query.filter(
        ClassBatch.status.in_(['recruiting', 'ongoing'])
    ).order_by(ClassBatch.start_date.desc()).all()
    
    # 获取所有活跃老师
    teachers = Teacher.query.filter_by(status='active').order_by(Teacher.name).all()
    
    # 获取所有活跃科目
    subjects = Subject.query.filter_by(status='active').order_by(Subject.sort_order).all()
    
    return jsonify({
        'success': True,
        'batches': [{'id': b.id, 'name': b.name} for b in batches],
        'teachers': [{'id': t.id, 'name': t.name} for t in teachers],
        'subjects': [{'id': s.id, 'name': s.name} for s in subjects]
    })
