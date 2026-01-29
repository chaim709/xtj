"""
督学服务路由 - 督学日志记录与督学管理
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.student import Student
from app.models.supervision import SupervisionLog
from app.models.study_plan import StudyPlan, PlanTask, PlanTemplate
from app.models.user import User
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


# ==================== 督学管理模块 ====================

@supervision_bp.route('/manage')
@login_required
def manage():
    """督学管理主页"""
    # 获取督学人员ID（管理员可查看所有）
    supervisor_id = None if current_user.is_admin() else current_user.id
    
    # 获取概览数据
    overview = SupervisionService.get_management_overview(supervisor_id)
    
    # 获取计划模板列表
    templates = SupervisionService.get_plan_templates()
    
    # 获取督学人员列表（用于分配功能）
    supervisors = []
    if current_user.is_admin():
        supervisors = User.query.filter_by(role='staff').all()
    
    return render_template('supervision/manage.html',
                         overview=overview,
                         templates=templates,
                         supervisors=supervisors)


@supervision_bp.route('/manage/students')
@login_required
def manage_students():
    """获取学员督学数据（AJAX）"""
    supervisor_id = None if current_user.is_admin() else current_user.id
    filter_type = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    
    data = SupervisionService.get_students_for_supervision(
        supervisor_id=supervisor_id,
        filter_type=filter_type,
        page=page,
        per_page=20
    )
    
    return jsonify(data)


@supervision_bp.route('/manage/plans')
@login_required
def manage_plans():
    """获取学习计划数据（AJAX）"""
    supervisor_id = None if current_user.is_admin() else current_user.id
    status = request.args.get('status', 'active')
    page = request.args.get('page', 1, type=int)
    
    data = SupervisionService.get_plans_overview(
        supervisor_id=supervisor_id,
        status=status,
        page=page,
        per_page=20
    )
    
    return jsonify(data)


@supervision_bp.route('/manage/logs')
@login_required
def manage_logs():
    """获取督学记录数据（AJAX）"""
    supervisor_id = None if current_user.is_admin() else current_user.id
    student_id = request.args.get('student_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    
    # 解析日期
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = None
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            end_date = None
    
    data = SupervisionService.get_supervision_logs_overview(
        supervisor_id=supervisor_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=20
    )
    
    return jsonify(data)


@supervision_bp.route('/manage/stats')
@login_required
def manage_stats():
    """获取业绩统计数据（AJAX）"""
    supervisor_id = None if current_user.is_admin() else current_user.id
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 解析日期
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = None
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            end_date = None
    
    data = SupervisionService.get_performance_stats(
        supervisor_id=supervisor_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(data)


@supervision_bp.route('/templates', methods=['GET', 'POST'])
@login_required
def templates():
    """计划模板管理"""
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'phase': request.form.get('phase'),
            'duration_days': request.form.get('duration_days', type=int),
            'description': request.form.get('description'),
        }
        
        try:
            template = SupervisionService.create_plan_template(data, current_user.id)
            flash('模板创建成功！', 'success')
        except Exception as e:
            flash(f'创建失败：{str(e)}', 'danger')
        
        return redirect(url_for('supervision.templates'))
    
    templates = SupervisionService.get_plan_templates(is_active=None)
    return render_template('supervision/templates.html', templates=templates)


@supervision_bp.route('/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """获取模板详情（AJAX）"""
    template = PlanTemplate.query.get_or_404(template_id)
    return jsonify(template.to_dict())


@supervision_bp.route('/templates/<int:template_id>/edit', methods=['POST'])
@login_required
def edit_template(template_id):
    """编辑模板"""
    template = PlanTemplate.query.get_or_404(template_id)
    
    template.name = request.form.get('name', template.name)
    template.phase = request.form.get('phase', template.phase)
    template.duration_days = request.form.get('duration_days', type=int) or template.duration_days
    template.description = request.form.get('description', template.description)
    
    db.session.commit()
    flash('模板更新成功！', 'success')
    return redirect(url_for('supervision.templates'))


@supervision_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """删除模板"""
    template = PlanTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    flash('模板已删除', 'success')
    return redirect(url_for('supervision.templates'))


@supervision_bp.route('/batch-create-plan', methods=['POST'])
@login_required
def batch_create_plan():
    """批量创建学习计划"""
    template_id = request.form.get('template_id', type=int)
    student_ids = request.form.getlist('student_ids', type=int)
    
    if not template_id or not student_ids:
        return jsonify({'success': False, 'message': '请选择模板和学员'})
    
    try:
        plans = SupervisionService.create_plan_from_template(
            template_id=template_id,
            student_ids=student_ids,
            user_id=current_user.id
        )
        return jsonify({
            'success': True,
            'message': f'成功为 {len(plans)} 名学员创建学习计划',
            'count': len(plans)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@supervision_bp.route('/assign-students', methods=['POST'])
@login_required
def assign_students():
    """分配学员给督学老师"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '权限不足'})
    
    supervisor_id = request.form.get('supervisor_id', type=int)
    student_ids = request.form.getlist('student_ids', type=int)
    
    if not supervisor_id or not student_ids:
        return jsonify({'success': False, 'message': '请选择督学老师和学员'})
    
    try:
        count = SupervisionService.assign_students_to_supervisor(student_ids, supervisor_id)
        return jsonify({
            'success': True,
            'message': f'成功分配 {count} 名学员',
            'count': count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@supervision_bp.route('/quick-log', methods=['POST'])
@login_required
def quick_log():
    """快速记录督学日志（AJAX）"""
    data = {
        'student_id': request.form.get('student_id', type=int),
        'supervisor_id': current_user.id,
        'contact_type': request.form.get('contact_type'),
        'content': request.form.get('content', '').strip(),
        'student_mood': request.form.get('student_mood'),
        'study_status': request.form.get('study_status'),
        'log_date': date.today(),
    }
    
    if not data['student_id']:
        return jsonify({'success': False, 'message': '请选择学员'})
    
    try:
        log = SupervisionService.create_log(data)
        return jsonify({
            'success': True,
            'message': '记录成功',
            'log_id': log.id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
