# -*- coding: utf-8 -*-
"""管理后台扩展路由 - 排行榜、数据导入、班级管理、统计分析"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required
from app import db
from app.models import (
    Question, Workbook, WorkbookItem, WorkbookPage,
    Student, Submission, Mistake, MistakeReview, StudentStats,
    Institution, WorkbookTemplate
)
from datetime import datetime, timedelta
from sqlalchemy import func
import os
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ==================== 仪表盘 ====================

@admin_bp.route('/')
@login_required
def dashboard():
    """管理仪表盘"""
    # 基础统计
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


# ==================== 排行榜 ====================

@admin_bp.route('/leaderboard')
@login_required
def leaderboard():
    """学员排行榜"""
    sort_by = request.args.get('sort', 'accuracy')
    period = request.args.get('period', 'all')
    
    # 计算时间范围
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
    
    from app.services.question.data_import import import_student_records_from_excel
    
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
        if results.get('new_students', 0) > 0:
            msg += f"，新增学员 {results['new_students']} 人"
        
        flash(msg, 'success')
        
        if results.get('errors'):
            for err in results['errors'][:5]:
                flash(err, 'warning')
                
    except Exception as e:
        flash(f'导入失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.data_import'))


@admin_bp.route('/import/template')
@login_required
def download_import_template():
    """下载导入模板"""
    from app.services.question.data_import import generate_import_template
    
    output = generate_import_template()
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='学员做题记录导入模板.xlsx'
    )


# ==================== 班级管理 ====================

@admin_bp.route('/classes')
@login_required
def classes():
    """班级列表"""
    from app.models import StudentClass
    classes = StudentClass.query.order_by(StudentClass.created_at.desc()).all()
    return render_template('admin/classes.html', classes=classes)


@admin_bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
def create_class():
    """创建班级"""
    from app.models import StudentClass
    
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
    from app.models import StudentClass
    
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
    from app.models import StudentClass
    
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
    from app.models import StudentClass
    
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
    from app.models import StudentClass
    
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


# ==================== 统计分析 ====================

@admin_bp.route('/statistics')
@login_required
def statistics():
    """数据分析"""
    # 概览数据
    total_mistakes = Mistake.query.count()
    total_students = Student.query.count()
    total_submissions = Submission.query.count()
    avg_mistakes = round(total_mistakes / total_students, 1) if total_students > 0 else 0
    
    overview = {
        'total_mistakes': total_mistakes,
        'total_students': total_students,
        'total_submissions': total_submissions,
        'avg_mistakes': avg_mistakes
    }
    
    # 按分类统计错题
    category_stats = db.session.query(
        Question.category,
        func.count(Mistake.id)
    ).join(Mistake).group_by(Question.category).all()
    
    category_stats_json = json.dumps([
        {'name': cat or '未分类', 'value': count}
        for cat, count in category_stats
    ], ensure_ascii=False)
    
    # 按难度统计
    difficulty_stats = db.session.query(
        Question.difficulty,
        func.count(Mistake.id)
    ).join(Mistake).group_by(Question.difficulty).all()
    
    difficulty_stats_json = json.dumps([
        {'name': str(diff) if diff else '中等', 'value': count}
        for diff, count in difficulty_stats
    ], ensure_ascii=False)
    
    # 趋势数据（近30天）
    today = datetime.now().date()
    dates = []
    counts = []
    
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        count = Mistake.query.filter(
            func.date(Mistake.created_at) == date
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
        func.count(Mistake.id).label('count')
    ).join(Mistake).group_by(Question.id).order_by(db.text('count DESC')).limit(20).all()
    
    # 按题册统计
    workbook_stats = db.session.query(
        Workbook.name,
        func.count(Mistake.id)
    ).join(Mistake).group_by(Workbook.id).order_by(db.text('count(*) DESC')).limit(10).all()
    
    # 学员错题排行
    student_ranking = db.session.query(
        Student.name,
        func.count(Mistake.id).label('mistake_count')
    ).join(Mistake).group_by(Student.id).order_by(db.text('mistake_count DESC')).limit(10).all()
    
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


# ==================== 学员详情扩展 ====================

@admin_bp.route('/students/<int:id>/download_mistakes')
@login_required
def download_mistake_book(id):
    """下载学员错题本PDF"""
    from app.services.question.report_generator import generate_mistake_book_pdf
    
    student = Student.query.get_or_404(id)
    mistakes = Mistake.query.filter_by(student_id=id).order_by(Mistake.created_at.desc()).all()
    institution = Institution.get_instance()
    
    if not mistakes:
        flash('该学员暂无错题记录', 'warning')
        return redirect(url_for('students.detail', id=id))
    
    try:
        filepath = generate_mistake_book_pdf(student, mistakes, institution)
        return send_file(filepath, as_attachment=True,
                        download_name=f'错题本_{student.name}.pdf')
    except Exception as e:
        flash(f'生成失败: {str(e)}', 'error')
        return redirect(url_for('students.detail', id=id))


@admin_bp.route('/students/<int:id>/download_report')
@login_required
def download_learning_report(id):
    """下载学员学习分析报告PDF"""
    from app.services.question.report_generator import generate_student_report
    
    student = Student.query.get_or_404(id)
    period = request.args.get('period', 'all')
    
    try:
        filepath = generate_student_report(id, period)
        return send_file(filepath, as_attachment=True,
                        download_name=f'学习报告_{student.name}.pdf')
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'生成失败: {str(e)}', 'error')
        return redirect(url_for('students.detail', id=id))


@admin_bp.route('/students/<int:id>/stats')
@login_required
def student_stats_api(id):
    """获取学员统计数据API"""
    from app.services.question.stats import StudentStatsService
    
    period = request.args.get('period', 'all')
    stats_service = StudentStatsService(id)
    
    return jsonify({
        'success': True,
        'data': stats_service.get_full_report_data(period)
    })
