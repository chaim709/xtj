"""
课程管理路由 - 科目、招生项目、报名套餐、班型、班次、课表、老师管理
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.course import (
    Subject, Project, Package, ClassType, ClassBatch,
    Schedule, ScheduleChangeLog, StudentBatch
)
from app.models.teacher import Teacher
from app.services.course_service import CourseService
from app.services.teacher_service import TeacherService
from app.services.schedule_service import ScheduleService
from app.services.attendance_service import AttendanceService
from app.services.recording_service import RecordingService

courses_bp = Blueprint('courses', __name__)


# ==================== 科目管理 ====================

@courses_bp.route('/subjects')
@login_required
def subject_list():
    """科目列表"""
    # 按考试类型分组
    civil_subjects = CourseService.get_subjects(exam_type='civil', include_inactive=True)
    career_subjects = CourseService.get_subjects(exam_type='career', include_inactive=True)
    common_subjects = CourseService.get_subjects(exam_type='common', include_inactive=True)
    
    return render_template('courses/subjects/list.html',
                         civil_subjects=civil_subjects,
                         career_subjects=career_subjects,
                         common_subjects=common_subjects)


@courses_bp.route('/subjects/create', methods=['GET', 'POST'])
@login_required
def subject_create():
    """新增科目"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.subject_list'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'short_name': request.form.get('short_name', '').strip(),
            'exam_type': request.form.get('exam_type', 'common'),
            'sort_order': request.form.get('sort_order', 0, type=int),
        }
        
        if not data['name']:
            flash('科目名称不能为空', 'danger')
            return render_template('courses/subjects/form.html', subject=None)
        
        try:
            subject = CourseService.create_subject(data)
            flash(f'科目 "{subject.name}" 创建成功！', 'success')
            return redirect(url_for('courses.subject_list'))
        except Exception as e:
            flash(f'创建失败：{str(e)}', 'danger')
    
    return render_template('courses/subjects/form.html', subject=None)


