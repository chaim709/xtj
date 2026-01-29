"""
督学服务路由 - 督学日志记录
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.student import Student
from app.models.supervision import SupervisionLog
from app.services.supervision_service import SupervisionService
from app.services.student_service import StudentService

supervision_bp = Blueprint('supervision', __name__)


@supervision_bp.route('/log', methods=['GET', 'POST'])
@login_required
def log_form():
    """督学日志记录"""
    # 获取学员ID（如果从学员详情页跳转过来）
    student_id = request.args.get('student_id', type=int)
    student = None
    
    if student_id:
        student = StudentService.get_student(student_id)
    
    if request.method == 'POST':
        # 获取表单数据
        student_id = request.form.get('student_id', type=int)
        
        if not student_id:
            flash('请选择学员', 'danger')
            return redirect(url_for('supervision.log_form'))
        
        data = {
            'student_id': student_id,
            'supervisor_id': current_user.id,
            'contact_type': request.form.get('contact_type'),
            'contact_duration': request.form.get('contact_duration', type=int),
            'content': request.form.get('content', '').strip(),
            'student_mood': request.form.get('student_mood'),
            'study_status': request.form.get('study_status'),
            'self_discipline': request.form.get('self_discipline'),
            'actions': request.form.get('actions', '').strip(),
            'tags': request.form.get('tags', '').strip(),
        }
        
        # 处理下次跟进日期
        next_date = request.form.get('next_follow_up_date', '')
        if next_date:
            try:
                data['next_follow_up_date'] = datetime.strptime(next_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 处理日志日期
        log_date = request.form.get('log_date', '')
        if log_date:
            try:
                data['log_date'] = datetime.strptime(log_date, '%Y-%m-%d').date()
            except ValueError:
                data['log_date'] = date.today()
        else:
            data['log_date'] = date.today()
        
        try:
            log = SupervisionService.create_log(data)
            flash('督学日志记录成功！', 'success')
            return redirect(url_for('students.detail', id=student_id))
        except Exception as e:
            flash(f'记录失败：{str(e)}', 'danger')
    
    # 获取学员列表（供选择）
    if current_user.is_admin():
        students = Student.query.filter_by(status='active').order_by(Student.name).all()
    else:
        students = Student.query.filter_by(
            supervisor_id=current_user.id,
            status='active'
        ).order_by(Student.name).all()
    
    # 配置选项
    from config import Config
    
    return render_template('supervision/log_form.html',
                         students=students,
                         selected_student=student,
                         contact_options=Config.CONTACT_OPTIONS,
                         mood_options=Config.MOOD_OPTIONS,
                         status_options=Config.STATUS_OPTIONS,
                         common_phrases=Config.COMMON_PHRASES,
                         today=date.today())


@supervision_bp.route('/history/<int:student_id>')
@login_required
def history(student_id):
    """学员督学历史"""
    student = StudentService.get_student(student_id)
    if not student:
        flash('学员不存在', 'danger')
        return redirect(url_for('students.list'))
    
    # 权限检查
    if not current_user.is_admin() and student.supervisor_id != current_user.id:
        flash('您没有权限查看该学员', 'danger')
        return redirect(url_for('students.list'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = SupervisionLog.query.filter_by(student_id=student_id)\
        .order_by(SupervisionLog.log_date.desc(), SupervisionLog.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('supervision/history.html',
                         student=student,
                         logs=logs)


@supervision_bp.route('/my-logs')
@login_required
def my_logs():
    """我的督学记录"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 日期筛选
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    logs = SupervisionService.get_logs_by_supervisor(
        supervisor_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page
    )
    
    return render_template('supervision/my_logs.html',
                         logs=logs,
                         start_date=start_date,
                         end_date=end_date)


@supervision_bp.route('/log/<int:log_id>')
@login_required
def log_detail(log_id):
    """日志详情"""
    log = SupervisionService.get_log(log_id)
    if not log:
        flash('日志不存在', 'danger')
        return redirect(url_for('supervision.my_logs'))
    
    # 权限检查
    if not current_user.is_admin() and log.supervisor_id != current_user.id:
        flash('您没有权限查看该日志', 'danger')
        return redirect(url_for('supervision.my_logs'))
    
    return render_template('supervision/log_detail.html', log=log)
