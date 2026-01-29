# -*- coding: utf-8 -*-
"""题库管理路由 - 从cuoti-system合并"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required
from app import db
from app.models import Question, Workbook, WorkbookItem, WorkbookPage, Institution, WorkbookTemplate
from datetime import datetime
import os

questions_bp = Blueprint('questions', __name__, url_prefix='/questions')


@questions_bp.route('/')
@login_required
def index():
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
    
    return render_template('questions/list.html',
                          pagination=pagination,
                          categories=categories,
                          current_category=category,
                          keyword=keyword)


@questions_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建题目"""
    if request.method == 'POST':
        question = Question(
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
            difficulty=request.form.get('difficulty', 3, type=int)
        )
        db.session.add(question)
        db.session.commit()
        
        flash('题目创建成功', 'success')
        return redirect(url_for('questions.index'))
    
    # 获取现有分类
    categories = db.session.query(Question.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('questions/form.html', question=None, categories=categories)


@questions_bp.route('/<int:id>')
@login_required
def view(id):
    """查看题目"""
    question = Question.query.get_or_404(id)
    return render_template('questions/view.html', question=question)


@questions_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
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
        question.difficulty = request.form.get('difficulty', 3, type=int)
        
        db.session.commit()
        flash('题目更新成功', 'success')
        return redirect(url_for('questions.view', id=id))
    
    categories = db.session.query(Question.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('questions/form.html', question=question, categories=categories)


@questions_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除题目"""
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    
    flash('题目已删除', 'success')
    return redirect(url_for('questions.index'))


@questions_bp.route('/statistics')
@login_required
def statistics():
    """题库统计"""
    from sqlalchemy import func
    
    total = Question.query.count()
    
    # 按分类统计
    category_stats = db.session.query(
        Question.category,
        func.count(Question.id)
    ).group_by(Question.category).all()
    
    # 按二级分类统计
    subcategory_stats = db.session.query(
        Question.subcategory,
        func.count(Question.id)
    ).filter(Question.subcategory.isnot(None)).group_by(Question.subcategory).all()
    
    return render_template('questions/statistics.html',
                          total=total,
                          category_stats=category_stats,
                          subcategory_stats=subcategory_stats)
