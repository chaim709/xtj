# -*- coding: utf-8 -*-
"""H5学员端路由 - 从cuoti-system合并"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from app import db
from app.models import (
    Question, Workbook, WorkbookItem, WorkbookPage, 
    Student, Submission, Mistake, MistakeReview, StudentStats
)
from datetime import datetime
import random
import re

h5_bp = Blueprint('h5', __name__, url_prefix='/h5')


def parse_qr_code_type(qr_code):
    """解析二维码类型和信息"""
    if not qr_code:
        return {'type': 'unknown'}
    
    # WB{id}P{page} - 标准分页模式
    match = re.match(r'WB(\d+)P(\d+)', qr_code)
    if match:
        return {
            'type': 'page',
            'workbook_id': int(match.group(1)),
            'page_num': int(match.group(2))
        }
    
    # CAT{id}_{idx} - 分类模式
    match = re.match(r'CAT(\d+)_(\d+)', qr_code)
    if match:
        return {
            'type': 'category',
            'workbook_id': int(match.group(1)),
            'category_index': int(match.group(2))
        }
    
    # WB{id} - 单二维码模式
    match = re.match(r'WB(\d+)$', qr_code)
    if match:
        return {
            'type': 'single',
            'workbook_id': int(match.group(1))
        }
    
    return {'type': 'unknown', 'qr_code': qr_code}


@h5_bp.route('/scan')
def scan():
    """扫码入口"""
    qr = request.args.get('qr', '')
    
    if not qr:
        return render_template('h5/error.html', message='无效的二维码')
    
    # 解析二维码
    qr_info = parse_qr_code_type(qr)
    
    if qr_info['type'] == 'unknown':
        return render_template('h5/error.html', message='无效的二维码格式')
    
    workbook_id = qr_info.get('workbook_id')
    workbook = Workbook.query.get(workbook_id)
    
    if not workbook:
        return render_template('h5/error.html', message='题册不存在')
    
    # 获取题目范围
    if qr_info['type'] == 'page':
        page = WorkbookPage.query.filter_by(
            workbook_id=workbook_id,
            page_num=qr_info['page_num']
        ).first()
        
        if page:
            start_order = page.start_order
            end_order = page.end_order
        else:
            start_order = 1
            end_order = workbook.total_questions
    elif qr_info['type'] == 'category':
        # 分类模式需要额外处理
        start_order = 1
        end_order = workbook.total_questions
    else:
        start_order = 1
        end_order = workbook.total_questions
    
    # 获取题目
    items = workbook.items.filter(
        WorkbookItem.order >= start_order,
        WorkbookItem.order <= end_order
    ).order_by(WorkbookItem.order).all()
    
    questions = []
    category = None
    subcategory = None
    
    for item in items:
        q = item.question
        if q:
            if not category and q.category:
                category = q.category
            if not subcategory and q.subcategory:
                subcategory = q.subcategory
            questions.append({
                'order': item.order,
                'id': q.id,
                'stem': q.stem[:50] + '...' if len(q.stem) > 50 else q.stem
            })
    
    return render_template('h5/submit.html',
                          workbook=workbook,
                          questions=questions,
                          start_order=start_order,
                          end_order=end_order,
                          category=category,
                          subcategory=subcategory,
                          qr_type=qr_info['type'])


@h5_bp.route('/submit', methods=['POST'])
def submit():
    """提交错题"""
    data = request.get_json()
    
    student_phone = data.get('phone', '').strip()
    student_name = data.get('name', '').strip()
    workbook_id = data.get('workbook_id')
    mistake_orders = data.get('mistakes', [])
    total_attempted = data.get('total_attempted', 0)
    
    if not student_phone or not workbook_id:
        return jsonify({'success': False, 'message': '参数不完整'})
    
    # 获取或创建学员
    student = Student.query.filter_by(phone=student_phone).first()
    if not student:
        student = Student(
            name=student_name or f'学员{student_phone[-4:]}',
            phone=student_phone
        )
        db.session.add(student)
        db.session.flush()
    
    # 获取题册
    workbook = Workbook.query.get(workbook_id)
    if not workbook:
        return jsonify({'success': False, 'message': '题册不存在'})
    
    # 获取分类信息
    start_order = data.get('start_order', 1)
    end_order = data.get('end_order', workbook.total_questions)
    
    items = workbook.items.filter(
        WorkbookItem.order >= start_order,
        WorkbookItem.order <= end_order
    ).all()
    
    category = None
    subcategory = None
    for item in items:
        if item.question:
            if not category and item.question.category:
                category = item.question.category
            if not subcategory and item.question.subcategory:
                subcategory = item.question.subcategory
            if category and subcategory:
                break
    
    # 创建提交记录
    submission = Submission(
        student_id=student.id,
        workbook_id=workbook_id,
        total_attempted=total_attempted,
        mistake_count=len(mistake_orders),
        start_order=start_order,
        end_order=end_order,
        category=category,
        subcategory=subcategory
    )
    submission.calculate_accuracy()
    db.session.add(submission)
    db.session.flush()
    
    # 记录错题
    for order in mistake_orders:
        item = workbook.items.filter_by(order=int(order)).first()
        if item:
            mistake = Mistake(
                student_id=student.id,
                question_id=item.question_id,
                workbook_id=workbook_id,
                submission_id=submission.id,
                question_order=order
            )
            db.session.add(mistake)
    
    # 更新学员统计
    update_student_stats(student.id, submission, subcategory)
    
    student.last_contact_date = datetime.now().date()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'提交成功！本次正确率 {submission.accuracy_rate}%',
        'stats': {
            'total_attempted': submission.total_attempted,
            'correct_count': submission.correct_count,
            'mistake_count': submission.mistake_count,
            'accuracy_rate': submission.accuracy_rate
        }
    })


def update_student_stats(student_id, submission, subcategory=None):
    """更新学员统计"""
    # 总体统计
    total_stat = StudentStats.get_or_create(student_id, 'total', None, 'all')
    total_stat.total_attempted += submission.total_attempted
    total_stat.total_correct += submission.correct_count
    total_stat.total_mistakes += submission.mistake_count
    total_stat.submission_count += 1
    total_stat.calculate_accuracy()
    
    # 板块统计
    if subcategory:
        subcat_stat = StudentStats.get_or_create(student_id, 'subcategory', subcategory, 'all')
        subcat_stat.total_attempted += submission.total_attempted
        subcat_stat.total_correct += submission.correct_count
        subcat_stat.total_mistakes += submission.mistake_count
        subcat_stat.submission_count += 1
        subcat_stat.calculate_accuracy()


@h5_bp.route('/my/<int:student_id>')
def my_mistakes(student_id):
    """我的错题"""
    student = Student.query.get_or_404(student_id)
    mistakes = Mistake.query.filter_by(student_id=student_id).order_by(Mistake.created_at.desc()).all()
    
    # 按分类统计
    from sqlalchemy import func
    category_stats = db.session.query(
        Question.category,
        func.count(Mistake.id)
    ).join(Mistake).filter(
        Mistake.student_id == student_id
    ).group_by(Question.category).all()
    
    # 最近提交
    submissions = Submission.query.filter_by(student_id=student_id).order_by(
        Submission.created_at.desc()
    ).limit(10).all()
    
    return render_template('h5/my_mistakes.html',
                          student=student,
                          mistakes=mistakes,
                          category_stats=category_stats,
                          submissions=submissions)


@h5_bp.route('/home/<int:student_id>')
def student_home(student_id):
    """学员主页"""
    from app.services.question.stats import StudentStatsService
    from app.services.question.reminder import ReminderService
    
    student = Student.query.get_or_404(student_id)
    
    # 获取统计
    stats_service = StudentStatsService(student_id)
    overview = stats_service.get_overview('all')
    
    # 获取复习统计
    reminder = ReminderService(student_id)
    reminder.sync_mistakes_to_reviews()
    review_stats = reminder.get_review_stats()
    
    # 最近提交
    recent_submissions = Submission.query.filter_by(
        student_id=student_id
    ).order_by(Submission.created_at.desc()).limit(5).all()
    
    return render_template('h5/student_home.html',
                          student=student,
                          overview=overview,
                          review_stats=review_stats,
                          recent_submissions=recent_submissions)


@h5_bp.route('/review/<int:student_id>')
def review_center(student_id):
    """复习中心"""
    from app.services.question.reminder import ReminderService
    
    student = Student.query.get_or_404(student_id)
    reminder = ReminderService(student_id)
    
    # 同步错题
    reminder.sync_mistakes_to_reviews()
    
    # 获取统计
    stats = reminder.get_review_stats()
    due_reviews = reminder.get_due_reviews(20)
    schedule = reminder.get_upcoming_reviews(7)
    
    return render_template('h5/review_center.html',
                          student=student,
                          stats=stats,
                          due_reviews=due_reviews,
                          schedule=schedule)


@h5_bp.route('/recommend/<int:student_id>')
def recommend_practice(student_id):
    """智能推荐"""
    from app.services.question.recommendation import RecommendationService
    
    student = Student.query.get_or_404(student_id)
    rec_service = RecommendationService(student_id)
    
    summary = rec_service.get_recommendation_summary()
    mode = request.args.get('mode', 'weak')
    count = request.args.get('count', 10, type=int)
    
    recommendations = rec_service.recommend_similar_questions(count, mode)
    
    questions = []
    for i, rec in enumerate(recommendations, 1):
        q = rec['question']
        questions.append({
            'index': i,
            'id': q.id,
            'stem': q.stem,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            },
            'answer': q.answer,
            'analysis': q.analysis,
            'category': q.category,
            'subcategory': q.subcategory,
            'reason': rec['reason']
        })
    
    return render_template('h5/recommend.html',
                          student=student,
                          summary=summary,
                          questions=questions,
                          mode=mode)


@h5_bp.route('/plan/<int:student_id>')
def study_plan(student_id):
    """学习计划"""
    from app.services.question.study_plan import StudyPlanGenerator
    
    student = Student.query.get_or_404(student_id)
    
    days = request.args.get('days', 7, type=int)
    daily_target = request.args.get('target', 20, type=int)
    
    generator = StudyPlanGenerator(student_id)
    plan = generator.generate_daily_plan(daily_target, days)
    
    return render_template('h5/study_plan.html',
                          student=student,
                          plan=plan)


@h5_bp.route('/practice/<int:student_id>')
def practice(student_id):
    """错题重做"""
    student = Student.query.get_or_404(student_id)
    
    category = request.args.get('category', '')
    count = request.args.get('count', 10, type=int)
    
    # 查询错题
    query = Mistake.query.filter_by(student_id=student_id)
    if category:
        query = query.join(Question).filter(Question.category == category)
    
    mistake_ids = [m.question_id for m in query.all()]
    
    if not mistake_ids:
        return render_template('h5/error.html', message='暂无错题记录')
    
    # 随机抽取
    if len(mistake_ids) > count:
        selected_ids = random.sample(mistake_ids, count)
    else:
        selected_ids = mistake_ids
        random.shuffle(selected_ids)
    
    questions = Question.query.filter(Question.id.in_(selected_ids)).all()
    random.shuffle(questions)
    
    question_list = []
    for i, q in enumerate(questions, 1):
        question_list.append({
            'index': i,
            'id': q.id,
            'stem': q.stem,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            },
            'answer': q.answer,
            'analysis': q.analysis,
            'category': q.category
        })
    
    return render_template('h5/practice.html',
                          student=student,
                          questions=question_list,
                          category=category)


@h5_bp.route('/practice/check', methods=['POST'])
def check_answer():
    """检查答案"""
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('answer', '').upper()
    
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'success': False, 'message': '题目不存在'})
    
    is_correct = user_answer == question.answer
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': question.answer,
        'analysis': question.analysis
    })


@h5_bp.route('/smart_practice/<int:student_id>')
def smart_practice(student_id):
    """智能练习（混合错题+新题）"""
    from app.services.question.recommendation import RecommendationService
    
    student = Student.query.get_or_404(student_id)
    rec_service = RecommendationService(student_id)
    
    count = request.args.get('count', 20, type=int)
    
    practice_set = rec_service.generate_practice_set(count)
    
    questions = []
    for i, item in enumerate(practice_set, 1):
        q = item['question']
        questions.append({
            'index': i,
            'id': q.id,
            'stem': q.stem,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            },
            'answer': q.answer,
            'analysis': q.analysis,
            'category': q.category,
            'subcategory': q.subcategory,
            'type': item['type'],
            'reason': item.get('reason', f"错过{item.get('mistake_count', 0)}次")
        })
    
    return render_template('h5/smart_practice.html',
                          student=student,
                          questions=questions)


@h5_bp.route('/review/<int:student_id>/start')
def start_review(student_id):
    """开始复习"""
    from app.services.question.reminder import ReminderService
    
    student = Student.query.get_or_404(student_id)
    reminder = ReminderService(student_id)
    
    due_reviews = reminder.get_due_reviews(10)
    
    if not due_reviews:
        return render_template('h5/error.html', message='暂无待复习的题目，太棒了！')
    
    questions = []
    for i, review in enumerate(due_reviews, 1):
        q = review.question
        questions.append({
            'index': i,
            'id': q.id,
            'stem': q.stem,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            },
            'answer': q.answer,
            'analysis': q.analysis,
            'category': q.category,
            'subcategory': q.subcategory,
            'review_count': review.review_count,
            'interval': review.current_interval
        })
    
    return render_template('h5/review_practice.html',
                          student=student,
                          questions=questions)


@h5_bp.route('/review/record', methods=['POST'])
def record_review():
    """记录复习结果"""
    from app.services.question.reminder import ReminderService
    
    data = request.get_json()
    student_id = data.get('student_id')
    question_id = data.get('question_id')
    is_correct = data.get('is_correct', False)
    
    reminder = ReminderService(student_id)
    success = reminder.record_review_result(question_id, is_correct)
    
    return jsonify({
        'success': success,
        'message': '已记录' if success else '记录失败'
    })


@h5_bp.route('/answers/<qr_code>')
def view_answers(qr_code):
    """查看答案解析（不需要提交）"""
    page = WorkbookPage.query.filter_by(qr_code=qr_code).first()
    
    if not page:
        return render_template('h5/error.html', message='无效的二维码')
    
    workbook = page.workbook
    
    items = workbook.items.filter(
        WorkbookItem.order >= page.start_order,
        WorkbookItem.order <= page.end_order
    ).order_by(WorkbookItem.order).all()
    
    questions = []
    for item in items:
        q = item.question
        if q:
            questions.append({
                'order': item.order,
                'stem': q.stem,
                'options': {
                    'A': q.option_a,
                    'B': q.option_b,
                    'C': q.option_c,
                    'D': q.option_d
                },
                'answer': q.answer,
                'analysis': q.analysis,
                'category': q.category
            })
    
    return render_template('h5/answers.html',
                          workbook=workbook,
                          page=page,
                          questions=questions)
