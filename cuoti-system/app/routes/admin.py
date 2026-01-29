# -*- coding: utf-8 -*-
"""管理后台路由"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Admin, Question, Workbook, WorkbookItem, WorkbookPage, Student, Submission, Mistake, Institution, WorkbookTemplate, StudentClass
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_DOC_EXTENSIONS = {'docx', 'pdf', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_doc_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS


# ==================== 认证 ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        
        flash('用户名或密码错误', 'error')
    
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('admin.login'))


# ==================== 仪表盘 ====================

@admin_bp.route('/')
@login_required
def dashboard():
    """仪表盘"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    stats = {
        'total_questions': Question.query.count(),
        'total_workbooks': Workbook.query.count(),
        'total_students': Student.query.count(),
        'total_mistakes': Mistake.query.count()
    }
    
    # 今日统计
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_stats = {
        'submissions': Submission.query.filter(Submission.created_at >= today_start).count(),
        'students': db.session.query(func.count(func.distinct(Submission.student_id))).filter(
            Submission.created_at >= today_start
        ).scalar() or 0,
        'mistakes': Mistake.query.filter(Mistake.created_at >= today_start).count()
    }
    
    # 最近提交
    recent_submissions = Submission.query.order_by(Submission.created_at.desc()).limit(10).all()
    
    # 最近题册
    recent_workbooks = Workbook.query.order_by(Workbook.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          stats=stats,
                          today_stats=today_stats,
                          recent_submissions=recent_submissions,
                          recent_workbooks=recent_workbooks)


# ==================== 题目管理 ====================

