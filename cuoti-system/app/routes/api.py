# -*- coding: utf-8 -*-
"""API接口"""
import sqlite3
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Question, Workbook, WorkbookItem, Student, Mistake

api_bp = Blueprint('api', __name__)


# ==================== 学员同步 ====================

@api_bp.route('/sync_students')
def sync_students():
    """从督学系统同步学员"""
    try:
        duxue_db = current_app.config.get('DUXUE_DB_PATH')
        
        if not duxue_db:
            return jsonify({'success': False, 'message': '未配置督学系统数据库'})
        
        import os
        if not os.path.exists(duxue_db):
            return jsonify({'success': False, 'message': f'督学系统数据库不存在: {duxue_db}'})
        
        # 连接督学系统数据库
        conn = sqlite3.connect(duxue_db)
        cursor = conn.cursor()
        
        # 查询学员
        cursor.execute("""
            SELECT id, name, phone, class_name, exam_type, status 
            FROM students 
            WHERE status = 'active' OR status IS NULL
            ORDER BY name
        """)
        
        duxue_students = cursor.fetchall()
        conn.close()
        
        # 同步到错题系统
        synced = 0
        for row in duxue_students:
            duxue_id, name, phone, class_name, exam_type, status = row
            
            if not name:
                continue
            
            # 检查是否已存在（通过名字匹配，因为手机号可能为空）
            existing = Student.query.filter_by(name=name).first()
            
            if existing:
                # 更新信息
                if phone:
                    existing.phone = phone
            else:
                # 创建新学员
                student = Student(
                    name=name,
                    phone=phone or f'duxue_{duxue_id}'  # 没有手机号时用ID
                )
                db.session.add(student)
                synced += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'同步完成，新增 {synced} 名学员',
            'total': len(duxue_students)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@api_bp.route('/students/list')
def list_students():
    """获取学员列表（供H5选择）"""
    keyword = request.args.get('keyword', '')
    
    query = Student.query
    
    if keyword:
        query = query.filter(Student.name.contains(keyword))
    
    students = query.order_by(Student.name).limit(100).all()
    
    return jsonify({
        'success': True,
        'students': [{'id': s.id, 'name': s.name, 'phone': s.phone} for s in students]
    })


@api_bp.route('/questions')
def get_questions():
    """获取题目列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    
    query = Question.query
    
    if category:
        query = query.filter(Question.category == category)
    if keyword:
        query = query.filter(Question.stem.contains(keyword))
    
    pagination = query.order_by(Question.id.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'data': [q.to_dict() for q in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@api_bp.route('/questions/<int:id>')
def get_question(id):
    """获取单个题目"""
    question = Question.query.get_or_404(id)
    return jsonify({
        'success': True,
        'data': question.to_dict()
    })


@api_bp.route('/workbooks/<int:id>/questions')
def get_workbook_questions(id):
    """获取题册题目列表"""
    workbook = Workbook.query.get_or_404(id)
    items = workbook.items.all()
    
    questions = []
    for item in items:
        q = item.question.to_dict()
        q['order'] = item.order
        questions.append(q)
    
    return jsonify({
        'success': True,
        'workbook': workbook.to_dict(),
        'questions': questions
    })


@api_bp.route('/students/<int:id>/mistakes')
def get_student_mistakes(id):
    """获取学员错题"""
    student = Student.query.get_or_404(id)
    mistakes = Mistake.query.filter_by(student_id=id).all()
    
    data = []
    for m in mistakes:
        data.append({
            'id': m.id,
            'question': m.question.to_dict(),
            'workbook_name': m.workbook.name if m.workbook else None,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({
        'success': True,
        'student': student.to_dict(),
        'mistakes': data
    })


@api_bp.route('/statistics/categories')
def get_category_stats():
    """按分类统计错题"""
    stats = db.session.query(
        Question.category,
        db.func.count(Mistake.id).label('count')
    ).join(Mistake).group_by(Question.category).all()
    
    return jsonify({
        'success': True,
        'data': [{'category': s[0], 'count': s[1]} for s in stats]
    })
