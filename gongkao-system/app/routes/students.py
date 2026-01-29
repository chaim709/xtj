"""
学员管理路由 - 学员CRUD和搜索
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.student import Student
from app.models.user import User
from app.services.student_service import StudentService
from app.services.tag_service import TagService

students_bp = Blueprint('students', __name__)


@students_bp.route('/')
@login_required
def list():
    """学员列表"""
    # 获取筛选参数
    filters = {
        'search': request.args.get('search', ''),
        'class_name': request.args.get('class_name', ''),
        'exam_type': request.args.get('exam_type', ''),
        'need_attention': request.args.get('need_attention', '') == '1',
    }
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 权限控制：督学人员只能看自己负责的学员
    supervisor_id = None if current_user.is_admin() else current_user.id
    
    # 搜索学员
    pagination = StudentService.search_students(
        filters=filters,
        supervisor_id=supervisor_id,
        page=page,
        per_page=per_page
    )
    
    # 获取班次选项（用于筛选）
    class_options = db.session.query(Student.class_name).filter(
        Student.class_name.isnot(None),
        Student.status == 'active'
    ).distinct().all()
    class_options = [c[0] for c in class_options if c[0]]
    
    return render_template('students/list.html',
                         students=pagination.items,
                         pagination=pagination,
                         filters=filters,
                         class_options=class_options)


@students_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """新增学员"""
    if request.method == 'POST':
        from decimal import Decimal
        
        # 获取表单数据
        data = {
            'name': request.form.get('name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'wechat': request.form.get('wechat', '').strip(),
            'class_name': request.form.get('class_name', '').strip(),
            'exam_type': request.form.get('exam_type', '').strip(),
            'target_position': request.form.get('target_position', '').strip(),
            'has_basic': request.form.get('has_basic') == 'on',
            'is_agreement': request.form.get('is_agreement') == 'on',
            'base_level': request.form.get('base_level', '').strip(),
            'learning_style': request.form.get('learning_style', '').strip(),
            'study_plan': request.form.get('study_plan', '').strip(),
            'education': request.form.get('education', '').strip(),
            'id_number': request.form.get('id_number', '').strip(),
            'address': request.form.get('address', '').strip(),
            'parent_phone': request.form.get('parent_phone', '').strip(),
            'emergency_contact': request.form.get('emergency_contact', '').strip(),
            'supervisor_id': request.form.get('supervisor_id', type=int),
            'payment_status': request.form.get('payment_status', '').strip(),
            'remarks': request.form.get('remarks', '').strip(),
            # 课程相关字段
            'package_id': request.form.get('package_id', type=int) or None,
            'discount_info': request.form.get('discount_info', '').strip(),
        }
        
        # 处理实付金额
        actual_price = request.form.get('actual_price')
        if actual_price:
            try:
                data['actual_price'] = Decimal(actual_price)
            except:
                pass
        
        # 处理入学日期
        enrollment_date = request.form.get('enrollment_date', '')
        if enrollment_date:
            try:
                data['enrollment_date'] = datetime.strptime(enrollment_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 处理课程报名日期
        course_enrollment_date = request.form.get('course_enrollment_date', '')
        if course_enrollment_date:
            try:
                data['course_enrollment_date'] = datetime.strptime(course_enrollment_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 处理有效期
        valid_until = request.form.get('valid_until', '')
        if valid_until:
            try:
                data['valid_until'] = datetime.strptime(valid_until, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 验证
        if not data['name']:
            flash('姓名不能为空', 'danger')
            return render_template('students/form.html', student=None, **get_form_options(None))
        
        # 创建学员
        try:
            student = StudentService.create_student(data)
            flash(f'学员 {student.name} 创建成功！', 'success')
            return redirect(url_for('students.detail', id=student.id))
        except Exception as e:
            flash(f'创建失败：{str(e)}', 'danger')
            return render_template('students/form.html', student=None, **get_form_options(None))
    
    return render_template('students/form.html', student=None, **get_form_options(None))


@students_bp.route('/<int:id>')
@login_required
def detail(id):
    """学员详情"""
    student = StudentService.get_student(id)
    if not student:
        flash('学员不存在', 'danger')
        return redirect(url_for('students.list'))
    
    # 权限检查
    if not current_user.is_admin() and student.supervisor_id != current_user.id:
        flash('您没有权限查看该学员', 'danger')
        return redirect(url_for('students.list'))
    
    # 第三阶段新增：获取增强数据
    enhanced_data = get_student_enhanced_data(id)
    
    # 获取学员所在班次的录播
    from app.services.recording_service import RecordingService
    recordings = RecordingService.get_recordings_by_student(id)
    
    return render_template('students/detail.html', 
                          student=student, 
                          enhanced_data=enhanced_data,
                          recordings=recordings)


def get_student_enhanced_data(student_id):
    """
    获取学员增强数据（课程进度、督学汇总、考勤统计）
    
    Args:
        student_id: 学员ID
    
    Returns:
        增强数据字典
    """
    from app.models.supervision import SupervisionLog
    from app.models.course import StudentBatch, Attendance, Schedule
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # 督学汇总
    total_logs = SupervisionLog.query.filter_by(student_id=student_id).count()
    
    # 最近30天督学记录数
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_logs = SupervisionLog.query.filter(
        SupervisionLog.student_id == student_id,
        SupervisionLog.created_at >= thirty_days_ago
    ).count()
    
    # 最后一次督学
    last_log = SupervisionLog.query.filter_by(
        student_id=student_id
    ).order_by(SupervisionLog.created_at.desc()).first()
    
    # 心态分布
    mood_stats = db.session.query(
        SupervisionLog.student_mood,
        func.count(SupervisionLog.id)
    ).filter(
        SupervisionLog.student_id == student_id,
        SupervisionLog.student_mood.isnot(None)
    ).group_by(SupervisionLog.student_mood).all()
    
    mood_distribution = {m[0]: m[1] for m in mood_stats}
    
    # 班次信息
    student_batches = StudentBatch.query.filter_by(
        student_id=student_id,
        status='active'
    ).all()
    
    batch_info = []
    for sb in student_batches:
        if sb.batch:
            batch_info.append({
                'id': sb.batch.id,
                'name': sb.batch.name,
                'status': sb.batch.status,
                'progress_day': sb.progress_day,
                'enroll_time': sb.enroll_time,
                'total_days': sb.batch.actual_days or 0
            })
    
    # 考勤统计（通过班次关联）
    attendance_stats = {'present': 0, 'absent': 0, 'late': 0, 'leave': 0, 'total': 0}
    
    for sb in student_batches:
        if sb.batch:
            # 获取该班次的所有课程安排
            schedule_ids = [s.id for s in Schedule.query.filter_by(batch_id=sb.batch.id).all()]
            if schedule_ids:
                records = Attendance.query.filter(
                    Attendance.student_id == student_id,
                    Attendance.schedule_id.in_(schedule_ids)
                ).all()
                
                for r in records:
                    attendance_stats['total'] += 1
                    if r.status in attendance_stats:
                        attendance_stats[r.status] += 1
    
    # 计算出勤率
    if attendance_stats['total'] > 0:
        attendance_stats['rate'] = round(
            (attendance_stats['present'] + attendance_stats['late']) / attendance_stats['total'] * 100, 1
        )
    else:
        attendance_stats['rate'] = 0
    
    return {
        'supervision': {
            'total_logs': total_logs,
            'recent_logs': recent_logs,
            'last_log': last_log,
            'mood_distribution': mood_distribution
        },
        'batches': batch_info,
        'attendance': attendance_stats
    }


@students_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑学员"""
    student = StudentService.get_student(id)
    if not student:
        flash('学员不存在', 'danger')
        return redirect(url_for('students.list'))
    
    # 权限检查
    if not current_user.is_admin() and student.supervisor_id != current_user.id:
        flash('您没有权限编辑该学员', 'danger')
        return redirect(url_for('students.list'))
    
    if request.method == 'POST':
        from decimal import Decimal
        
        # 获取表单数据
        data = {
            'name': request.form.get('name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'wechat': request.form.get('wechat', '').strip(),
            'class_name': request.form.get('class_name', '').strip(),
            'exam_type': request.form.get('exam_type', '').strip(),
            'target_position': request.form.get('target_position', '').strip(),
            'has_basic': request.form.get('has_basic') == 'on',
            'is_agreement': request.form.get('is_agreement') == 'on',
            'base_level': request.form.get('base_level', '').strip(),
            'learning_style': request.form.get('learning_style', '').strip(),
            'study_plan': request.form.get('study_plan', '').strip(),
            'education': request.form.get('education', '').strip(),
            'id_number': request.form.get('id_number', '').strip(),
            'address': request.form.get('address', '').strip(),
            'parent_phone': request.form.get('parent_phone', '').strip(),
            'emergency_contact': request.form.get('emergency_contact', '').strip(),
            'supervisor_id': request.form.get('supervisor_id', type=int),
            'payment_status': request.form.get('payment_status', '').strip(),
            'remarks': request.form.get('remarks', '').strip(),
            'need_attention': request.form.get('need_attention') == 'on',
            # 课程相关字段
            'package_id': request.form.get('package_id', type=int) or None,
            'discount_info': request.form.get('discount_info', '').strip(),
        }
        
        # 处理实付金额
        actual_price = request.form.get('actual_price')
        if actual_price:
            try:
                data['actual_price'] = Decimal(actual_price)
            except:
                data['actual_price'] = None
        else:
            data['actual_price'] = None
        
        # 处理入学日期
        enrollment_date = request.form.get('enrollment_date', '')
        if enrollment_date:
            try:
                data['enrollment_date'] = datetime.strptime(enrollment_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 处理课程报名日期
        course_enrollment_date = request.form.get('course_enrollment_date', '')
        if course_enrollment_date:
            try:
                data['course_enrollment_date'] = datetime.strptime(course_enrollment_date, '%Y-%m-%d').date()
            except ValueError:
                data['course_enrollment_date'] = None
        else:
            data['course_enrollment_date'] = None
        
        # 处理有效期
        valid_until = request.form.get('valid_until', '')
        if valid_until:
            try:
                data['valid_until'] = datetime.strptime(valid_until, '%Y-%m-%d').date()
            except ValueError:
                data['valid_until'] = None
        else:
            data['valid_until'] = None
        
        # 验证
        if not data['name']:
            flash('姓名不能为空', 'danger')
            return render_template('students/form.html', student=student, **get_form_options(student))
        
        # 更新学员
        try:
            StudentService.update_student(id, data)
            flash('学员信息更新成功！', 'success')
            return redirect(url_for('students.detail', id=id))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
            return render_template('students/form.html', student=student, **get_form_options(student))
    
    return render_template('students/form.html', student=student, **get_form_options(student))


@students_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除学员"""
    student = StudentService.get_student(id)
    if not student:
        flash('学员不存在', 'danger')
        return redirect(url_for('students.list'))
    
    # 权限检查：只有管理员可以删除
    if not current_user.is_admin():
        flash('您没有权限删除学员', 'danger')
        return redirect(url_for('students.list'))
    
    try:
        name = student.name
        StudentService.delete_student(id)
        flash(f'学员 {name} 已删除', 'success')
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('students.list'))


@students_bp.route('/<int:id>/toggle-attention', methods=['POST'])
@login_required
def toggle_attention(id):
    """切换关注状态"""
    student = StudentService.get_student(id)
    if not student:
        return jsonify({'success': False, 'message': '学员不存在'})
    
    try:
        new_status = not student.need_attention
        StudentService.mark_attention(id, new_status)
        return jsonify({
            'success': True,
            'need_attention': new_status,
            'message': '已标记为重点关注' if new_status else '已取消重点关注'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def get_supervisors():
    """获取所有督学人员列表"""
    return User.query.filter(User.role.in_(['admin', 'supervisor']), User.status == 'active').all()


def get_form_options(student=None):
    """
    获取表单选项
    
    Args:
        student: 学员对象（用于获取已选套餐的项目套餐列表）
    
    Returns:
        dict: 表单选项数据
    """
    from config import Config
    from app.services.course_service import CourseService
    
    # 获取招生项目
    projects = CourseService.get_all_projects(status='recruiting')
    
    # 如果学员已有套餐，加载该项目的套餐列表
    packages = []
    if student and student.package_id and student.package:
        packages = CourseService.get_packages(
            project_id=student.package.project_id, 
            status='active'
        )
    
    return {
        'supervisors': get_supervisors(),
        'class_options': Config.CLASS_OPTIONS,
        'exam_type_options': Config.EXAM_TYPE_OPTIONS,
        'projects': projects,
        'packages': packages,
    }


# ==================== 标签管理 ====================

@students_bp.route('/<int:id>/tags', methods=['GET'])
@login_required
def get_tags(id):
    """获取学员的所有标签"""
    student = StudentService.get_student(id)
    if not student:
        return jsonify({'success': False, 'message': '学员不存在'})
    
    tags = TagService.get_tags_by_student(id)
    return jsonify({
        'success': True,
        'tags': [tag.to_dict() for tag in tags]
    })


@students_bp.route('/<int:id>/tags', methods=['POST'])
@login_required
def add_tag(id):
    """添加标签"""
    student = StudentService.get_student(id)
    if not student:
        return jsonify({'success': False, 'message': '学员不存在'})
    
    # 权限检查
    if not current_user.is_admin() and student.supervisor_id != current_user.id:
        return jsonify({'success': False, 'message': '您没有权限操作该学员'})
    
    data = request.get_json() or request.form
    module = data.get('module', '').strip()
    sub_module = data.get('sub_module', '').strip() if data.get('sub_module') else None
    level = data.get('level', '').strip() if data.get('level') else None
    
    # 处理正确率
    accuracy_rate = None
    if 'accuracy_rate' in data:
        try:
            accuracy_rate = float(data.get('accuracy_rate'))
        except (TypeError, ValueError):
            pass
    
    if not module:
        return jsonify({'success': False, 'message': '请选择模块'})
    
    try:
        tag = TagService.add_tag(
            student_id=id,
            module=module,
            sub_module=sub_module,
            accuracy_rate=accuracy_rate,
            level=level
        )
        return jsonify({
            'success': True,
            'tag': tag.to_dict(),
            'message': '标签添加成功'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'添加标签失败: {str(e)}'})


@students_bp.route('/<int:student_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(student_id, tag_id):
    """删除标签"""
    try:
        success = TagService.delete_tag(tag_id)
        if success:
            return jsonify({'success': True, 'message': '标签已删除'})
        else:
            return jsonify({'success': False, 'message': '标签不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@students_bp.route('/modules', methods=['GET'])
@login_required
def get_modules():
    """获取模块分类"""
    modules = TagService.get_modules()
    return jsonify({
        'success': True,
        'modules': modules
    })