@admin_bp.route('/questions')
@login_required
def questions():
    """题目列表"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    
    query = Question.query
    
    if category:
        query = query.filter(Question.category == category)
    if keyword:
        query = query.filter(Question.stem.contains(keyword))
    
    pagination = query.order_by(Question.id.desc()).paginate(page=page, per_page=20)
    
    # 获取所有分类
    categories = db.session.query(Question.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('admin/questions.html',
                          pagination=pagination,
                          categories=categories,
                          current_category=category,
                          keyword=keyword)


@admin_bp.route('/questions/create', methods=['GET', 'POST'])
@login_required
def create_question():
    """创建题目"""
    if request.method == 'POST':
        # 生成UID
        count = Question.query.count() + 1
        uid = f'Q-{str(count).zfill(5)}'
        
        question = Question(
            uid=uid,
            stem=request.form.get('stem'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            answer=request.form.get('answer'),
            analysis=request.form.get('analysis'),
            category=request.form.get('category'),
            subcategory=request.form.get('subcategory'),
            knowledge_point=request.form.get('knowledge_point'),
            source=request.form.get('source'),
            difficulty=request.form.get('difficulty', '中等')
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('题目创建成功', 'success')
        return redirect(url_for('admin.questions'))
    
    return render_template('admin/question_form.html', question=None)


@admin_bp.route('/questions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    """编辑题目"""
    question = Question.query.get_or_404(id)
    
    if request.method == 'POST':
        question.stem = request.form.get('stem')
        question.option_a = request.form.get('option_a')
        question.option_b = request.form.get('option_b')
        question.option_c = request.form.get('option_c')
        question.option_d = request.form.get('option_d')
        question.answer = request.form.get('answer')
        question.analysis = request.form.get('analysis')
        question.category = request.form.get('category')
        question.subcategory = request.form.get('subcategory')
        question.knowledge_point = request.form.get('knowledge_point')
        question.source = request.form.get('source')
        question.difficulty = request.form.get('difficulty', '中等')
        
        db.session.commit()
        
        flash('题目更新成功', 'success')
        return redirect(url_for('admin.questions'))
    
    return render_template('admin/question_form.html', question=question)


@admin_bp.route('/questions/<int:id>/delete', methods=['POST'])
@login_required
def delete_question(id):
    """删除题目"""
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    
    flash('题目已删除', 'success')
    return redirect(url_for('admin.questions'))


# ==================== 题册管理 ====================

@admin_bp.route('/workbooks')
@login_required
def workbooks():
    """题册列表"""
    page = request.args.get('page', 1, type=int)
    pagination = Workbook.query.order_by(Workbook.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/workbooks.html', pagination=pagination)


@admin_bp.route('/workbooks/create', methods=['GET', 'POST'])
@login_required
def create_workbook():
    """创建题册"""
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        template = WorkbookTemplate.query.get(template_id) if template_id else WorkbookTemplate.get_default()
        
        workbook = Workbook(
            name=request.form.get('name'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            template_id=template.id if template else None,
            questions_per_page=template.questions_per_page if template else 5,
            answer_mode=template.answer_mode if template else 'hidden'
        )
        
        db.session.add(workbook)
        db.session.commit()
        
        flash('题册创建成功，请添加题目', 'success')
        return redirect(url_for('admin.edit_workbook', id=workbook.id))
    
    templates = WorkbookTemplate.query.all()
    if not templates:
        # 确保有默认模板
        WorkbookTemplate.get_default()
        templates = WorkbookTemplate.query.all()
    
    return render_template('admin/workbook_form.html', workbook=None, templates=templates)


@admin_bp.route('/workbooks/<int:id>')
@login_required
def view_workbook(id):
    """查看题册"""
    workbook = Workbook.query.get_or_404(id)
    items = workbook.items.all()
    
    return render_template('admin/workbook_view.html', workbook=workbook, items=items)


@admin_bp.route('/workbooks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_workbook(id):
    """编辑题册"""
    workbook = Workbook.query.get_or_404(id)
    
    if request.method == 'POST':
        workbook.name = request.form.get('name')
        workbook.description = request.form.get('description')
        workbook.category = request.form.get('category')
        
        template_id = request.form.get('template_id')
        if template_id:
            template = WorkbookTemplate.query.get(template_id)
            if template:
                workbook.template_id = template.id
                workbook.questions_per_page = template.questions_per_page
                workbook.answer_mode = template.answer_mode
        
        db.session.commit()
        
        flash('题册更新成功', 'success')
        return redirect(url_for('admin.view_workbook', id=id))
    
    # 获取已添加的题目
    items = workbook.items.all()
    
    # 获取可添加的题目
    added_ids = [item.question_id for item in items]
    available_questions = Question.query.filter(~Question.id.in_(added_ids) if added_ids else True).limit(100).all()
    
    templates = WorkbookTemplate.query.all()
    
    return render_template('admin/workbook_edit.html', 
                          workbook=workbook, 
                          items=items,
                          available_questions=available_questions,
                          templates=templates)


@admin_bp.route('/workbooks/<int:id>/add_questions', methods=['POST'])
@login_required
def add_questions_to_workbook(id):
    """添加题目到题册"""
    workbook = Workbook.query.get_or_404(id)
    question_ids = request.form.getlist('question_ids')
    
    current_order = workbook.items.count()
    
    for qid in question_ids:
        current_order += 1
        item = WorkbookItem(
            workbook_id=workbook.id,
            question_id=int(qid),
            order=current_order
        )
        db.session.add(item)
    
    workbook.total_questions = current_order
    db.session.commit()
    
    flash(f'已添加 {len(question_ids)} 道题目', 'success')
    return redirect(url_for('admin.edit_workbook', id=id))


@admin_bp.route('/workbooks/<int:id>/remove_question/<int:item_id>', methods=['POST'])
@login_required
def remove_question_from_workbook(id, item_id):
    """从题册移除题目"""
    item = WorkbookItem.query.get_or_404(item_id)
    
    if item.workbook_id != id:
        flash('操作无效', 'error')
        return redirect(url_for('admin.edit_workbook', id=id))
    
    db.session.delete(item)
    
    # 重新排序
    workbook = Workbook.query.get(id)
    items = workbook.items.order_by(WorkbookItem.order).all()
    for i, item in enumerate(items, 1):
        item.order = i
    
    workbook.total_questions = len(items)
    db.session.commit()
    
    flash('题目已移除', 'success')
    return redirect(url_for('admin.edit_workbook', id=id))


@admin_bp.route('/workbooks/<int:id>/generate', methods=['POST'])
@login_required
def generate_workbook(id):
    """生成题册PDF"""
    workbook = Workbook.query.get_or_404(id)
    
    # 检查是否需要嵌入图片模式
    embed_mode = request.form.get('embed_mode', 'standard')
    
    try:
        if embed_mode == 'fullpage':
            # 整页嵌入模式（适用于图形推理等图片题）
            from app.utils.image_workbook_generator import generate_full_page_workbook
            images_dir = os.path.join(current_app.root_path, '..', 'data/parsed/图形推理700题/images')
            pdf_path = generate_full_page_workbook(workbook, images_dir)
        elif embed_mode == 'cropped':
            # 裁剪嵌入模式
            from app.utils.image_workbook_generator import generate_image_workbook_pdf
            pdf_path = generate_image_workbook_pdf(workbook, embed_images=True)
        elif embed_mode == 'by_category':
            # 按分类生成模式（每个分类一个二维码）
            from app.utils.generator import generate_workbook_pdf_by_category
            pdf_path = generate_workbook_pdf_by_category(workbook)
        elif embed_mode == 'single_qr':
            # 单二维码模式（整本题册一个二维码）
            from app.utils.generator import generate_workbook_pdf_single_qr
            pdf_path = generate_workbook_pdf_single_qr(workbook)
        elif embed_mode.startswith('enhance_'):
            # 增强模式：在原PDF/Word上添加封面和二维码
            from app.utils.generator import enhance_existing_pdf
            
            # 优先处理上传的文件
            uploaded_file = request.files.get('source_file')
            source_file = request.form.get('source_pdf', '')
            
            if uploaded_file and uploaded_file.filename:
                # 处理上传的文件
                filename = uploaded_file.filename
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext not in ('pdf', 'doc', 'docx'):
                    raise ValueError("仅支持 PDF、DOC、DOCX 格式的文件")
                
                # 保存上传的文件
                upload_dir = os.path.join(current_app.root_path, '..', 'data/uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                # 使用安全文件名 + UUID避免覆盖
                safe_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(filename)}"
                source_file = os.path.join(upload_dir, safe_name)
                uploaded_file.save(source_file)
            elif not source_file or not os.path.exists(source_file):
                raise ValueError("请上传文件或指定有效的原始文件路径")
            
            # 解析二维码模式
            qr_mode_map = {
                'enhance_single': 'single',
                'enhance_standard': 'standard',
                'enhance_category': 'by_category'
            }
            qr_mode = qr_mode_map.get(embed_mode, 'single')
            
            # 解析分类范围（如果有）
            category_ranges = None
            cat_ranges_str = request.form.get('category_ranges', '')
            if cat_ranges_str and qr_mode == 'by_category':
                try:
                    import json
                    category_ranges = json.loads(cat_ranges_str)
                except:
                    pass
            
            pdf_path = enhance_existing_pdf(source_file, workbook, qr_mode=qr_mode, category_ranges=category_ranges)
        else:
            # 标准模式
            from app.utils.generator import generate_workbook_pdf
            pdf_path = generate_workbook_pdf(workbook)
        
        workbook.pdf_path = pdf_path
        db.session.commit()
        
        flash('题册PDF已生成', 'success')
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'生成失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.view_workbook', id=id))


@admin_bp.route('/workbooks/<int:id>/download')
@login_required
def download_workbook(id):
    """下载题册PDF"""
    workbook = Workbook.query.get_or_404(id)
    
    if not workbook.pdf_path or not os.path.exists(workbook.pdf_path):
        flash('请先生成PDF', 'error')
        return redirect(url_for('admin.view_workbook', id=id))
    
    return send_file(workbook.pdf_path, as_attachment=True, 
                    download_name=f'{workbook.name}.pdf')


@admin_bp.route('/workbooks/<int:id>/delete', methods=['POST'])
@login_required
def delete_workbook(id):
    """删除题册"""
    workbook = Workbook.query.get_or_404(id)
    
    # 删除关联数据
    WorkbookItem.query.filter_by(workbook_id=id).delete()
    WorkbookPage.query.filter_by(workbook_id=id).delete()
    
    db.session.delete(workbook)
    db.session.commit()
    
    flash('题册已删除', 'success')
    return redirect(url_for('admin.workbooks'))


# ==================== 学员管理 ====================

@admin_bp.route('/students')
@login_required
def students():
    """学员列表"""
    page = request.args.get('page', 1, type=int)
    pagination = Student.query.order_by(Student.created_at.desc()).paginate(page=page, per_page=20)
    
    # 获取每个学员的最后提交记录
    student_last_subs = {}
    for s in pagination.items:
        last_sub = Submission.query.filter_by(student_id=s.id).order_by(Submission.created_at.desc()).first()
        student_last_subs[s.id] = last_sub
    
    return render_template('admin/students.html', pagination=pagination, student_last_subs=student_last_subs)


@admin_bp.route('/students/<int:id>')
@login_required
def view_student(id):
    """查看学员错题"""
    student = Student.query.get_or_404(id)
    
    # 获取提交记录
    submissions = Submission.query.filter_by(student_id=id).order_by(Submission.created_at.desc()).all()
    
    # 获取错题
    mistakes = Mistake.query.filter_by(student_id=id).order_by(Mistake.created_at.desc()).all()
    
    # 按分类统计
    category_stats = db.session.query(
        Question.category,
        db.func.count(Mistake.id)
    ).join(Mistake).filter(Mistake.student_id == id).group_by(Question.category).all()
    
    return render_template('admin/student_view.html', 
                          student=student,
                          submissions=submissions,
                          mistakes=mistakes,
                          category_stats=category_stats)


@admin_bp.route('/students/<int:id>/download_mistakes')
@login_required
def download_mistake_book(id):
    """下载学员错题本PDF"""
    from app.utils.report_generator import generate_mistake_book_pdf
    
    student = Student.query.get_or_404(id)
    mistakes = Mistake.query.filter_by(student_id=id).order_by(Mistake.created_at.desc()).all()
    institution = Institution.get_instance()
    
    if not mistakes:
        flash('该学员暂无错题记录', 'warning')
        return redirect(url_for('admin.view_student', id=id))
    
    try:
        filepath = generate_mistake_book_pdf(student, mistakes, institution)
        return send_file(filepath, as_attachment=True,
                        download_name=f'错题本_{student.name}.pdf')
    except Exception as e:
        flash(f'生成失败: {str(e)}', 'error')
        return redirect(url_for('admin.view_student', id=id))


@admin_bp.route('/students/<int:id>/download_report')
@login_required
def download_learning_report(id):
    """下载学员学习分析报告PDF"""
    from app.utils.report_generator import generate_student_report
    
    student = Student.query.get_or_404(id)
    period = request.args.get('period', 'all')  # 支持时间范围筛选
    
    try:
        filepath = generate_student_report(id, period)
        return send_file(filepath, as_attachment=True,
                        download_name=f'学习报告_{student.name}.pdf')
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'生成失败: {str(e)}', 'error')
        return redirect(url_for('admin.view_student', id=id))


@admin_bp.route('/students/<int:id>/stats')
@login_required
def student_stats_api(id):
    """获取学员统计数据API"""
    from app.utils.stats import StudentStatsService
    
    period = request.args.get('period', 'all')
    stats_service = StudentStatsService(id)
    
    return jsonify({
        'success': True,
        'data': stats_service.get_full_report_data(period)
    })


# ==================== 班级管理 ====================

@admin_bp.route('/classes')
@login_required
def classes():
    """班级列表"""
    classes = StudentClass.query.order_by(StudentClass.created_at.desc()).all()
    return render_template('admin/classes.html', classes=classes)


@admin_bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
def create_class():
    """创建班级"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        teacher = request.form.get('teacher', '').strip()
        
        if not name:
            flash('班级名称不能为空', 'error')
            return redirect(url_for('admin.create_class'))
        
        new_class = StudentClass(
            name=name,
            description=description,
            teacher=teacher
        )
        db.session.add(new_class)
        db.session.commit()
        
        flash(f'班级 "{name}" 创建成功', 'success')
        return redirect(url_for('admin.classes'))
    
    return render_template('admin/class_form.html', class_obj=None)


