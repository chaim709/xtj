# -*- coding: utf-8 -*-
"""H5学员端路由"""
from flask import Blueprint, render_template, request, jsonify, session
from app import db
from app.models import Workbook, WorkbookItem, WorkbookPage, Question, Student, Submission, Mistake, StudentStats, MistakeReview
from datetime import datetime, timedelta
import random

h5_bp = Blueprint('h5', __name__)


def update_student_stats(student_id, submission, category=None, subcategory=None):
    """更新学员统计数据（多维度）"""
    
    # 更新总体统计
    total_stat = StudentStats.get_or_create(student_id, 'total', None, 'all')
    total_stat.total_attempted += submission.total_attempted
    total_stat.total_correct += submission.correct_count
    total_stat.total_mistakes += submission.mistake_count
    total_stat.submission_count += 1
    total_stat.calculate_accuracy()
    
    # 更新题册统计
    workbook_stat = StudentStats.get_or_create(
        student_id, 'workbook', str(submission.workbook_id), 'all'
    )
    workbook_stat.total_attempted += submission.total_attempted
    workbook_stat.total_correct += submission.correct_count
    workbook_stat.total_mistakes += submission.mistake_count
    workbook_stat.submission_count += 1
    workbook_stat.calculate_accuracy()
    
    # 更新一级分类统计
    if category:
        cat_stat = StudentStats.get_or_create(student_id, 'category', category, 'all')
        cat_stat.total_attempted += submission.total_attempted
        cat_stat.total_correct += submission.correct_count
        cat_stat.total_mistakes += submission.mistake_count
        cat_stat.submission_count += 1
        cat_stat.calculate_accuracy()
    
    # 更新二级分类（板块）统计
    if subcategory:
        subcat_stat = StudentStats.get_or_create(student_id, 'subcategory', subcategory, 'all')
        subcat_stat.total_attempted += submission.total_attempted
        subcat_stat.total_correct += submission.correct_count
        subcat_stat.total_mistakes += submission.mistake_count
        subcat_stat.submission_count += 1
        subcat_stat.calculate_accuracy()
    
    db.session.flush()


def parse_qr_code_type(qr_code):
    """解析二维码类型和信息"""
    import re
    
    # 分类模式: CAT{workbook_id}_{category_idx}
    cat_match = re.match(r'CAT(\d+)_(\d+)', qr_code)
    if cat_match:
        return {
            'type': 'category',
            'workbook_id': int(cat_match.group(1)),
            'category_idx': int(cat_match.group(2))
        }
    
    # 标准模式: WB{workbook_id}P{page_num}
    page_match = re.match(r'WB(\d+)P(\d+)', qr_code)
    if page_match:
        return {
            'type': 'standard',
            'workbook_id': int(page_match.group(1)),
            'page_num': int(page_match.group(2))
        }
    
    # 单二维码模式: WB{workbook_id}
    single_match = re.match(r'WB(\d+)$', qr_code)
    if single_match:
        return {
            'type': 'single',
            'workbook_id': int(single_match.group(1))
        }
    
    # 兼容旧格式（直接查询）
    return {'type': 'legacy'}


@h5_bp.route('/scan/<qr_code>')
def scan(qr_code):
    """扫码页面"""
    # 查找页面
    page = WorkbookPage.query.filter_by(qr_code=qr_code).first()
    
    if not page:
        return render_template('h5/error.html', message='无效的二维码')
    
    workbook = page.workbook
    
    # 解析二维码类型
    qr_info = parse_qr_code_type(qr_code)
    
    # 获取该范围的题目
    items = WorkbookItem.query.filter(
        WorkbookItem.workbook_id == workbook.id,
        WorkbookItem.order >= page.start_order,
        WorkbookItem.order <= page.end_order
    ).order_by(WorkbookItem.order).all()
    
    # 获取板块信息（从题目分类推断）
    category = None
    subcategory = None
    if items:
        # 取第一题的分类作为该范围的分类
        first_q = items[0].question
        category = first_q.category
        subcategory = first_q.subcategory
    
    questions = []
    for item in items:
        questions.append({
            'order': item.order,
            'id': item.question_id,
            'stem': item.question.stem[:50] + '...' if len(item.question.stem) > 50 else item.question.stem,
            'category': item.question.category,
            'subcategory': item.question.subcategory
        })
    
    # 计算该范围的总题数
    total_questions_in_range = len(questions)
    
    return render_template('h5/submit.html',
                          workbook=workbook,
                          page=page,
                          questions=questions,
                          qr_code=qr_code,
                          qr_type=qr_info.get('type', 'legacy'),
                          category=category,
                          subcategory=subcategory,
                          total_questions_in_range=total_questions_in_range,
                          start_order=page.start_order,
                          end_order=page.end_order)


