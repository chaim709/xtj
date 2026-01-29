"""
开放API路由 - 第三阶段新增
提供RESTful API供外部系统调用（如题库系统、扣子智能体）
"""
from functools import wraps
from flask import Blueprint, jsonify, request, current_app
from app import db

api_v1_bp = Blueprint('api_v1', __name__)


def require_api_key(f):
    """
    API Key验证装饰器
    
    从请求头X-API-Key读取API Key并验证
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = current_app.config.get('API_KEY')
        
        if not api_key:
            return jsonify({
                'success': False,
                'message': '缺少API Key',
                'error_code': 'MISSING_API_KEY'
            }), 401
        
        if api_key != expected_key:
            return jsonify({
                'success': False,
                'message': '无效的API Key',
                'error_code': 'INVALID_API_KEY'
            }), 401
        
        return f(*args, **kwargs)
    return decorated


def api_response(data=None, message='操作成功', pagination=None):
    """
    统一API响应格式
    
    Args:
        data: 响应数据
        message: 响应消息
        pagination: 分页信息
    
    Returns:
        JSON响应
    """
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    if pagination:
        response['pagination'] = pagination
    return jsonify(response)


def api_error(message, error_code, status_code=400):
    """
    统一API错误响应
    
    Args:
        message: 错误消息
        error_code: 错误代码
        status_code: HTTP状态码
    
    Returns:
        JSON错误响应
    """
    return jsonify({
        'success': False,
        'message': message,
        'error_code': error_code
    }), status_code


# ============ 学员接口 ============

@api_v1_bp.route('/students')
@require_api_key
def list_students():
    """
    获取学员列表
    
    Query Params:
        page: 页码（默认1）
        per_page: 每页数量（默认20，最大100）
        status: 状态筛选
        batch_id: 班次ID筛选
    
    Returns:
        JSON: 学员列表+分页信息
    """
    from app.models.student import Student
    from app.models.course import StudentBatch
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    batch_id = request.args.get('batch_id', type=int)
    
    query = Student.query
    
    if status:
        query = query.filter_by(status=status)
    
    if batch_id:
        query = query.join(StudentBatch).filter(StudentBatch.batch_id == batch_id)
    
    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    students = [{
        'id': s.id,
        'name': s.name,
        'phone': s.phone,
        'status': s.status,
        'exam_type': s.exam_type,
        'class_name': s.class_name,
        'need_attention': s.need_attention,
        'created_at': s.created_at.isoformat() if s.created_at else None
    } for s in pagination.items]
    
    return api_response(
        data=students,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    )


@api_v1_bp.route('/students/<int:id>')
@require_api_key
def get_student(id):
    """
    获取单个学员详情
    
    Args:
        id: 学员ID
    
    Returns:
        JSON: 学员详情
    """
    from app.models.student import Student
    
    student = Student.query.get(id)
    if not student:
        return api_error('学员不存在', 'NOT_FOUND', 404)
    
    # 获取薄弱项标签
    tags = [{
        'id': t.id,
        'module': t.module,
        'submodule': t.sub_module,
        'accuracy': t.accuracy_rate
    } for t in student.weakness_tags]
    
    data = {
        'id': student.id,
        'name': student.name,
        'phone': student.phone,
        'wechat': student.wechat,
        'status': student.status,
        'exam_type': student.exam_type,
        'class_name': student.class_name,
        'target_position': student.target_position,
        'has_basic': student.has_basic,
        'is_agreement': student.is_agreement,
        'base_level': student.base_level,
        'need_attention': student.need_attention,
        'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
        'created_at': student.created_at.isoformat() if student.created_at else None,
        'weakness_tags': tags
    }
    
    return api_response(data=data)


# ============ 班次接口 ============

@api_v1_bp.route('/batches')
@require_api_key
def list_batches():
    """
    获取班次列表
    
    Query Params:
        status: 状态筛选（recruiting/ongoing/ended）
        project_id: 项目ID筛选
    
    Returns:
        JSON: 班次列表
    """
    from app.models.course import ClassBatch, ClassType
    
    status = request.args.get('status')
    project_id = request.args.get('project_id', type=int)
    
    query = ClassBatch.query
    
    if status:
        query = query.filter_by(status=status)
    
    if project_id:
        query = query.join(ClassType).filter(ClassType.project_id == project_id)
    
    batches = query.order_by(ClassBatch.start_date.desc()).all()
    
    data = [{
        'id': b.id,
        'name': b.name,
        'batch_number': b.batch_number,
        'status': b.status,
        'start_date': b.start_date.isoformat() if b.start_date else None,
        'end_date': b.end_date.isoformat() if b.end_date else None,
        'max_students': b.max_students,
        'enrolled_count': b.enrolled_count,
        'class_type_name': b.class_type.name if b.class_type else None
    } for b in batches]
    
    return api_response(data=data)


@api_v1_bp.route('/batches/<int:id>')
@require_api_key
def get_batch(id):
    """
    获取单个班次详情
    
    Args:
        id: 班次ID
    
    Returns:
        JSON: 班次详情
    """
    from app.models.course import ClassBatch
    
    batch = ClassBatch.query.get(id)
    if not batch:
        return api_error('班次不存在', 'NOT_FOUND', 404)
    
    data = {
        'id': batch.id,
        'name': batch.name,
        'batch_number': batch.batch_number,
        'status': batch.status,
        'start_date': batch.start_date.isoformat() if batch.start_date else None,
        'end_date': batch.end_date.isoformat() if batch.end_date else None,
        'actual_days': batch.actual_days,
        'max_students': batch.max_students,
        'enrolled_count': batch.enrolled_count,
        'classroom': batch.classroom,
        'class_type': {
            'id': batch.class_type.id,
            'name': batch.class_type.name
        } if batch.class_type else None
    }
    
    return api_response(data=data)


@api_v1_bp.route('/batches/<int:id>/students')
@require_api_key
def get_batch_students(id):
    """
    获取班次学员列表
    
    Args:
        id: 班次ID
    
    Returns:
        JSON: 学员列表
    """
    from app.models.course import ClassBatch, StudentBatch
    
    batch = ClassBatch.query.get(id)
    if not batch:
        return api_error('班次不存在', 'NOT_FOUND', 404)
    
    student_batches = StudentBatch.query.filter_by(
        batch_id=id,
        status='active'
    ).all()
    
    students = [{
        'id': sb.student.id,
        'name': sb.student.name,
        'phone': sb.student.phone,
        'enroll_time': sb.enroll_time.isoformat() if sb.enroll_time else None,
        'progress_day': sb.progress_day
    } for sb in student_batches if sb.student]
    
    return api_response(data=students)


# ============ 扣子智能督学接口 ============

@api_v1_bp.route('/students/search')
@require_api_key
def search_students():
    """
    学员智能搜索（供扣子调用）
    
    支持模糊搜索学员，返回匹配结果及相关信息
    
    Query Params:
        query: 搜索关键词（学员姓名/手机号）
        include_logs: 是否包含最近督学记录（默认false）
        include_homework: 是否包含作业完成情况（默认false）
        limit: 返回数量限制（默认5）
    
    Returns:
        JSON: 匹配的学员列表
    """
    from app.models.student import Student
    from app.models.supervision import SupervisionLog
    from app.models.homework import HomeworkSubmission
    
    query = request.args.get('query', '').strip()
    include_logs = request.args.get('include_logs', 'false').lower() == 'true'
    include_homework = request.args.get('include_homework', 'false').lower() == 'true'
    limit = min(request.args.get('limit', 5, type=int), 20)
    
    if not query:
        return api_error('请提供搜索关键词', 'MISSING_QUERY', 400)
    
    # 模糊搜索：按姓名或手机号
    students = Student.query.filter(
        db.or_(
            Student.name.ilike(f'%{query}%'),
            Student.phone.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    results = []
    for s in students:
        student_data = {
            'id': s.id,
            'name': s.name,
            'phone': s.phone,
            'class_name': s.class_name,
            'status': s.status,
            'exam_type': s.exam_type,
            'need_attention': s.need_attention,
            'is_agreement': s.is_agreement
        }
        
        # 获取最近督学记录
        if include_logs:
            recent_logs = SupervisionLog.query.filter_by(
                student_id=s.id
            ).order_by(SupervisionLog.log_date.desc()).limit(3).all()
            
            student_data['recent_logs'] = [{
                'id': log.id,
                'log_date': log.log_date.isoformat() if log.log_date else None,
                'content': log.content[:100] + '...' if log.content and len(log.content) > 100 else log.content,
                'student_mood': log.student_mood,
                'study_status': log.study_status
            } for log in recent_logs]
        
        # 获取作业完成情况
        if include_homework:
            recent_submissions = HomeworkSubmission.query.filter_by(
                student_id=s.id
            ).order_by(HomeworkSubmission.submit_time.desc()).limit(3).all()
            
            student_data['recent_homework'] = [{
                'task_name': sub.task.task_name if sub.task else None,
                'accuracy_rate': sub.accuracy_rate,
                'submit_time': sub.submit_time.isoformat() if sub.submit_time else None
            } for sub in recent_submissions]
        
        results.append(student_data)
    
    return api_response(
        data=results,
        message=f'找到 {len(results)} 个匹配的学员'
    )


@api_v1_bp.route('/supervision/logs', methods=['POST'])
@require_api_key
def create_supervision_log():
    """
    创建督学记录（供扣子语音录入调用）
    
    支持通过学员姓名智能匹配学员ID
    
    Request Body:
        student_name: 学员姓名（用于智能匹配）
        student_id: 学员ID（可选，优先使用）
        content: 督学内容
        mood: 学员情绪（积极/平稳/焦虑/低落）
        study_status: 学习状态（优秀/良好/一般/较差）
        contact_type: 沟通方式（电话/微信/面谈）
        next_action: 后续计划
        next_follow_up_date: 下次跟进时间
    
    Returns:
        JSON: 创建结果
    """
    from app.models.student import Student
    from app.models.supervision import SupervisionLog
    from datetime import date
    
    # 同时支持 JSON body 和 query string 参数（兼容扣子平台）
    data = request.get_json(silent=True) or {}
    
    # 如果 JSON body 为空，从 query string 获取参数
    if not data:
        data = {
            'student_name': request.args.get('student_name', ''),
            'student_id': request.args.get('student_id'),
            'content': request.args.get('content', ''),
            'mood': request.args.get('mood'),
            'study_status': request.args.get('study_status'),
            'contact_type': request.args.get('contact_type'),
            'next_action': request.args.get('next_action'),
            'next_follow_up_date': request.args.get('next_follow_up_date')
        }
    
    # 获取学员ID
    student_id = data.get('student_id')
    student_name = data.get('student_name', '').strip() if data.get('student_name') else ''
    
    if not student_id and not student_name:
        return api_error('请提供学员ID或姓名', 'MISSING_STUDENT', 400)
    
    # 如果没有ID，通过姓名匹配
    if not student_id:
        # 精确匹配优先
        student = Student.query.filter_by(name=student_name).first()
        
        # 如果没有精确匹配，尝试模糊匹配
        if not student:
            students = Student.query.filter(
                Student.name.ilike(f'%{student_name}%')
            ).all()
            
            if len(students) == 0:
                return api_error(f'未找到名为"{student_name}"的学员', 'STUDENT_NOT_FOUND', 404)
            elif len(students) > 1:
                # 返回多个匹配结果让用户选择
                matches = [{'id': s.id, 'name': s.name, 'class_name': s.class_name} for s in students[:5]]
                return api_response(
                    data={'matches': matches, 'need_confirm': True},
                    message=f'找到{len(students)}个匹配的学员，请确认'
                )
            else:
                student = students[0]
        
        student_id = student.id
    else:
        student = Student.query.get(student_id)
        if not student:
            return api_error('学员不存在', 'STUDENT_NOT_FOUND', 404)
    
    # 创建督学记录
    try:
        log = SupervisionLog(
            student_id=student_id,
            supervisor_id=1,  # 默认督学ID，扣子调用时可通过API Key关联
            content=data.get('content', ''),
            student_mood=data.get('mood') or data.get('student_mood'),
            study_status=data.get('study_status'),
            contact_type=data.get('contact_type', '语音录入'),
            actions=data.get('next_action') or data.get('actions'),
            log_date=date.today()
        )
        
        # 处理下次跟进时间
        next_date = data.get('next_follow_up_date')
        if next_date:
            from datetime import datetime
            if isinstance(next_date, str):
                try:
                    log.next_follow_up_date = datetime.strptime(next_date, '%Y-%m-%d').date()
                except ValueError:
                    pass
        
        db.session.add(log)
        
        # 更新学员最后联系时间
        student.last_contact_date = date.today()
        
        db.session.commit()
        
        return api_response(
            data={
                'log_id': log.id,
                'student_id': student_id,
                'student_name': student.name
            },
            message=f'已为学员"{student.name}"创建督学记录'
        )
    
    except Exception as e:
        db.session.rollback()
        return api_error(f'创建失败: {str(e)}', 'CREATE_FAILED', 500)


@api_v1_bp.route('/homework/batch-push', methods=['POST'])
@require_api_key
def batch_push_homework():
    """
    批量推送作业（供扣子调用）
    
    可以推送已有作业，也可以直接创建新作业并推送
    
    Request Body:
        homework_id: 作业ID（可选，不传则创建新作业）
        title: 作业标题（创建新作业时必填）
        content: 作业内容（创建新作业时必填）
        due_date: 截止日期（可选）
        batch_id: 班次ID（可选）
        batch_name: 班次名称（可选，用于智能匹配）
        student_ids: 学员ID列表（可选，不传则推送给整个班次或所有学员）
    
    Returns:
        JSON: 推送结果
    """
    from app.models.homework import HomeworkTask
    from app.models.course import ClassBatch, StudentBatch
    from app.models.student import Student
    from datetime import date, datetime, timedelta
    import json
    
    # 同时支持 JSON body 和 query string 参数（兼容扣子平台）
    data = request.get_json(silent=True) or {}
    
    # 如果 JSON body 为空，从 query string 获取参数
    if not data:
        student_ids_str = request.args.get('student_ids', '')
        data = {
            'homework_id': request.args.get('homework_id'),
            'batch_id': request.args.get('batch_id'),
            'batch_name': request.args.get('batch_name', ''),
            'student_ids': [int(x) for x in student_ids_str.split(',') if x.strip()] if student_ids_str else [],
            'title': request.args.get('title', ''),
            'content': request.args.get('content', ''),
            'due_date': request.args.get('due_date')
        }
    
    homework_id = data.get('homework_id')
    title = data.get('title', '').strip() if data.get('title') else ''
    content = data.get('content', '').strip() if data.get('content') else ''
    due_date_str = data.get('due_date')
    batch_id = data.get('batch_id')
    batch_name = data.get('batch_name', '').strip() if data.get('batch_name') else ''
    student_ids = data.get('student_ids', [])
    
    # 如果没有作业ID，则创建新作业
    if not homework_id:
        if not title:
            return api_error('请提供作业标题', 'MISSING_TITLE', 400)
        
        # 解析截止日期
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except:
                due_date = date.today() + timedelta(days=7)  # 默认7天后
        else:
            due_date = date.today() + timedelta(days=7)
        
        # 创建新作业
        homework = HomeworkTask(
            task_name=title,
            description=content or title,
            task_type='daily',
            deadline=due_date,
            creator_id=1  # 默认创建者
        )
        db.session.add(homework)
        db.session.flush()  # 获取ID
        homework_id = homework.id
    else:
        # 验证作业存在
        homework = HomeworkTask.query.get(homework_id)
        if not homework:
            return api_error('作业不存在', 'HOMEWORK_NOT_FOUND', 404)
    
    target_student_ids = []
    
    # 如果提供了学员ID列表，直接使用
    if student_ids:
        target_student_ids = student_ids
    elif batch_id or batch_name:
        # 通过班次获取学员
        if not batch_id and batch_name:
            batch = ClassBatch.query.filter(
                ClassBatch.name.ilike(f'%{batch_name}%')
            ).first()
            if batch:
                batch_id = batch.id
        
        if batch_id:
            # 获取班次所有学员
            student_batches = StudentBatch.query.filter_by(
                batch_id=batch_id,
                status='active'
            ).all()
            target_student_ids = [sb.student_id for sb in student_batches]
    else:
        # 如果没有指定目标，推送给所有活跃学员（限制前20个）
        all_students = Student.query.filter_by(status='active').limit(20).all()
        target_student_ids = [s.id for s in all_students]
    
    if not target_student_ids:
        return api_error('未找到目标学员', 'NO_STUDENTS', 400)
    
    # 更新作业的目标学员
    try:
        # 合并现有目标学员
        existing_ids = []
        if homework.target_students:
            try:
                existing_ids = json.loads(homework.target_students)
            except:
                existing_ids = [int(x) for x in homework.target_students.split(',') if x.strip()]
        
        all_ids = list(set(existing_ids + target_student_ids))
        homework.target_students = json.dumps(all_ids)
        
        db.session.commit()
        
        # 获取学员名称
        students = Student.query.filter(Student.id.in_(target_student_ids)).all()
        student_names = [s.name for s in students]
        
        return api_response(
            data={
                'homework_id': homework_id,
                'homework_name': homework.task_name,
                'pushed_count': len(target_student_ids),
                'student_names': student_names[:10]  # 只返回前10个名字
            },
            message=f'已将作业"{homework.task_name}"推送给{len(target_student_ids)}名学员'
        )
    
    except Exception as e:
        db.session.rollback()
        return api_error(f'推送失败: {str(e)}', 'PUSH_FAILED', 500)


@api_v1_bp.route('/reminders/pending')
@require_api_key
def get_pending_reminders():
    """
    获取待处理事项（供扣子调用）
    
    返回督学老师需要处理的事项
    
    Query Params:
        type: 事项类型（follow_up/homework/all）
        days: 超期天数阈值（默认3天）
        limit: 返回数量限制（默认10）
    
    Returns:
        JSON: 待处理事项列表
    """
    from app.models.student import Student
    from app.models.supervision import SupervisionLog
    from app.models.homework import HomeworkTask, HomeworkSubmission
    from datetime import date, timedelta
    from sqlalchemy import func
    
    reminder_type = request.args.get('type', 'all')
    days_threshold = request.args.get('days', 3, type=int)
    limit = min(request.args.get('limit', 10, type=int), 50)
    
    result = {
        'follow_up_students': [],
        'pending_homework': [],
        'attention_students': [],
        'summary': {}
    }
    
    today = date.today()
    threshold_date = today - timedelta(days=days_threshold)
    
    # 待跟进学员（超过N天未联系）
    if reminder_type in ['follow_up', 'all']:
        # 获取超期未联系的学员
        overdue_students = Student.query.filter(
            db.or_(
                Student.last_contact_date < threshold_date,
                Student.last_contact_date.is_(None)
            ),
            Student.status == '在读'
        ).order_by(Student.last_contact_date.asc().nullsfirst()).limit(limit).all()
        
        result['follow_up_students'] = [{
            'id': s.id,
            'name': s.name,
            'class_name': s.class_name,
            'phone': s.phone,
            'last_contact_date': s.last_contact_date.isoformat() if s.last_contact_date else None,
            'days_overdue': (today - s.last_contact_date).days if s.last_contact_date else 999
        } for s in overdue_students]
    
    # 待批改作业
    if reminder_type in ['homework', 'all']:
        active_homework = HomeworkTask.query.filter(
            HomeworkTask.status == 'published',
            HomeworkTask.deadline >= today
        ).all()
        
        for hw in active_homework[:limit]:
            stats = hw.get_statistics()
            if stats['completed'] < stats['total_target']:
                result['pending_homework'].append({
                    'id': hw.id,
                    'task_name': hw.task_name,
                    'deadline': hw.deadline.isoformat() if hw.deadline else None,
                    'completed': stats['completed'],
                    'total': stats['total_target'],
                    'completion_rate': round(stats['completion_rate'], 1)
                })
    
    # 重点关注学员
    if reminder_type == 'all':
        attention_students = Student.query.filter_by(
            need_attention=True,
            status='在读'
        ).limit(limit).all()
        
        result['attention_students'] = [{
            'id': s.id,
            'name': s.name,
            'class_name': s.class_name,
            'is_agreement': s.is_agreement
        } for s in attention_students]
    
    # 汇总信息
    result['summary'] = {
        'follow_up_count': len(result['follow_up_students']),
        'pending_homework_count': len(result['pending_homework']),
        'attention_count': len(result['attention_students']),
        'today': today.isoformat()
    }
    
    return api_response(
        data=result,
        message=f'共有{result["summary"]["follow_up_count"]}个待跟进学员，{result["summary"]["pending_homework_count"]}个待完成作业'
    )


@api_v1_bp.route('/reports/weekly')
@require_api_key
def get_weekly_report():
    """
    生成周报数据（供扣子调用）
    
    生成督学老师的周工作报告
    
    Query Params:
        week: 周选择（current/last，默认current）
    
    Returns:
        JSON: 周报数据
    """
    from app.models.student import Student
    from app.models.supervision import SupervisionLog
    from app.models.homework import HomeworkTask, HomeworkSubmission
    from datetime import date, timedelta
    from sqlalchemy import func
    
    week = request.args.get('week', 'current')
    
    today = date.today()
    
    # 计算周的起止日期
    if week == 'current':
        # 本周一
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
    else:
        # 上周
        start_of_week = today - timedelta(days=today.weekday() + 7)
        end_of_week = start_of_week + timedelta(days=6)
    
    # 督学记录统计
    log_count = SupervisionLog.query.filter(
        SupervisionLog.log_date >= start_of_week,
        SupervisionLog.log_date <= end_of_week
    ).count()
    
    # 按学员心态分布
    mood_stats = db.session.query(
        SupervisionLog.student_mood,
        func.count(SupervisionLog.id)
    ).filter(
        SupervisionLog.log_date >= start_of_week,
        SupervisionLog.log_date <= end_of_week,
        SupervisionLog.student_mood.isnot(None)
    ).group_by(SupervisionLog.student_mood).all()
    
    mood_distribution = {mood: count for mood, count in mood_stats}
    
    # 联系的学员数量（去重）
    contacted_students = db.session.query(
        func.count(func.distinct(SupervisionLog.student_id))
    ).filter(
        SupervisionLog.log_date >= start_of_week,
        SupervisionLog.log_date <= end_of_week
    ).scalar() or 0
    
    # 学员总数
    total_students = Student.query.filter_by(status='在读').count()
    
    # 作业统计
    homework_published = HomeworkTask.query.filter(
        HomeworkTask.publish_time >= start_of_week,
        HomeworkTask.publish_time <= end_of_week + timedelta(days=1)
    ).count()
    
    # 作业完成情况
    submissions_count = HomeworkSubmission.query.filter(
        HomeworkSubmission.submit_time >= start_of_week,
        HomeworkSubmission.submit_time <= end_of_week + timedelta(days=1)
    ).count()
    
    # 平均正确率
    avg_accuracy = db.session.query(
        func.avg(HomeworkSubmission.accuracy_rate)
    ).filter(
        HomeworkSubmission.submit_time >= start_of_week,
        HomeworkSubmission.submit_time <= end_of_week + timedelta(days=1)
    ).scalar() or 0
    
    # 重点关注学员变化
    attention_students = Student.query.filter_by(
        need_attention=True,
        status='在读'
    ).all()
    
    report = {
        'period': {
            'week': week,
            'start_date': start_of_week.isoformat(),
            'end_date': end_of_week.isoformat()
        },
        'supervision': {
            'total_logs': log_count,
            'contacted_students': contacted_students,
            'total_students': total_students,
            'contact_rate': round(contacted_students / total_students * 100, 1) if total_students > 0 else 0,
            'mood_distribution': mood_distribution
        },
        'homework': {
            'published': homework_published,
            'submissions': submissions_count,
            'avg_accuracy': round(avg_accuracy, 1)
        },
        'attention': {
            'count': len(attention_students),
            'students': [{'id': s.id, 'name': s.name, 'class_name': s.class_name} for s in attention_students[:5]]
        },
        'summary_text': f'本周共完成{log_count}次督学记录，覆盖{contacted_students}/{total_students}名学员（覆盖率{round(contacted_students / total_students * 100, 1) if total_students > 0 else 0}%）。发布{homework_published}个作业，收到{submissions_count}份提交，平均正确率{round(avg_accuracy, 1)}%。'
    }
    
    return api_response(
        data=report,
        message='周报生成成功'
    )


# ============ 薄弱项更新接口（供题库系统调用）============

@api_v1_bp.route('/students/<int:id>/weakness', methods=['POST'])
@require_api_key
def update_student_weakness(id):
    """
    更新学员薄弱项
    
    Args:
        id: 学员ID
    
    Request Body:
        tags: 薄弱项标签数组
            - module: 模块名称
            - submodule: 子模块名称（可选）
            - accuracy: 正确率（可选）
    
    Returns:
        JSON: 操作结果
    """
    from app.models.student import Student
    from app.models.tag import WeaknessTag
    from app import db
    
    student = Student.query.get(id)
    if not student:
        return api_error('学员不存在', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data or 'tags' not in data:
        return api_error('缺少tags参数', 'INVALID_REQUEST', 400)
    
    tags = data.get('tags', [])
    
    try:
        for tag_data in tags:
            module = tag_data.get('module')
            if not module:
                continue
            
            submodule = tag_data.get('submodule', '')
            accuracy = tag_data.get('accuracy')
            
            # 检查是否已存在相同标签
            existing = WeaknessTag.query.filter_by(
                student_id=id,
                module=module,
                sub_module=submodule
            ).first()
            
            if existing:
                # 更新正确率
                if accuracy is not None:
                    existing.accuracy_rate = accuracy
            else:
                # 创建新标签
                tag = WeaknessTag(
                    student_id=id,
                    module=module,
                    sub_module=submodule,
                    accuracy_rate=accuracy
                )
                db.session.add(tag)
        
        db.session.commit()
        return api_response(message='薄弱项更新成功')
    
    except Exception as e:
        db.session.rollback()
        return api_error(f'更新失败: {str(e)}', 'UPDATE_FAILED', 500)


# ============ 错误处理 ============

@api_v1_bp.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return api_error('资源不存在', 'NOT_FOUND', 404)


@api_v1_bp.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return api_error('服务器内部错误', 'INTERNAL_ERROR', 500)