@admin_bp.route('/classes/<int:id>')
@login_required
def view_class(id):
    """班级详情"""
    from sqlalchemy import func
    
    class_obj = StudentClass.query.get_or_404(id)
    students = class_obj.students.all()
    
    # 计算班级统计
    class_stats = db.session.query(
        func.sum(Submission.total_attempted).label('total_attempted'),
        func.sum(Submission.correct_count).label('total_correct'),
        func.sum(Submission.mistake_count).label('total_mistakes'),
        func.count(Submission.id).label('submission_count')
    ).join(Student).filter(Student.class_id == id).first()
    
    total_attempted = class_stats.total_attempted or 0
    total_correct = class_stats.total_correct or 0
    accuracy = round(total_correct / total_attempted * 100, 1) if total_attempted > 0 else 0
    
    stats = {
        'student_count': len(students),
        'total_attempted': total_attempted,
        'total_correct': total_correct,
        'total_mistakes': class_stats.total_mistakes or 0,
        'accuracy_rate': accuracy,
        'submission_count': class_stats.submission_count or 0
    }
    
    # 获取所有学员（用于添加学员模态框）
    all_students = Student.query.order_by(Student.name).all()
    
    return render_template('admin/class_view.html', 
                          class_obj=class_obj, 
                          students=students,
                          stats=stats,
                          all_students=all_students)