@h5_bp.route('/submit', methods=['POST'])
def submit():
    """提交错题"""
    from app.models import StudentStats
    
    data = request.get_json()
    
    qr_code = data.get('qr_code')
    student_id = data.get('student_id')  # 新增：直接传学员ID
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    mistake_orders = data.get('mistakes', [])  # 错题的题号列表
    total_attempted = data.get('total_attempted', 0)  # 新增：本次做了多少题
    
    # 查找页面
    page = WorkbookPage.query.filter_by(qr_code=qr_code).first()
    if not page:
        return jsonify({'success': False, 'message': '无效的二维码'})
    
    workbook = page.workbook
    
    # 获取学员
    if student_id:
        # 通过ID查找
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'message': '学员不存在'})
    elif name and phone:
        # 兼容旧方式：通过手机号查找或创建
        student = Student.query.filter_by(phone=phone).first()
        if not student:
            student = Student(name=name, phone=phone)
            db.session.add(student)
            db.session.flush()
        else:
            student.name = name
    else:
        return jsonify({'success': False, 'message': '请选择学员'})
    
    # 获取该范围题目的分类信息
    items = WorkbookItem.query.filter(
        WorkbookItem.workbook_id == workbook.id,
        WorkbookItem.order >= page.start_order,
        WorkbookItem.order <= page.end_order
    ).order_by(WorkbookItem.order).all()
    
    category = None
    subcategory = None
    if items:
        first_q = items[0].question
        category = first_q.category
        subcategory = first_q.subcategory
    
    # 如果没传total_attempted，默认为该范围的题目数
    if not total_attempted or total_attempted <= 0:
        total_attempted = len(items)
    
    # 创建提交记录
    submission = Submission(
        student_id=student.id,
        workbook_id=workbook.id,
        page_num=page.page_num,
        mistake_count=len(mistake_orders),
        total_attempted=total_attempted,
        category=category,
        subcategory=subcategory,
        start_order=page.start_order,
        end_order=page.end_order
    )
    # 自动计算正确率
    submission.calculate_accuracy()
    
    db.session.add(submission)
    db.session.flush()
    
    # 更新学员统计（多维度）
    update_student_stats(student.id, submission, category, subcategory)
    
    # 记录错题
    result_questions = []
    for order in mistake_orders:
        item = WorkbookItem.query.filter_by(
            workbook_id=workbook.id,
            order=int(order)
        ).first()
        
        if item:
            # 检查是否已记录
            existing = Mistake.query.filter_by(
                student_id=student.id,
                question_id=item.question_id,
                workbook_id=workbook.id
            ).first()
            
            if not existing:
                mistake = Mistake(
                    student_id=student.id,
                    question_id=item.question_id,
                    submission_id=submission.id,
                    workbook_id=workbook.id,
                    question_order=order
                )
                db.session.add(mistake)
            
            # 返回错题详情
            q = item.question
            result_questions.append({
                'order': order,
                'stem': q.stem,
                'options': {
                    'A': q.option_a,
                    'B': q.option_b,
                    'C': q.option_c,
                    'D': q.option_d
                },
                'answer': q.answer,
                'analysis': q.analysis
            })
    
    student.last_submit_at = db.func.now()
    db.session.commit()
    
    # 构建返回消息
    accuracy_msg = ''
    if submission.total_attempted > 0:
        accuracy_msg = f'，正确率 {submission.accuracy_rate}%'
    
    return jsonify({
        'success': True,
        'message': f'提交成功！做了{submission.total_attempted}题，错{len(mistake_orders)}题{accuracy_msg}',
        'questions': result_questions,
        'stats': {
            'total_attempted': submission.total_attempted,
            'correct_count': submission.correct_count,
            'mistake_count': submission.mistake_count,
            'accuracy_rate': submission.accuracy_rate,
            'category': category,
            'subcategory': subcategory
        }
    })


@h5_bp.route('/result')
def result():
    """结果页面（查看错题解析）"""
    return render_template('h5/result.html')


@h5_bp.route('/answers/<qr_code>')
def view_answers(qr_code):
    """查看答案解析（不需要提交）"""
    page = WorkbookPage.query.filter_by(qr_code=qr_code).first()
    
    if not page:
        return render_template('h5/error.html', message='无效的二维码')
    
    workbook = page.workbook
    
    # 获取该页的题目
    items = WorkbookItem.query.filter(
        WorkbookItem.workbook_id == workbook.id,
        WorkbookItem.order >= page.start_order,
        WorkbookItem.order <= page.end_order
    ).order_by(WorkbookItem.order).all()
    
    questions = []
    for item in items:
        q = item.question
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