@courses_bp.route('/subjects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def subject_edit(id):
    """编辑科目"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.subject_list'))
    
    subject = CourseService.get_subject(id)
    if not subject:
        flash('科目不存在', 'danger')
        return redirect(url_for('courses.subject_list'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'short_name': request.form.get('short_name', '').strip(),
            'exam_type': request.form.get('exam_type', 'common'),
            'sort_order': request.form.get('sort_order', 0, type=int),
        }
        
        try:
            CourseService.update_subject(id, data)
            flash('科目更新成功！', 'success')
            return redirect(url_for('courses.subject_list'))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('courses/subjects/form.html', subject=subject)


@courses_bp.route('/subjects/<int:id>/toggle', methods=['POST'])
@login_required
def subject_toggle(id):
    """切换科目状态"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        subject = CourseService.toggle_subject_status(id)
        return jsonify({
            'success': True,
            'status': subject.status,
            'message': f'科目已{"启用" if subject.status == "active" else "停用"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
def subject_delete(id):
    """删除科目"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        CourseService.delete_subject(id)
        return jsonify({'success': True, 'message': '科目已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 招生项目 ====================

@courses_bp.route('/projects')
@login_required
def project_list():
    """招生项目列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    year = request.args.get('year', type=int)
    
    projects = CourseService.get_projects(
        status=status or None,
        year=year,
        page=page,
        per_page=20
    )
    
    # 获取年份选项
    years = db.session.query(Project.year).distinct().order_by(Project.year.desc()).all()
    years = [y[0] for y in years]
    
    return render_template('courses/projects/list.html',
                         projects=projects,
                         years=years,
                         current_status=status,
                         current_year=year)


@courses_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def project_create():
    """新增招生项目"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.project_list'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'exam_type': request.form.get('exam_type'),
            'year': request.form.get('year', type=int),
            'description': request.form.get('description', '').strip(),
        }
        
        # 处理日期
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if start_date:
            data['start_date'] = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            data['end_date'] = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not data['name']:
            flash('项目名称不能为空', 'danger')
            return render_template('courses/projects/form.html', project=None)
        
        try:
            project = CourseService.create_project(data)
            flash(f'项目 "{project.name}" 创建成功！', 'success')
            return redirect(url_for('courses.project_detail', id=project.id))
        except Exception as e:
            flash(f'创建失败：{str(e)}', 'danger')
    
    return render_template('courses/projects/form.html', project=None)


@courses_bp.route('/projects/<int:id>')
@login_required
def project_detail(id):
    """招生项目详情"""
    project = CourseService.get_project(id)
    if not project:
        flash('项目不存在', 'danger')
        return redirect(url_for('courses.project_list'))
    
    # 获取套餐和班型
    packages = CourseService.get_packages(project_id=id)
    class_types = CourseService.get_class_types(project_id=id)
    
    # 统计数据
    total_students = 0
    total_batches = 0
    for ct in class_types:
        total_batches += ct.batches.count()
        for batch in ct.batches:
            total_students += batch.enrolled_count
    
    stats = {
        'package_count': len(packages),
        'type_count': len(class_types),
        'batch_count': total_batches,
        'student_count': total_students,
    }
    
    return render_template('courses/projects/detail.html',
                         project=project,
                         packages=packages,
                         class_types=class_types,
                         stats=stats)


@courses_bp.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(id):
    """编辑招生项目"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.project_list'))
    
    project = CourseService.get_project(id)
    if not project:
        flash('项目不存在', 'danger')
        return redirect(url_for('courses.project_list'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'exam_type': request.form.get('exam_type'),
            'year': request.form.get('year', type=int),
            'description': request.form.get('description', '').strip(),
        }
        
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if start_date:
            data['start_date'] = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            data['end_date'] = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        try:
            CourseService.update_project(id, data)
            flash('项目更新成功！', 'success')
            return redirect(url_for('courses.project_detail', id=id))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('courses/projects/form.html', project=project)


@courses_bp.route('/projects/<int:id>/status', methods=['POST'])
@login_required
def project_status(id):
    """更新项目状态"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    status = request.form.get('status')
    if status not in ['preparing', 'recruiting', 'ended']:
        return jsonify({'success': False, 'message': '无效的状态'})
    
    try:
        project = CourseService.update_project_status(id, status)
        return jsonify({
            'success': True,
            'status': project.status,
            'status_display': project.status_display,
            'message': '状态已更新'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
def project_delete(id):
    """删除项目"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        CourseService.delete_project(id)
        flash('项目已删除', 'success')
        return jsonify({'success': True, 'redirect': url_for('courses.project_list')})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 报名套餐 ====================

@courses_bp.route('/packages')
@login_required
def package_list():
    """报名套餐列表"""
    project_id = request.args.get('project_id', type=int)
    
    projects = CourseService.get_all_projects()
    
    if project_id:
        packages = CourseService.get_packages(project_id=project_id)
        current_project = CourseService.get_project(project_id)
    else:
        packages = []
        current_project = None
        if projects:
            # 默认显示第一个项目的套餐
            current_project = projects[0]
            packages = CourseService.get_packages(project_id=current_project.id)
    
    return render_template('courses/packages/list.html',
                         packages=packages,
                         projects=projects,
                         current_project=current_project)


@courses_bp.route('/packages/create', methods=['GET', 'POST'])
@login_required
def package_create():
    """新增报名套餐"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.package_list'))
    
    project_id = request.args.get('project_id', type=int)
    
    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        
        data = {
            'project_id': project_id,
            'name': request.form.get('name', '').strip(),
            'package_type': request.form.get('package_type'),
            'price': request.form.get('price', 0, type=float),
            'valid_days': request.form.get('valid_days', type=int),
            'description': request.form.get('description', '').strip(),
            'include_all_types': request.form.get('include_all_types') == 'on',
            'sort_order': request.form.get('sort_order', 0, type=int),
        }
        
        # 处理有效期日期
        valid_start = request.form.get('valid_start')
        valid_end = request.form.get('valid_end')
        if valid_start:
            data['valid_start'] = datetime.strptime(valid_start, '%Y-%m-%d').date()
        if valid_end:
            data['valid_end'] = datetime.strptime(valid_end, '%Y-%m-%d').date()
        
        # 处理包含的班型
        if not data['include_all_types']:
            included_types = request.form.getlist('included_type_ids')
            data['included_type_ids'] = ','.join(included_types)
        
        # 处理优惠规则
        discount_rules = {}
        # 团报优惠
        group_discount = []
        for i in range(1, 4):
            min_people = request.form.get(f'group_min_{i}', type=int)
            discount = request.form.get(f'group_discount_{i}', type=float)
            if min_people and discount:
                group_discount.append({
                    'min_people': min_people,
                    'discount': discount,
                    'description': f'{min_people}人团报优惠{int(discount)}元'
                })
        if group_discount:
            discount_rules['group_discount'] = group_discount
        
        # 早鸟优惠
        early_bird_end = request.form.get('early_bird_end')
        early_bird_discount = request.form.get('early_bird_discount', type=float)
        if early_bird_end and early_bird_discount:
            discount_rules['early_bird'] = {
                'end_date': early_bird_end,
                'discount': early_bird_discount,
                'description': f'早鸟优惠{int(early_bird_discount)}元'
            }
        
        if discount_rules:
            data['discount_rules'] = discount_rules
        
        if not data['name']:
            flash('套餐名称不能为空', 'danger')
        else:
            try:
                package = CourseService.create_package(data)
                flash(f'套餐 "{package.name}" 创建成功！', 'success')
                return redirect(url_for('courses.package_list', project_id=project_id))
            except Exception as e:
                flash(f'创建失败：{str(e)}', 'danger')
    
    projects = CourseService.get_all_projects()
    current_project = CourseService.get_project(project_id) if project_id else None
    class_types = CourseService.get_class_types(project_id) if project_id else []
    
    return render_template('courses/packages/form.html',
                         package=None,
                         projects=projects,
                         current_project=current_project,
                         class_types=class_types)


@courses_bp.route('/packages/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def package_edit(id):
    """编辑报名套餐"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.package_list'))
    
    package = CourseService.get_package(id)
    if not package:
        flash('套餐不存在', 'danger')
        return redirect(url_for('courses.package_list'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'package_type': request.form.get('package_type'),
            'price': request.form.get('price', 0, type=float),
            'valid_days': request.form.get('valid_days', type=int),
            'description': request.form.get('description', '').strip(),
            'include_all_types': request.form.get('include_all_types') == 'on',
            'sort_order': request.form.get('sort_order', 0, type=int),
        }
        
        # 处理优惠规则（同create）
        discount_rules = {}
        group_discount = []
        for i in range(1, 4):
            min_people = request.form.get(f'group_min_{i}', type=int)
            discount = request.form.get(f'group_discount_{i}', type=float)
            if min_people and discount:
                group_discount.append({
                    'min_people': min_people,
                    'discount': discount,
                    'description': f'{min_people}人团报优惠{int(discount)}元'
                })
        if group_discount:
            discount_rules['group_discount'] = group_discount
        
        early_bird_end = request.form.get('early_bird_end')
        early_bird_discount = request.form.get('early_bird_discount', type=float)
        if early_bird_end and early_bird_discount:
            discount_rules['early_bird'] = {
                'end_date': early_bird_end,
                'discount': early_bird_discount,
                'description': f'早鸟优惠{int(early_bird_discount)}元'
            }
        
        data['discount_rules'] = discount_rules
        
        try:
            CourseService.update_package(id, data)
            flash('套餐更新成功！', 'success')
            return redirect(url_for('courses.package_list', project_id=package.project_id))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    projects = CourseService.get_all_projects()
    class_types = CourseService.get_class_types(package.project_id)
    
    return render_template('courses/packages/form.html',
                         package=package,
                         projects=projects,
                         current_project=package.project,
                         class_types=class_types)


@courses_bp.route('/packages/<int:id>/toggle', methods=['POST'])
@login_required
def package_toggle(id):
    """切换套餐状态"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        package = CourseService.toggle_package_status(id)
        return jsonify({
            'success': True,
            'status': package.status,
            'message': f'套餐已{"上架" if package.status == "active" else "下架"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 班型管理 ====================

@courses_bp.route('/types')
@login_required
def type_list():
    """班型列表"""
    project_id = request.args.get('project_id', type=int)
    
    projects = CourseService.get_all_projects()
    
    if project_id:
        class_types = CourseService.get_class_types(project_id)
        current_project = CourseService.get_project(project_id)
    else:
        class_types = []
        current_project = None
        if projects:
            current_project = projects[0]
            class_types = CourseService.get_class_types(current_project.id)
    
    return render_template('courses/types/list.html',
                         class_types=class_types,
                         projects=projects,
                         current_project=current_project)


@courses_bp.route('/types/create', methods=['GET', 'POST'])
@login_required
def type_create():
    """新增班型"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.type_list'))
    
    project_id = request.args.get('project_id', type=int)
    
    if request.method == 'POST':
        data = {
            'project_id': request.form.get('project_id', type=int),
            'name': request.form.get('name', '').strip(),
            'planned_days': request.form.get('planned_days', type=int),
            'single_price': request.form.get('single_price', type=float),
            'description': request.form.get('description', '').strip(),
            'sort_order': request.form.get('sort_order', 0, type=int),
        }
        
        if not data['name']:
            flash('班型名称不能为空', 'danger')
        else:
            try:
                class_type = CourseService.create_class_type(data)
                flash(f'班型 "{class_type.name}" 创建成功！', 'success')
                return redirect(url_for('courses.type_list', project_id=data['project_id']))
            except Exception as e:
                flash(f'创建失败：{str(e)}', 'danger')
    
    projects = CourseService.get_all_projects()
    current_project = CourseService.get_project(project_id) if project_id else None
    
    return render_template('courses/types/form.html',
                         class_type=None,
                         projects=projects,
                         current_project=current_project)


@courses_bp.route('/types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def type_edit(id):
    """编辑班型"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.type_list'))
    
    class_type = CourseService.get_class_type(id)
    if not class_type:
        flash('班型不存在', 'danger')
        return redirect(url_for('courses.type_list'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'planned_days': request.form.get('planned_days', type=int),
            'single_price': request.form.get('single_price', type=float),
            'description': request.form.get('description', '').strip(),
            'sort_order': request.form.get('sort_order', 0, type=int),
        }
        
        try:
            CourseService.update_class_type(id, data)
            flash('班型更新成功！', 'success')
            return redirect(url_for('courses.type_list', project_id=class_type.project_id))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    projects = CourseService.get_all_projects()
    
    return render_template('courses/types/form.html',
                         class_type=class_type,
                         projects=projects,
                         current_project=class_type.project)


@courses_bp.route('/types/reorder', methods=['POST'])
@login_required
def type_reorder():
    """重新排序班型"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    project_id = request.form.get('project_id', type=int)
    type_ids = request.form.getlist('type_ids[]', type=int)
    
    try:
        CourseService.reorder_class_types(project_id, type_ids)
        return jsonify({'success': True, 'message': '排序已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/types/<int:id>/delete', methods=['POST'])
@login_required
def type_delete(id):
    """删除班型"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        CourseService.delete_class_type(id)
        return jsonify({'success': True, 'message': '班型已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 班次管理 ====================

@courses_bp.route('/batches')
@login_required
def batch_list():
    """班次列表"""
    page = request.args.get('page', 1, type=int)
    project_id = request.args.get('project_id', type=int)
    class_type_id = request.args.get('class_type_id', type=int)
    status = request.args.get('status', '')
    
    batches = CourseService.get_batches(
        class_type_id=class_type_id,
        project_id=project_id,
        status=status or None,
        page=page,
        per_page=20
    )
    
    projects = CourseService.get_all_projects()
    class_types = []
    if project_id:
        class_types = CourseService.get_class_types(project_id)
    
    return render_template('courses/batches/list.html',
                         batches=batches,
                         projects=projects,
                         class_types=class_types,
                         current_project_id=project_id,
                         current_type_id=class_type_id,
                         current_status=status)


@courses_bp.route('/batches/create', methods=['GET', 'POST'])
@login_required
def batch_create():
    """新增班次"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.batch_list'))
    
    class_type_id = request.args.get('class_type_id', type=int)
    
    if request.method == 'POST':
        data = {
            'class_type_id': request.form.get('class_type_id', type=int),
            'name': request.form.get('name', '').strip(),
            'max_students': request.form.get('max_students', type=int),
            'classroom': request.form.get('classroom', '').strip(),
        }
        
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if start_date:
            data['start_date'] = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            data['end_date'] = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not data['class_type_id']:
            flash('请选择班型', 'danger')
        elif not data.get('start_date') or not data.get('end_date'):
            flash('请设置开课和结课日期', 'danger')
        else:
            try:
                batch = CourseService.create_batch(data)
                flash(f'班次 "{batch.name}" 创建成功！', 'success')
                return redirect(url_for('courses.batch_detail', id=batch.id))
            except Exception as e:
                flash(f'创建失败：{str(e)}', 'danger')
    
    projects = CourseService.get_all_projects()
    class_type = CourseService.get_class_type(class_type_id) if class_type_id else None
    
    return render_template('courses/batches/form.html',
                         batch=None,
                         projects=projects,
                         class_type=class_type)


@courses_bp.route('/batches/<int:id>')
@login_required
def batch_detail(id):
    """班次详情"""
    batch = CourseService.get_batch(id)
    if not batch:
        flash('班次不存在', 'danger')
        return redirect(url_for('courses.batch_list'))
    
    # 获取课表
    schedules = ScheduleService.get_schedules(id)
    
    # 获取学员
    students = CourseService.get_batch_students(id)
    
    # 科目列表（用于添加课表）
    subjects = CourseService.get_subjects()
    
    # 老师列表
    teachers = TeacherService.get_all_teachers()
    
    return render_template('courses/batches/detail.html',
                         batch=batch,
                         schedules=schedules,
                         students=students,
                         subjects=subjects,
                         teachers=teachers)


@courses_bp.route('/batches/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def batch_edit(id):
    """编辑班次"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.batch_list'))
    
    batch = CourseService.get_batch(id)
    if not batch:
        flash('班次不存在', 'danger')
        return redirect(url_for('courses.batch_list'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'max_students': request.form.get('max_students', type=int),
            'classroom': request.form.get('classroom', '').strip(),
        }
        
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if start_date:
            data['start_date'] = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            data['end_date'] = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        try:
            CourseService.update_batch(id, data)
            flash('班次更新成功！', 'success')
            return redirect(url_for('courses.batch_detail', id=id))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    projects = CourseService.get_all_projects()
    
    return render_template('courses/batches/form.html',
                         batch=batch,
                         projects=projects,
                         class_type=batch.class_type)


@courses_bp.route('/batches/<int:id>/status', methods=['POST'])
@login_required
def batch_status(id):
    """更新班次状态"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    status = request.form.get('status')
    if status not in ['recruiting', 'ongoing', 'ended']:
        return jsonify({'success': False, 'message': '无效的状态'})
    
    try:
        batch = CourseService.update_batch_status(id, status)
        return jsonify({
            'success': True,
            'status': batch.status,
            'status_display': batch.status_display,
            'message': '状态已更新'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/batches/<int:id>/copy', methods=['POST'])
@login_required
def batch_copy(id):
    """复制班次"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    new_start_date = request.form.get('new_start_date')
    if not new_start_date:
        return jsonify({'success': False, 'message': '请选择新班次开课日期'})
    
    try:
        new_start_date = datetime.strptime(new_start_date, '%Y-%m-%d').date()
        new_batch = CourseService.copy_batch(id, new_start_date)
        
        # 复制课表
        ScheduleService.copy_from_batch(id, new_batch.id)
        
        return jsonify({
            'success': True,
            'batch_id': new_batch.id,
            'message': f'班次已复制为 "{new_batch.name}"',
            'redirect': url_for('courses.batch_detail', id=new_batch.id)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/batches/<int:id>/delete', methods=['POST'])
@login_required
def batch_delete(id):
    """删除班次"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        CourseService.delete_batch(id)
        return jsonify({'success': True, 'message': '班次已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 老师管理 ====================

@courses_bp.route('/teachers')
@login_required
def teacher_list():
    """老师列表"""
    page = request.args.get('page', 1, type=int)
    subject_id = request.args.get('subject_id', type=int)
    status = request.args.get('status', 'active')
    
    teachers = TeacherService.get_teachers(
        subject_id=subject_id,
        status=status if status else None,
        page=page,
        per_page=20
    )
    
    subjects = CourseService.get_subjects()
    
    return render_template('courses/teachers/list.html',
                         teachers=teachers,
                         subjects=subjects,
                         current_subject_id=subject_id,
                         current_status=status)


@courses_bp.route('/teachers/create', methods=['GET', 'POST'])
@login_required
def teacher_create():
    """新增老师"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.teacher_list'))
    
    if request.method == 'POST':
        subject_ids = request.form.getlist('subject_ids')
        
        data = {
            'name': request.form.get('name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'subject_ids': ','.join(subject_ids),
            'daily_rate': request.form.get('daily_rate', type=float),
            'hourly_rate': request.form.get('hourly_rate', type=float),
            'id_card': request.form.get('id_card', '').strip(),
            'bank_account': request.form.get('bank_account', '').strip(),
            'bank_name': request.form.get('bank_name', '').strip(),
            'remark': request.form.get('remark', '').strip(),
        }
        
        if not data['name']:
            flash('姓名不能为空', 'danger')
        elif not data['phone']:
            flash('手机号不能为空', 'danger')
        elif not subject_ids:
            flash('请选择擅长科目', 'danger')
        else:
            try:
                teacher = TeacherService.create_teacher(data)
                flash(f'老师 "{teacher.name}" 添加成功！', 'success')
                return redirect(url_for('courses.teacher_list'))
            except Exception as e:
                flash(f'添加失败：{str(e)}', 'danger')
    
    subjects = CourseService.get_subjects()
    
    return render_template('courses/teachers/form.html',
                         teacher=None,
                         subjects=subjects)


@courses_bp.route('/teachers/<int:id>')
@login_required
def teacher_detail(id):
    """老师详情"""
    teacher = TeacherService.get_teacher(id)
    if not teacher:
        flash('老师不存在', 'danger')
        return redirect(url_for('courses.teacher_list'))
    
    # 获取排课记录
    schedules = TeacherService.get_teacher_schedules(id)
    
    # 计算本月工作量
    today = date.today()
    month_start = today.replace(day=1)
    month_end = (month_start.replace(month=month_start.month % 12 + 1, day=1) 
                 if month_start.month < 12 
                 else month_start.replace(year=month_start.year + 1, month=1, day=1)) - timedelta(days=1)
    
    workload = TeacherService.get_workload(id, month_start, month_end)
    
    return render_template('courses/teachers/detail.html',
                         teacher=teacher,
                         schedules=schedules,
                         workload=workload)


@courses_bp.route('/teachers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def teacher_edit(id):
    """编辑老师"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('courses.teacher_list'))
    
    teacher = TeacherService.get_teacher(id)
    if not teacher:
        flash('老师不存在', 'danger')
        return redirect(url_for('courses.teacher_list'))
    
    if request.method == 'POST':
        subject_ids = request.form.getlist('subject_ids')
        
        data = {
            'name': request.form.get('name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'subject_ids': ','.join(subject_ids),
            'daily_rate': request.form.get('daily_rate', type=float),
            'hourly_rate': request.form.get('hourly_rate', type=float),
            'id_card': request.form.get('id_card', '').strip(),
            'bank_account': request.form.get('bank_account', '').strip(),
            'bank_name': request.form.get('bank_name', '').strip(),
            'remark': request.form.get('remark', '').strip(),
        }
        
        try:
            TeacherService.update_teacher(id, data)
            flash('老师信息更新成功！', 'success')
            return redirect(url_for('courses.teacher_detail', id=id))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    subjects = CourseService.get_subjects()
    
    return render_template('courses/teachers/form.html',
                         teacher=teacher,
                         subjects=subjects)


@courses_bp.route('/teachers/<int:id>/toggle', methods=['POST'])
@login_required
def teacher_toggle(id):
    """切换老师状态"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        teacher = TeacherService.toggle_teacher_status(id)
        return jsonify({
            'success': True,
            'status': teacher.status,
            'message': f'老师已{"启用" if teacher.status == "active" else "停用"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/teachers/workload')
@login_required
def teacher_workload():
    """老师工作量统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 默认本月
    today = date.today()
    if not start_date:
        start_date = today.replace(day=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1) 
                   if start_date.month < 12 
                   else start_date.replace(year=start_date.year + 1, month=1, day=1)) - timedelta(days=1)
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    workloads = TeacherService.get_all_workload(start_date, end_date)
    
    return render_template('courses/teachers/workload.html',
                         workloads=workloads,
                         start_date=start_date,
                         end_date=end_date)


# ==================== API端点 ====================

@courses_bp.route('/api/check-teacher-conflict', methods=['POST'])
@login_required
def api_check_conflict():
    """检测老师时间冲突"""
    teacher_id = request.form.get('teacher_id', type=int)
    check_date = request.form.get('date')
    exclude_schedule_id = request.form.get('exclude_schedule_id', type=int)
    
    if not teacher_id or not check_date:
        return jsonify({'success': False, 'message': '参数不完整'})
    
    try:
        check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        result = TeacherService.check_conflict(teacher_id, check_date, exclude_schedule_id)
        
        schedules_info = []
        for s in result['schedules']:
            schedules_info.append({
                'batch_name': s.batch.name,
                'subject_name': s.subject.name if s.subject else '',
            })
        
        return jsonify({
            'success': True,
            'has_conflict': result['has_conflict'],
            'schedules': schedules_info
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/api/available-teachers')
@login_required
def api_available_teachers():
    """获取可用老师"""
    subject_id = request.args.get('subject_id', type=int)
    check_date = request.args.get('date')
    
    if not subject_id or not check_date:
        return jsonify([])
    
    try:
        check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        teachers = TeacherService.get_available_teachers(subject_id, check_date)
        
        return jsonify([{
            'id': t.id,
            'name': t.name
        } for t in teachers])
    except:
        return jsonify([])


@courses_bp.route('/api/packages/<int:project_id>')
@login_required
def api_packages(project_id):
    """获取项目套餐"""
    packages = CourseService.get_packages(project_id=project_id, status='active')
    return jsonify([p.to_dict() for p in packages])


@courses_bp.route('/api/types/<int:project_id>')
@login_required
def api_types(project_id):
    """获取项目班型"""
    class_types = CourseService.get_class_types(project_id, status='active')
    return jsonify([t.to_dict() for t in class_types])


@courses_bp.route('/api/batches/<int:type_id>')
@login_required
def api_batches(type_id):
    """获取班型班次"""
    batches = CourseService.get_all_batches(class_type_id=type_id, status='recruiting')
    return jsonify([b.to_dict() for b in batches])


# ==================== 课表管理API ====================

@courses_bp.route('/batches/<int:batch_id>/schedules', methods=['POST'])
@login_required
def schedule_create(batch_id):
    """添加单个课表"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        data = {
            'batch_id': batch_id,
            'schedule_date': datetime.strptime(request.form.get('schedule_date'), '%Y-%m-%d').date(),
            'day_number': request.form.get('day_number', type=int),
            'subject_id': request.form.get('subject_id', type=int),
            'morning_teacher_id': request.form.get('morning_teacher_id', type=int) or None,
            'afternoon_teacher_id': request.form.get('afternoon_teacher_id', type=int) or None,
            'evening_type': request.form.get('evening_type', 'self_study'),
            'evening_teacher_id': request.form.get('evening_teacher_id', type=int) or None,
            'remark': request.form.get('remark', '').strip(),
        }
        
        schedule = ScheduleService.create_schedule(data)
        return jsonify({
            'success': True,
            'schedule': schedule.to_dict(),
            'message': '课表添加成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/schedules/<int:id>', methods=['PUT', 'POST'])
@login_required
def schedule_update(id):
    """更新课表"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        data = {}
        
        if request.form.get('subject_id'):
            data['subject_id'] = request.form.get('subject_id', type=int)
        if 'morning_teacher_id' in request.form:
            data['morning_teacher_id'] = request.form.get('morning_teacher_id', type=int) or None
        if 'afternoon_teacher_id' in request.form:
            data['afternoon_teacher_id'] = request.form.get('afternoon_teacher_id', type=int) or None
        if 'evening_type' in request.form:
            data['evening_type'] = request.form.get('evening_type')
        if 'evening_teacher_id' in request.form:
            data['evening_teacher_id'] = request.form.get('evening_teacher_id', type=int) or None
        if 'remark' in request.form:
            data['remark'] = request.form.get('remark', '').strip()
        
        reason = request.form.get('reason', '').strip()
        
        schedule = ScheduleService.update_schedule(id, data, current_user.id, reason)
        return jsonify({
            'success': True,
            'schedule': schedule.to_dict(),
            'message': '课表更新成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/schedules/<int:id>/delete', methods=['POST'])
@login_required
def schedule_delete(id):
    """删除课表"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        ScheduleService.delete_schedule(id)
        return jsonify({'success': True, 'message': '课表已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/batches/<int:batch_id>/schedules/generate', methods=['POST'])
@login_required
def schedule_generate(batch_id):
    """批量生成课表"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    try:
        import json
        subject_days = json.loads(request.form.get('subject_days', '[]'))
        
        if not subject_days:
            return jsonify({'success': False, 'message': '请至少添加一个科目'})
        
        schedules = ScheduleService.generate_schedules(batch_id, subject_days)
        return jsonify({
            'success': True,
            'count': len(schedules),
            'message': f'成功生成 {len(schedules)} 天课表'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/batches/<int:batch_id>/schedules/import', methods=['POST'])
@login_required
def schedule_import(batch_id):
    """从Excel导入课表"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '请选择文件'})
    
    try:
        result = ScheduleService.import_from_excel(batch_id, file.read(), file.filename)
        
        message = f'导入完成: 成功 {result["success"]} 条'
        if result['failed'] > 0:
            message += f', 失败 {result["failed"]} 条'
        
        return jsonify({
            'success': True,
            'result': result,
            'message': message
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/batches/<int:batch_id>/schedules/copy', methods=['POST'])
@login_required
def schedule_copy(batch_id):
    """从其他班次复制课表"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    source_batch_id = request.form.get('source_batch_id', type=int)
    if not source_batch_id:
        return jsonify({'success': False, 'message': '请选择源班次'})
    
    try:
        schedules = ScheduleService.copy_from_batch(source_batch_id, batch_id)
        return jsonify({
            'success': True,
            'count': len(schedules),
            'message': f'成功复制 {len(schedules)} 天课表'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/batches/<int:batch_id>/schedules/export')
@login_required
def schedule_export(batch_id):
    """导出课表为Excel"""
    try:
        batch = CourseService.get_batch(batch_id)
        if not batch:
            flash('班次不存在', 'danger')
            return redirect(url_for('courses.batch_list'))
        
        output = ScheduleService.export_to_excel(batch_id)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{batch.name}_课表.xlsx'
        )
    except Exception as e:
        flash(f'导出失败: {str(e)}', 'danger')
        return redirect(url_for('courses.batch_detail', id=batch_id))


@courses_bp.route('/schedule-template')
@login_required
def schedule_template():
    """下载课表导入模板"""
    try:
        output = ScheduleService.get_schedule_template()
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='课表导入模板.xlsx'
        )
    except Exception as e:
        flash(f'下载失败: {str(e)}', 'danger')
        return redirect(url_for('courses.batch_list'))


@courses_bp.route('/change-logs')
@login_required
def change_log_list():
    """变更记录列表"""
    page = request.args.get('page', 1, type=int)
    batch_id = request.args.get('batch_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    
    logs = ScheduleService.get_change_logs(
        batch_id=batch_id,
        teacher_id=teacher_id,
        page=page,
        per_page=30
    )
    
    batches = ClassBatch.query.filter(ClassBatch.status != 'ended').order_by(ClassBatch.start_date.desc()).all()
    teachers = TeacherService.get_all_teachers()
    
    return render_template('courses/change_logs.html',
                         logs=logs,
                         batches=batches,
                         teachers=teachers,
                         current_batch_id=batch_id,
                         current_teacher_id=teacher_id)


# ==================== 考勤管理 ====================

@courses_bp.route('/batches/<int:batch_id>/attendance')
@login_required
def attendance_list(batch_id):
    """考勤管理页面"""
    batch = CourseService.get_batch(batch_id)
    if not batch:
        flash('班次不存在', 'danger')
        return redirect(url_for('courses.batch_list'))
    
    # 获取考勤统计
    try:
        stats = AttendanceService.get_batch_statistics(batch_id)
    except:
        stats = {'total_days': 0, 'recorded_days': 0, 'student_stats': []}
    
    # 获取课表
    schedules = ScheduleService.get_schedules(batch_id)
    
    # 获取学员
    students = CourseService.get_batch_students(batch_id)
    
    return render_template('courses/attendance/list.html',
                         batch=batch,
                         stats=stats,
                         schedules=schedules,
                         students=students)


@courses_bp.route('/batches/<int:batch_id>/attendance/record', methods=['GET', 'POST'])
@login_required
def attendance_record(batch_id):
    """记录考勤"""
    batch = CourseService.get_batch(batch_id)
    if not batch:
        flash('班次不存在', 'danger')
        return redirect(url_for('courses.batch_list'))
    
    schedule_id = request.args.get('schedule_id', type=int)
    attendance_date = request.args.get('date')
    
    if not schedule_id:
        # 如果没指定课表，默认今天
        today = date.today()
        schedule = ScheduleService.get_schedule_by_date(batch_id, today)
        if schedule:
            schedule_id = schedule.id
            attendance_date = today.strftime('%Y-%m-%d')
        else:
            flash('今日没有课程安排', 'warning')
            return redirect(url_for('courses.attendance_list', batch_id=batch_id))
    
    schedule = ScheduleService.get_schedule(schedule_id)
    if not schedule:
        flash('课表不存在', 'danger')
        return redirect(url_for('courses.attendance_list', batch_id=batch_id))
    
    if request.method == 'POST':
        # 批量保存考勤
        records = []
        for key in request.form:
            if key.startswith('status_'):
                student_id = int(key.replace('status_', ''))
                status = request.form.get(key)
                remark = request.form.get(f'remark_{student_id}', '')
                records.append({
                    'student_id': student_id,
                    'status': status,
                    'remark': remark
                })
        
        try:
            count = AttendanceService.batch_record_attendance(
                batch_id,
                schedule_id,
                schedule.schedule_date,
                records
            )
            flash(f'成功记录 {count} 人考勤', 'success')
            return redirect(url_for('courses.attendance_list', batch_id=batch_id))
        except Exception as e:
            flash(f'保存失败: {str(e)}', 'danger')
    
    # 获取学员列表
    students = CourseService.get_batch_students(batch_id)
    
    # 获取已有的考勤记录
    existing = {a.student_id: a for a in AttendanceService.get_attendance_by_date(batch_id, schedule.schedule_date)}
    
    return render_template('courses/attendance/record.html',
                         batch=batch,
                         schedule=schedule,
                         students=students,
                         existing=existing)


@courses_bp.route('/api/attendance/daily-summary')
@login_required
def api_attendance_summary():
    """获取某天的考勤汇总"""
    batch_id = request.args.get('batch_id', type=int)
    attendance_date = request.args.get('date')
    
    if not batch_id or not attendance_date:
        return jsonify({'success': False, 'message': '参数不完整'})
    
    try:
        attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        summary = AttendanceService.get_daily_summary(batch_id, attendance_date)
        return jsonify({'success': True, 'data': summary})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 录播管理 ====================

@courses_bp.route('/recordings')
@login_required
def recording_list():
    """录播列表"""
    page = request.args.get('page', 1, type=int)
    batch_id = request.args.get('batch_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    
    recordings = RecordingService.get_recordings(
        batch_id=batch_id,
        subject_id=subject_id,
        page=page,
        per_page=20
    )
    
    batches = RecordingService.get_all_batches()
    subjects = RecordingService.get_subjects()
    
    return render_template('courses/recordings/list.html',
                         recordings=recordings,
                         batches=batches,
                         subjects=subjects,
                         current_batch_id=batch_id,
                         current_subject_id=subject_id)


@courses_bp.route('/recordings/create', methods=['GET', 'POST'])
@login_required
def recording_create():
    """新增录播"""
    batch_id = request.args.get('batch_id', type=int)
    
    if request.method == 'POST':
        batch_id = request.form.get('batch_id', type=int)
        
        data = {
            'batch_id': batch_id,
            'recording_date': datetime.strptime(request.form.get('recording_date'), '%Y-%m-%d').date(),
            'period': request.form.get('period', 'morning'),
            'title': request.form.get('title', '').strip(),
            'recording_url': request.form.get('recording_url', '').strip(),
            'subject_id': request.form.get('subject_id', type=int) or None,
            'teacher_id': request.form.get('teacher_id', type=int) or None,
            'duration_minutes': request.form.get('duration_minutes', type=int) or None,
            'remark': request.form.get('remark', '').strip(),
        }
        
        if not data['batch_id']:
            flash('请选择班次', 'danger')
        elif not data['title']:
            flash('录播标题不能为空', 'danger')
        elif not data['recording_url']:
            flash('录播链接不能为空', 'danger')
        else:
            try:
                recording = RecordingService.create_recording(data, current_user.id)
                flash(f'录播 "{recording.title}" 添加成功！', 'success')
                
                # 返回来源页面
                return_to = request.form.get('return_to', '')
                if return_to == 'batch' and batch_id:
                    return redirect(url_for('courses.batch_detail', id=batch_id) + '#recordings')
                return redirect(url_for('courses.recording_list'))
            except Exception as e:
                flash(f'添加失败：{str(e)}', 'danger')
    
    batches = RecordingService.get_all_batches()
    subjects = RecordingService.get_subjects()
    teachers = RecordingService.get_teachers()
    
    current_batch = None
    if batch_id:
        current_batch = CourseService.get_batch(batch_id)
    
    return render_template('courses/recordings/form.html',
                         recording=None,
                         batches=batches,
                         subjects=subjects,
                         teachers=teachers,
                         current_batch=current_batch)


@courses_bp.route('/recordings/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def recording_edit(id):
    """编辑录播"""
    recording = RecordingService.get_recording(id)
    if not recording:
        flash('录播记录不存在', 'danger')
        return redirect(url_for('courses.recording_list'))
    
    if request.method == 'POST':
        data = {
            'recording_date': datetime.strptime(request.form.get('recording_date'), '%Y-%m-%d').date(),
            'period': request.form.get('period', 'morning'),
            'title': request.form.get('title', '').strip(),
            'recording_url': request.form.get('recording_url', '').strip(),
            'subject_id': request.form.get('subject_id', type=int) or None,
            'teacher_id': request.form.get('teacher_id', type=int) or None,
            'duration_minutes': request.form.get('duration_minutes', type=int) or None,
            'remark': request.form.get('remark', '').strip(),
        }
        
        try:
            RecordingService.update_recording(id, data)
            flash('录播更新成功！', 'success')
            
            return_to = request.form.get('return_to', '')
            if return_to == 'batch':
                return redirect(url_for('courses.batch_detail', id=recording.batch_id) + '#recordings')
            return redirect(url_for('courses.recording_list'))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    batches = RecordingService.get_all_batches()
    subjects = RecordingService.get_subjects()
    teachers = RecordingService.get_teachers()
    
    return render_template('courses/recordings/form.html',
                         recording=recording,
                         batches=batches,
                         subjects=subjects,
                         teachers=teachers,
                         current_batch=recording.batch)


@courses_bp.route('/recordings/<int:id>/delete', methods=['POST'])
@login_required
def recording_delete(id):
    """删除录播"""
    try:
        recording = RecordingService.get_recording(id)
        batch_id = recording.batch_id if recording else None
        
        RecordingService.delete_recording(id)
        
        # 判断返回位置
        return_to = request.form.get('return_to', '')
        if return_to == 'batch' and batch_id:
            flash('录播已删除', 'success')
            return jsonify({'success': True, 'redirect': url_for('courses.batch_detail', id=batch_id) + '#recordings'})
        
        return jsonify({'success': True, 'message': '录播已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@courses_bp.route('/batches/<int:batch_id>/recordings')
@login_required
def batch_recordings(batch_id):
    """班次录播列表（JSON）"""
    recordings = RecordingService.get_recordings_by_batch(batch_id)
    return jsonify([r.to_dict() for r in recordings])