@admin_bp.route('/classes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_class(id):
    """编辑班级"""
    class_obj = StudentClass.query.get_or_404(id)
    
    if request.method == 'POST':
        class_obj.name = request.form.get('name', '').strip()
        class_obj.description = request.form.get('description', '').strip()
        class_obj.teacher = request.form.get('teacher', '').strip()
        
        db.session.commit()
        flash('班级信息已更新', 'success')
        return redirect(url_for('admin.view_class', id=id))
    
    return render_template('admin/class_form.html', class_obj=class_obj)


@admin_bp.route('/classes/<int:id>/delete', methods=['POST'])
@login_required
def delete_class(id):
    """删除班级"""
    class_obj = StudentClass.query.get_or_404(id)
    
    # 移除学员的班级关联
    Student.query.filter_by(class_id=id).update({'class_id': None})
    
    db.session.delete(class_obj)
    db.session.commit()
    
    flash(f'班级 "{class_obj.name}" 已删除', 'success')
    return redirect(url_for('admin.classes'))


@admin_bp.route('/classes/<int:id>/add_students', methods=['POST'])
@login_required
def add_students_to_class(id):
    """添加学员到班级"""
    class_obj = StudentClass.query.get_or_404(id)
    student_ids = request.form.getlist('student_ids')
    
    count = 0
    for sid in student_ids:
        student = Student.query.get(int(sid))
        if student:
            student.class_id = id
            count += 1
    
    db.session.commit()
    flash(f'已添加 {count} 名学员到班级', 'success')
    return redirect(url_for('admin.view_class', id=id))


@admin_bp.route('/students/<int:id>/set_class', methods=['POST'])
@login_required
def set_student_class(id):
    """设置学员班级"""
    student = Student.query.get_or_404(id)
    class_id = request.form.get('class_id')
    
    if class_id:
        student.class_id = int(class_id) if class_id != '0' else None
    else:
        student.class_id = None
    
    db.session.commit()
    flash('学员班级已更新', 'success')
    return redirect(url_for('admin.view_student', id=id))


# ==================== 排行榜 ====================

@admin_bp.route('/leaderboard')
@login_required
def leaderboard():
    """学员排行榜"""
    from sqlalchemy import func, desc
    
    # 获取排序方式
    sort_by = request.args.get('sort', 'accuracy')  # accuracy, total, streak
    period = request.args.get('period', 'all')  # all, 7d, 30d
    
    # 计算时间范围
    from datetime import datetime, timedelta
    start_date = None
    if period == '7d':
        start_date = datetime.now() - timedelta(days=7)
    elif period == '30d':
        start_date = datetime.now() - timedelta(days=30)
    
    # 构建查询
    query = db.session.query(
        Student.id,
        Student.name,
        Student.phone,
        func.sum(Submission.total_attempted).label('total_attempted'),
        func.sum(Submission.correct_count).label('total_correct'),
        func.sum(Submission.mistake_count).label('total_mistakes'),
        func.count(Submission.id).label('submission_count')
    ).outerjoin(Submission, Student.id == Submission.student_id)
    
    if start_date:
        query = query.filter(
            db.or_(Submission.created_at >= start_date, Submission.id.is_(None))
        )
    
    query = query.group_by(Student.id)
    
    # 获取所有结果并计算正确率
    results = query.all()
    
    leaderboard_data = []
    for row in results:
        total = row.total_attempted or 0
        correct = row.total_correct or 0
        mistakes = row.total_mistakes or 0
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        
        leaderboard_data.append({
            'id': row.id,
            'name': row.name,
            'phone': row.phone,
            'total_attempted': total,
            'total_correct': correct,
            'total_mistakes': mistakes,
            'accuracy_rate': accuracy,
            'submission_count': row.submission_count or 0
        })
    
    # 排序
    if sort_by == 'accuracy':
        leaderboard_data.sort(key=lambda x: (x['accuracy_rate'], x['total_attempted']), reverse=True)
    elif sort_by == 'total':
        leaderboard_data.sort(key=lambda x: x['total_attempted'], reverse=True)
    elif sort_by == 'submissions':
        leaderboard_data.sort(key=lambda x: x['submission_count'], reverse=True)
    
    # 添加排名
    for i, item in enumerate(leaderboard_data, 1):
        item['rank'] = i
    
    return render_template('admin/leaderboard.html',
                          leaderboard=leaderboard_data,
                          sort_by=sort_by,
                          period=period)


# ==================== 数据导入 ====================

@admin_bp.route('/import', methods=['GET', 'POST'])
@login_required
def data_import():
    """数据批量导入"""
    if request.method == 'GET':
        return render_template('admin/data_import.html')
    
    # 处理上传
    from app.utils.data_import import import_student_records_from_excel
    
    file = request.files.get('file')
    if not file or not file.filename:
        flash('请选择文件', 'error')
        return redirect(url_for('admin.data_import'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('仅支持Excel文件 (.xlsx, .xls)', 'error')
        return redirect(url_for('admin.data_import'))
    
    try:
        results = import_student_records_from_excel(file)
        
        msg = f"导入完成！成功 {results['success']} 条，失败 {results['failed']} 条"
        if results['new_students'] > 0:
            msg += f"，新增学员 {results['new_students']} 人"
        
        flash(msg, 'success')
        
        if results['errors']:
            for err in results['errors'][:5]:
                flash(err, 'warning')
            if len(results['errors']) > 5:
                flash(f"... 还有 {len(results['errors'])-5} 条错误", 'warning')
                
    except Exception as e:
        flash(f'导入失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.data_import'))


@admin_bp.route('/import/template')
@login_required
def download_import_template():
    """下载导入模板"""
    from app.utils.data_import import generate_import_template
    
    output = generate_import_template()
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='学员做题记录导入模板.xlsx'
    )


# ==================== 错题统计 ====================

@admin_bp.route('/statistics')
@login_required
def statistics():
    """数据分析"""
    import json
    from datetime import datetime, timedelta
    
    # 概览数据
    total_mistakes = Mistake.query.count()
    total_students = Student.query.count()
    total_submissions = Submission.query.count()
    avg_mistakes = total_mistakes / total_students if total_students > 0 else 0
    
    overview = {
        'total_mistakes': total_mistakes,
        'total_students': total_students,
        'total_submissions': total_submissions,
        'avg_mistakes': avg_mistakes
    }
    
    # 按分类统计错题
    category_stats = db.session.query(
        Question.category,
        db.func.count(Mistake.id)
    ).join(Mistake).group_by(Question.category).all()
    
    # 转换为ECharts格式
    category_stats_json = json.dumps([
        {'name': cat or '未分类', 'value': count} 
        for cat, count in category_stats
    ], ensure_ascii=False)
    
    # 按难度统计
    difficulty_stats = db.session.query(
        Question.difficulty,
        db.func.count(Mistake.id)
    ).join(Mistake).group_by(Question.difficulty).all()
    
    difficulty_stats_json = json.dumps([
        {'name': diff or '中等', 'value': count}
        for diff, count in difficulty_stats
    ], ensure_ascii=False)
    
    # 趋势数据（近30天）
    today = datetime.now().date()
    dates = []
    counts = []
    
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        count = Mistake.query.filter(
            db.func.date(Mistake.created_at) == date
        ).count()
        dates.append(date.strftime('%m-%d'))
        counts.append(count)
    
    trend_data_json = json.dumps({
        'dates': dates,
        'counts': counts
    }, ensure_ascii=False)
    
    # 错误率最高的题目
    top_mistakes = db.session.query(
        Question,
        db.func.count(Mistake.id).label('count')
    ).join(Mistake).group_by(Question.id).order_by(db.text('count DESC')).limit(20).all()
    
    # 按题册统计
    workbook_stats = db.session.query(
        Workbook.name,
        db.func.count(Mistake.id)
    ).join(Mistake).group_by(Workbook.id).order_by(db.text('count(*) DESC')).limit(10).all()
    
    # 学员错题排行
    student_ranking = db.session.query(
        Student.name,
        db.func.count(Mistake.id).label('mistake_count')
    ).join(Mistake).group_by(Student.id).order_by(db.text('mistake_count DESC')).limit(10).all()
    
    # 转换为字典列表
    student_ranking = [{'name': name, 'mistake_count': count} for name, count in student_ranking]
    
    return render_template('admin/statistics.html',
                          overview=overview,
                          category_stats=category_stats,
                          category_stats_json=category_stats_json,
                          difficulty_stats_json=difficulty_stats_json,
                          trend_data_json=trend_data_json,
                          top_mistakes=top_mistakes,
                          workbook_stats=workbook_stats,
                          student_ranking=student_ranking)


# ==================== 机构配置 ====================

@admin_bp.route('/settings')
@login_required
def settings():
    """机构设置"""
    institution = Institution.get_instance()
    templates = WorkbookTemplate.query.all()
    
    return render_template('admin/settings.html', 
                          institution=institution,
                          templates=templates)


@admin_bp.route('/settings/institution', methods=['POST'])
@login_required
def update_institution():
    """更新机构信息"""
    institution = Institution.get_instance()
    
    institution.name = request.form.get('name', '').strip()
    institution.slogan = request.form.get('slogan', '').strip()
    institution.phone = request.form.get('phone', '').strip()
    institution.wechat = request.form.get('wechat', '').strip()
    institution.address = request.form.get('address', '').strip()
    institution.website = request.form.get('website', '').strip()
    institution.primary_color = request.form.get('primary_color', '#1a73e8').strip()
    institution.secondary_color = request.form.get('secondary_color', '#34a853').strip()
    institution.header_text = request.form.get('header_text', '').strip()
    institution.footer_text = request.form.get('footer_text', '').strip()
    
    # 处理Logo上传
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 使用固定名称保存Logo
            ext = filename.rsplit('.', 1)[1].lower()
            logo_filename = f'logo.{ext}'
            
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'brand')
            os.makedirs(upload_dir, exist_ok=True)
            
            logo_path = os.path.join(upload_dir, logo_filename)
            file.save(logo_path)
            institution.logo_path = logo_path
    
    db.session.commit()
    flash('机构信息已更新', 'success')
    return redirect(url_for('admin.settings'))