@h5_bp.route('/my/<int:student_id>')
def my_mistakes(student_id):
    """学员个人中心 - 错题列表"""
    student = Student.query.get_or_404(student_id)
    
    # 获取错题统计
    mistakes = Mistake.query.filter_by(student_id=student_id).order_by(Mistake.created_at.desc()).all()
    
    # 按分类统计
    category_stats = db.session.query(
        Question.category,
        db.func.count(Mistake.id)
    ).join(Mistake).filter(Mistake.student_id == student_id).group_by(Question.category).all()
    
    # 获取最近提交
    submissions = Submission.query.filter_by(student_id=student_id).order_by(Submission.created_at.desc()).limit(10).all()
    
    return render_template('h5/my_mistakes.html',
                          student=student,
                          mistakes=mistakes,
                          category_stats=category_stats,
                          submissions=submissions)


@h5_bp.route('/practice/<int:student_id>')
def practice(student_id):
    """错题重做"""
    student = Student.query.get_or_404(student_id)
    
    # 获取参数
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
    
    # 获取题目详情
    questions = Question.query.filter(Question.id.in_(selected_ids)).all()
    
    # 打乱顺序
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


@h5_bp.route('/recommend/<int:student_id>')
def recommend_practice(student_id):
    """智能推荐练习"""
    from app.utils.recommendation import RecommendationService
    
    student = Student.query.get_or_404(student_id)
    rec_service = RecommendationService(student_id)
    
    # 获取推荐摘要
    summary = rec_service.get_recommendation_summary()
    
    # 获取模式参数
    mode = request.args.get('mode', 'weak')
    count = request.args.get('count', 10, type=int)
    
    # 生成推荐题目
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


@h5_bp.route('/smart_practice/<int:student_id>')
def smart_practice(student_id):
    """智能练习（混合错题+新题）"""
    from app.utils.recommendation import RecommendationService
    
    student = Student.query.get_or_404(student_id)
    rec_service = RecommendationService(student_id)
    
    count = request.args.get('count', 20, type=int)
    
    # 生成练习题集
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


@h5_bp.route('/review/<int:student_id>')
def review_center(student_id):
    """复习中心"""
    from app.utils.reminder import ReminderService
    
    student = Student.query.get_or_404(student_id)
    reminder = ReminderService(student_id)
    
    # 同步错题到复习记录
    reminder.sync_mistakes_to_reviews()
    
    # 获取统计
    stats = reminder.get_review_stats()
    
    # 获取待复习题目
    due_reviews = reminder.get_due_reviews(20)
    
    # 获取未来复习计划
    schedule = reminder.get_upcoming_reviews(7)
    
    return render_template('h5/review_center.html',
                          student=student,
                          stats=stats,
                          due_reviews=due_reviews,
                          schedule=schedule)


@h5_bp.route('/review/<int:student_id>/start')
def start_review(student_id):
    """开始复习"""
    from app.utils.reminder import ReminderService
    
    student = Student.query.get_or_404(student_id)
    reminder = ReminderService(student_id)
    
    # 获取待复习题目
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
    from app.utils.reminder import ReminderService
    
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


@h5_bp.route('/plan/<int:student_id>')
def study_plan(student_id):
    """学习计划"""
    from app.utils.study_plan import StudyPlanGenerator
    
    student = Student.query.get_or_404(student_id)
    
    # 获取参数
    days = request.args.get('days', 7, type=int)
    daily_target = request.args.get('target', 20, type=int)
    
    # 生成计划
    generator = StudyPlanGenerator(student_id)
    plan = generator.generate_daily_plan(daily_target, days)
    
    return render_template('h5/study_plan.html',
                          student=student,
                          plan=plan)


@h5_bp.route('/home/<int:student_id>')
def student_home(student_id):
    """学员个人主页"""
    from app.utils.stats import StudentStatsService
    from app.utils.reminder import ReminderService
    
    student = Student.query.get_or_404(student_id)
    
    # 获取统计
    stats_service = StudentStatsService(student_id)
    overview = stats_service.get_overview('all')
    
    # 获取复习统计
    reminder = ReminderService(student_id)
    reminder.sync_mistakes_to_reviews()
    review_stats = reminder.get_review_stats()
    
    # 获取最近提交
    recent_submissions = Submission.query.filter_by(
        student_id=student_id
    ).order_by(Submission.created_at.desc()).limit(5).all()
    
    return render_template('h5/student_home.html',
                          student=student,
                          overview=overview,
                          review_stats=review_stats,
                          recent_submissions=recent_submissions)
