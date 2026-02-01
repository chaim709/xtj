# -*- coding: utf-8 -*-
"""
学员端API路由
供小程序调用的学员相关接口
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, jsonify, request, g
from sqlalchemy import and_
from app import db
from app.models.student import Student
from app.models.course import Schedule, CourseRecording, StudentBatch, ClassBatch
from app.routes.wx_api import require_student_auth

student_api_bp = Blueprint('student_api', __name__, url_prefix='/api/v1/students')


@student_api_bp.route('/me', methods=['GET'])
@require_student_auth
def get_current_student():
    """
    获取当前登录学员信息
    
    Returns:
        学员基本信息、班次信息、打卡统计
    """
    student = g.student
    
    # 获取打卡统计
    checkin_stats = {
        'totalDays': getattr(student, 'total_checkin_days', 0) or 0,
        'consecutiveDays': getattr(student, 'consecutive_checkin_days', 0) or 0,
        'todayChecked': False
    }
    
    # 检查今日是否打卡
    last_checkin = getattr(student, 'last_checkin_date', None)
    if last_checkin and last_checkin == date.today():
        checkin_stats['todayChecked'] = True
    
    # 获取班次信息
    current_batch = None
    student_batch = StudentBatch.query.filter_by(
        student_id=student.id,
        status='active'
    ).first()
    
    if student_batch and student_batch.batch:
        batch = student_batch.batch
        current_batch = {
            'id': batch.id,
            'name': batch.name,
            'status': batch.status,
            'progressDay': student_batch.progress_day
        }
    
    return jsonify({
        'success': True,
        'data': {
            'id': student.id,
            'name': student.name,
            'phone': student.phone[:3] + '****' + student.phone[-4:] if student.phone else '',
            'className': student.class_name,
            'examType': student.exam_type,
            'targetPosition': student.target_position,
            'status': student.status,
            'currentBatch': current_batch,
            'checkinStats': checkin_stats
        }
    })


@student_api_bp.route('/me/schedule', methods=['GET'])
@require_student_auth
def get_my_schedule():
    """
    获取我的课表
    
    Query Params:
        date: 指定日期 (YYYY-MM-DD)，默认今天
        week: 获取整周 (true/false)，默认false
    
    Returns:
        课表列表
    """
    student = g.student
    
    # 获取学员当前班次
    student_batch = StudentBatch.query.filter_by(
        student_id=student.id,
        status='active'
    ).first()
    
    if not student_batch:
        return jsonify({
            'success': True,
            'data': {
                'schedules': [],
                'message': '暂无课程安排'
            }
        })
    
    batch_id = student_batch.batch_id
    
    # 解析日期参数
    date_str = request.args.get('date', date.today().isoformat())
    is_week = request.args.get('week', 'false').lower() == 'true'
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()
    
    # 构建查询
    query = Schedule.query.filter_by(batch_id=batch_id)
    
    if is_week:
        # 获取本周一到周日
        monday = target_date - timedelta(days=target_date.weekday())
        sunday = monday + timedelta(days=6)
        query = query.filter(
            Schedule.schedule_date >= monday,
            Schedule.schedule_date <= sunday
        )
    else:
        query = query.filter(Schedule.schedule_date == target_date)
    
    schedules = query.order_by(Schedule.schedule_date, Schedule.day_number).all()
    
    result = []
    for s in schedules:
        result.append({
            'id': s.id,
            'date': s.schedule_date.isoformat() if s.schedule_date else None,
            'dayNumber': s.day_number,
            'subjectName': s.subject.name if s.subject else '',
            'morningTeacher': s.morning_teacher.name if s.morning_teacher else '',
            'afternoonTeacher': s.afternoon_teacher.name if s.afternoon_teacher else '',
            'eveningType': s.evening_type_display,
            'eveningTeacher': s.evening_teacher.name if s.evening_teacher else '',
            'remark': s.remark
        })
    
    return jsonify({
        'success': True,
        'data': {
            'date': date_str,
            'isWeek': is_week,
            'schedules': result
        }
    })


@student_api_bp.route('/me/recordings', methods=['GET'])
@require_student_auth
def get_my_recordings():
    """
    获取我的录播课列表
    
    Query Params:
        page: 页码，默认1
        limit: 每页数量，默认20
        subject_id: 科目筛选
    
    Returns:
        录播课列表（分页）
    """
    student = g.student
    
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 50)
    subject_id = request.args.get('subject_id', type=int)
    
    # 获取学员班次
    student_batch = StudentBatch.query.filter_by(
        student_id=student.id,
        status='active'
    ).first()
    
    if not student_batch:
        return jsonify({
            'success': True,
            'data': {
                'total': 0,
                'items': []
            }
        })
    
    # 查询录播课
    query = CourseRecording.query.filter_by(batch_id=student_batch.batch_id)
    
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    # 分页
    pagination = query.order_by(
        CourseRecording.recording_date.desc()
    ).paginate(page=page, per_page=limit, error_out=False)
    
    items = []
    for r in pagination.items:
        items.append({
            'id': r.id,
            'title': r.title,
            'recordingDate': r.recording_date.isoformat() if r.recording_date else None,
            'period': r.period_display,
            'subjectName': r.subject.name if r.subject else '',
            'teacherName': r.teacher.name if r.teacher else '',
            'duration': r.duration_display,
            'recordingUrl': r.recording_url
        })
    
    return jsonify({
        'success': True,
        'data': {
            'total': pagination.total,
            'page': page,
            'limit': limit,
            'items': items
        }
    })


@student_api_bp.route('/me/messages', methods=['GET'])
@require_student_auth
def get_my_messages():
    """
    获取我的督学消息
    
    Query Params:
        page: 页码，默认1
        limit: 每页数量，默认20
        is_read: 筛选已读/未读
    
    Returns:
        消息列表
    """
    from app.models.supervision import SupervisionLog
    
    student = g.student
    
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 50)
    
    # 查询督学记录作为消息
    query = SupervisionLog.query.filter_by(student_id=student.id)
    
    # 分页
    pagination = query.order_by(
        SupervisionLog.log_date.desc(),
        SupervisionLog.created_at.desc()
    ).paginate(page=page, per_page=limit, error_out=False)
    
    items = []
    for log in pagination.items:
        items.append({
            'id': log.id,
            'type': 'supervision',
            'title': '督学老师给您留言',
            'content': log.content[:100] + '...' if log.content and len(log.content) > 100 else log.content,
            'fullContent': log.content,
            'supervisorName': log.supervisor.username if log.supervisor else '督学老师',
            'mood': log.student_mood,
            'studyStatus': log.study_status,
            'createdAt': log.created_at.isoformat() if log.created_at else None,
            'logDate': log.log_date.isoformat() if log.log_date else None
        })
    
    return jsonify({
        'success': True,
        'data': {
            'total': pagination.total,
            'unreadCount': 0,  # TODO: 实现已读未读
            'page': page,
            'limit': limit,
            'items': items
        }
    })


@student_api_bp.route('/me/checkin', methods=['POST'])
@require_student_auth
def do_checkin():
    """
    每日打卡
    
    Request Body:
        studyMinutes: 学习时长（分钟）
        note: 打卡备注
    
    Returns:
        打卡结果、连续天数、累计天数
    """
    student = g.student
    data = request.get_json() or {}
    
    today = date.today()
    
    # 检查今日是否已打卡
    last_checkin = getattr(student, 'last_checkin_date', None)
    if last_checkin and last_checkin == today:
        return jsonify({
            'success': False,
            'message': '今日已打卡',
            'error_code': 'ALREADY_CHECKED_IN'
        }), 400
    
    try:
        # 计算连续打卡
        consecutive_days = getattr(student, 'consecutive_checkin_days', 0) or 0
        total_days = getattr(student, 'total_checkin_days', 0) or 0
        
        if last_checkin and last_checkin == today - timedelta(days=1):
            # 连续打卡
            consecutive_days += 1
        else:
            # 断签，重新计算
            consecutive_days = 1
        
        total_days += 1
        
        # 更新学员记录
        student.last_checkin_date = today
        student.consecutive_checkin_days = consecutive_days
        student.total_checkin_days = total_days
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'打卡成功！连续打卡{consecutive_days}天',
            'data': {
                'consecutiveDays': consecutive_days,
                'totalDays': total_days,
                'todayChecked': True
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '打卡失败，请重试',
            'error_code': 'CHECKIN_FAILED'
        }), 500


@student_api_bp.route('/me/homework', methods=['GET'])
@require_student_auth
def get_my_homework():
    """
    获取我的作业列表
    
    Returns:
        作业列表
    """
    from app.models.homework import HomeworkTask, HomeworkSubmission
    import json
    
    student = g.student
    
    # 查询分配给该学员的作业
    tasks = HomeworkTask.query.filter(
        HomeworkTask.status == 'published'
    ).order_by(HomeworkTask.deadline.desc()).limit(20).all()
    
    items = []
    for task in tasks:
        # 检查是否分配给该学员
        target_students = []
        if task.target_students:
            try:
                target_students = json.loads(task.target_students)
            except:
                pass
        
        # 如果没有指定目标学员，则所有人可见；否则检查是否在目标列表中
        if target_students and student.id not in target_students:
            continue
        
        # 检查是否已提交
        submission = HomeworkSubmission.query.filter_by(
            task_id=task.id,
            student_id=student.id
        ).first()
        
        items.append({
            'id': task.id,
            'title': task.task_name,
            'description': task.description,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'status': 'completed' if submission else 'pending',
            'submitTime': submission.submit_time.isoformat() if submission and submission.submit_time else None,
            'accuracyRate': submission.accuracy_rate if submission else None
        })
    
    return jsonify({
        'success': True,
        'data': {
            'items': items
        }
    })