@admin_bp.route('/settings/logo/delete', methods=['POST'])
@login_required
def delete_logo():
    """删除Logo"""
    institution = Institution.get_instance()
    
    if institution.logo_path and os.path.exists(institution.logo_path):
        os.remove(institution.logo_path)
    
    institution.logo_path = None
    db.session.commit()
    
    flash('Logo已删除', 'success')
    return redirect(url_for('admin.settings'))


# ==================== 习题册模板管理 ====================

@admin_bp.route('/templates')
@login_required
def templates():
    """模板列表"""
    templates = WorkbookTemplate.query.all()
    return render_template('admin/templates.html', templates=templates)


@admin_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """创建模板"""
    if request.method == 'POST':
        template = WorkbookTemplate(
            name=request.form.get('name', '').strip(),
            answer_mode=request.form.get('answer_mode', 'hidden'),
            questions_per_page=int(request.form.get('questions_per_page', 5)),
            show_difficulty=request.form.get('show_difficulty') == 'on',
            show_category=request.form.get('show_category') == 'on',
            show_knowledge_point=request.form.get('show_knowledge_point') == 'on',
            brand_enabled=request.form.get('brand_enabled') == 'on',
            show_cover=request.form.get('show_cover') == 'on',
            show_qrcode=request.form.get('show_qrcode') == 'on',
            title_font_size=int(request.form.get('title_font_size', 16)),
            stem_font_size=int(request.form.get('stem_font_size', 12)),
            option_font_size=int(request.form.get('option_font_size', 11))
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('模板创建成功', 'success')
        return redirect(url_for('admin.templates'))
    
    return render_template('admin/template_form.html', template=None)


@admin_bp.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(id):
    """编辑模板"""
    template = WorkbookTemplate.query.get_or_404(id)
    
    if request.method == 'POST':
        template.name = request.form.get('name', '').strip()
        template.answer_mode = request.form.get('answer_mode', 'hidden')
        template.questions_per_page = int(request.form.get('questions_per_page', 5))
        template.show_difficulty = request.form.get('show_difficulty') == 'on'
        template.show_category = request.form.get('show_category') == 'on'
        template.show_knowledge_point = request.form.get('show_knowledge_point') == 'on'
        template.brand_enabled = request.form.get('brand_enabled') == 'on'
        template.show_cover = request.form.get('show_cover') == 'on'
        template.show_qrcode = request.form.get('show_qrcode') == 'on'
        template.title_font_size = int(request.form.get('title_font_size', 16))
        template.stem_font_size = int(request.form.get('stem_font_size', 12))
        template.option_font_size = int(request.form.get('option_font_size', 11))
        
        db.session.commit()
        
        flash('模板更新成功', 'success')
        return redirect(url_for('admin.templates'))
    
    return render_template('admin/template_form.html', template=template)


@admin_bp.route('/templates/<int:id>/set_default', methods=['POST'])
@login_required
def set_default_template(id):
    """设为默认模板"""
    # 取消其他默认
    WorkbookTemplate.query.update({WorkbookTemplate.is_default: False})
    
    template = WorkbookTemplate.query.get_or_404(id)
    template.is_default = True
    db.session.commit()
    
    flash(f'已将 "{template.name}" 设为默认模板', 'success')
    return redirect(url_for('admin.templates'))


@admin_bp.route('/templates/<int:id>/delete', methods=['POST'])
@login_required
def delete_template(id):
    """删除模板"""
    template = WorkbookTemplate.query.get_or_404(id)
    
    if template.is_default:
        flash('无法删除默认模板', 'error')
        return redirect(url_for('admin.templates'))
    
    db.session.delete(template)
    db.session.commit()
    
    flash('模板已删除', 'success')
    return redirect(url_for('admin.templates'))


# ==================== 题目导入 ====================

@admin_bp.route('/import')
@login_required
def import_questions():
    """导入题目页面"""
    return render_template('admin/import.html')


@admin_bp.route('/import/upload', methods=['POST'])
@login_required
def upload_document():
    """上传文档并解析"""
    from app.utils.parser import parse_document, validate_parsed_questions
    from app.utils.analyzer import batch_analyze
    import json
    
    if 'file' not in request.files:
        flash('请选择文件', 'error')
        return redirect(url_for('admin.import_questions'))
    
    file = request.files['file']
    if file.filename == '':
        flash('请选择文件', 'error')
        return redirect(url_for('admin.import_questions'))
    
    if not allowed_doc_file(file.filename):
        flash('不支持的文件格式，请上传 Word/PDF/Excel 文件', 'error')
        return redirect(url_for('admin.import_questions'))
    
    # 保存文件
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'imports')
    os.makedirs(upload_dir, exist_ok=True)
    
    # 添加时间戳避免重名
    import time
    timestamp = int(time.time())
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    try:
        # 解析文档
        result = parse_document(filepath)
        
        if not result.get('success'):
            flash(f'解析失败: {result.get("error", "未知错误")}', 'error')
            return redirect(url_for('admin.import_questions'))
        
        # 使用本地规则分析题目分类
        questions = result.get('questions', [])
        analyzed_questions = batch_analyze(questions, use_ai=False)
        result['questions'] = analyzed_questions
        
        # 验证结果
        validation = validate_parsed_questions(result.get('questions', []))
        
        # 保存解析结果到session或临时文件
        result_file = filepath + '.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return render_template('admin/import_preview.html',
                              result=result,
                              validation=validation,
                              result_file=os.path.basename(result_file))
    
    except Exception as e:
        flash(f'解析出错: {str(e)}', 'error')
        return redirect(url_for('admin.import_questions'))


