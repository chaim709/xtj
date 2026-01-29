"""
作业管理路由 - 作业发布和成绩录入
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.homework import HomeworkTask, HomeworkSubmission
from app.models.student import Student
from app.services.homework_service import HomeworkService
from app.services.tag_service import TagService

homework_bp = Blueprint('homework', __name__)


@homework_bp.route('/')
@login_required
def list():
    """作业列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    tasks = HomeworkService.get_tasks(
        status=status or None,
        page=page,
        per_page=20
    )
    
    return render_template('homework/list.html',
                         tasks=tasks,
                         current_status=status)


@homework_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建作业"""
    if request.method == 'POST':
        data = {
            'task_name': request.form.get('task_name', '').strip(),
            'task_type': request.form.get('task_type'),
            'module': request.form.get('module'),
            'sub_module': request.form.get('sub_module'),
            'question_count': request.form.get('question_count', type=int),
            'suggested_time': request.form.get('suggested_time', type=int),
            'description': request.form.get('description', '').strip(),
            'target_class': request.form.get('target_class'),
            'creator_id': current_user.id,
        }
        
        # 处理截止时间
        deadline = request.form.get('deadline')
        if deadline:
            try:
                data['deadline'] = datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
        
        # 处理目标学员
        target_type = request.form.get('target_type', 'all')
        if target_type == 'all':
            # 所有学员
            if current_user.is_admin():
                students = Student.query.filter_by(status='active').all()
            else:
                students = Student.query.filter_by(
                    supervisor_id=current_user.id,
                    status='active'
                ).all()
            data['target_students'] = [s.id for s in students]
        elif target_type == 'class':
            # 指定班次
            class_name = request.form.get('target_class')
            students = Student.query.filter_by(
                class_name=class_name,
                status='active'
            ).all()
            data['target_students'] = [s.id for s in students]
        else:
            # 指定学员
            selected = request.form.getlist('target_students')
            data['target_students'] = [int(s) for s in selected if s]
        
        # 验证
        if not data['task_name']:
            flash('作业名称不能为空', 'danger')
            return redirect(url_for('homework.create'))
        
        if not data['target_students']:
            flash('请选择目标学员', 'danger')
            return redirect(url_for('homework.create'))
        
        try:
            task = HomeworkService.create_task(data)
            flash(f'作业 "{task.task_name}" 发布成功！', 'success')
            return redirect(url_for('homework.detail', id=task.id))
        except Exception as e:
            flash(f'发布失败：{str(e)}', 'danger')
    
    # 获取学员和班次列表
    if current_user.is_admin():
        students = Student.query.filter_by(status='active').order_by(Student.name).all()
    else:
        students = Student.query.filter_by(
            supervisor_id=current_user.id,
            status='active'
        ).order_by(Student.name).all()
    
    classes = db.session.query(Student.class_name).filter(
        Student.class_name.isnot(None),
        Student.status == 'active'
    ).distinct().all()
    classes = [c[0] for c in classes if c[0]]
    
    modules = TagService.get_modules()
    
    return render_template('homework/create.html',
                         students=students,
                         classes=classes,
                         modules=modules)


@homework_bp.route('/<int:id>')
@login_required
def detail(id):
    """作业详情"""
    task = HomeworkService.get_task(id)
    if not task:
        flash('作业不存在', 'danger')
        return redirect(url_for('homework.list'))
    
    # 获取统计信息
    stats = HomeworkService.get_task_statistics(id)
    
    # 获取提交记录
    submissions = HomeworkService.get_submissions_by_task(id)
    
    # 获取目标学员列表（用于录入）
    target_ids = []
    if task.target_students:
        target_ids = [int(x) for x in task.target_students.split(',') if x.strip()]
    
    target_students = Student.query.filter(Student.id.in_(target_ids)).all() if target_ids else []
    
    # 已提交的学员ID
    submitted_ids = set(s.student_id for s in submissions)
    
    return render_template('homework/detail.html',
                         task=task,
                         stats=stats,
                         submissions=submissions,
                         target_students=target_students,
                         submitted_ids=submitted_ids)


@homework_bp.route('/<int:id>/submit', methods=['POST'])
@login_required
def submit(id):
    """录入学员成绩"""
    task = HomeworkService.get_task(id)
    if not task:
        return jsonify({'success': False, 'message': '作业不存在'})
    
    student_id = request.form.get('student_id', type=int)
    if not student_id:
        return jsonify({'success': False, 'message': '请选择学员'})
    
    data = {
        'completed_count': request.form.get('completed_count', type=int),
        'correct_count': request.form.get('correct_count', type=int),
        'time_spent': request.form.get('time_spent', type=int),
        'wrong_questions': request.form.get('wrong_questions', '').strip(),
        'feedback': request.form.get('feedback', '').strip(),
    }
    
    # 验证
    if data['completed_count'] and data['correct_count']:
        if data['correct_count'] > data['completed_count']:
            return jsonify({'success': False, 'message': '正确数量不能大于完成数量'})
    
    try:
        submission = HomeworkService.record_submission(
            task_id=id,
            student_id=student_id,
            data=data,
            recorder_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'message': '成绩录入成功',
            'submission': submission.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@homework_bp.route('/<int:id>/close', methods=['POST'])
@login_required
def close(id):
    """关闭作业"""
    task = HomeworkService.get_task(id)
    if not task:
        flash('作业不存在', 'danger')
        return redirect(url_for('homework.list'))
    
    # 权限检查
    if not current_user.is_admin() and task.creator_id != current_user.id:
        flash('您没有权限关闭此作业', 'danger')
        return redirect(url_for('homework.detail', id=id))
    
    HomeworkService.close_task(id)
    flash('作业已关闭', 'success')
    return redirect(url_for('homework.detail', id=id))