@admin_bp.route('/import/confirm', methods=['POST'])
@login_required
def confirm_import():
    """确认导入题目"""
    import json
    
    result_file = request.form.get('result_file')
    selected_indices = request.form.getlist('selected')
    default_category = request.form.get('default_category', '')
    default_source = request.form.get('default_source', '')
    
    if not result_file:
        flash('导入数据已过期，请重新上传', 'error')
        return redirect(url_for('admin.import_questions'))
    
    # 读取解析结果
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'imports')
    filepath = os.path.join(upload_dir, result_file)
    
    if not os.path.exists(filepath):
        flash('导入数据已过期，请重新上传', 'error')
        return redirect(url_for('admin.import_questions'))
    
    with open(filepath, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    questions = result.get('questions', [])
    
    # 如果选择了特定题目
    if selected_indices:
        selected_set = set(int(i) for i in selected_indices)
        questions = [q for i, q in enumerate(questions) if i in selected_set]
    
    # 导入题目
    imported_count = 0
    error_count = 0
    
    # 获取当前最大UID
    max_uid = db.session.query(db.func.max(Question.id)).scalar() or 0
    
    for q in questions:
        try:
            max_uid += 1
            uid = f"Q-{str(max_uid).zfill(5)}"
            
            # 确定分类（优先使用分析结果，其次使用默认值）
            category = q.get('category') or q.get('section') or default_category or '常识判断'
            
            question = Question(
                uid=uid,
                stem=q.get('stem', ''),
                option_a=q.get('options', {}).get('A', ''),
                option_b=q.get('options', {}).get('B', ''),
                option_c=q.get('options', {}).get('C', ''),
                option_d=q.get('options', {}).get('D', ''),
                answer=q.get('answer', '').upper() if q.get('answer') else '',
                analysis=q.get('analysis', ''),
                category=category,
                subcategory=q.get('subcategory', ''),
                knowledge_point=q.get('knowledge_point', ''),
                source=default_source or result.get('source_file', ''),
                difficulty=q.get('difficulty', '中等')
            )
            
            db.session.add(question)
            imported_count += 1
        except Exception as e:
            error_count += 1
    
    db.session.commit()
    
    # 清理临时文件
    try:
        os.remove(filepath)
        # 也清理原始文件
        original_file = filepath.replace('.json', '')
        if os.path.exists(original_file):
            os.remove(original_file)
    except:
        pass
    
    if error_count > 0:
        flash(f'成功导入 {imported_count} 道题目，{error_count} 道失败', 'warning')
    else:
        flash(f'成功导入 {imported_count} 道题目', 'success')
    
    return redirect(url_for('admin.questions'))
