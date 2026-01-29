# -*- coding: utf-8 -*-
"""题册管理路由 - 从cuoti-system合并"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required
from app import db
from app.models import Question, Workbook, WorkbookItem, WorkbookPage, Institution, WorkbookTemplate
from datetime import datetime
import os

workbooks_bp = Blueprint('workbooks', __name__, url_prefix='/workbooks')


@workbooks_bp.route('/')
@login_required
def index():
    """题册列表"""
    workbooks = Workbook.query.order_by(Workbook.created_at.desc()).all()
    return render_template('workbooks/list.html', workbooks=workbooks)


@workbooks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建题册"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '')
        question_ids = request.form.getlist('question_ids')
        
        if not name:
            flash('题册名称不能为空', 'error')
            return redirect(url_for('workbooks.create'))
        
        workbook = Workbook(
            name=name,
            description=description,
            category=category
        )
        db.session.add(workbook)
        db.session.flush()
        
        # 添加题目
        for i, qid in enumerate(question_ids, 1):
            item = WorkbookItem(
                workbook_id=workbook.id,
                question_id=int(qid),
                order=i
            )
            db.session.add(item)
        
        workbook.update_question_count()
        db.session.commit()
        
        flash(f'题册 "{name}" 创建成功', 'success')
        return redirect(url_for('workbooks.view', id=workbook.id))
    
    # 获取题目列表
    questions = Question.query.order_by(Question.id.desc()).limit(100).all()
    categories = db.session.query(Question.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('workbooks/form.html', 
                          workbook=None, 
                          questions=questions,
                          categories=categories)


@workbooks_bp.route('/<int:id>')
@login_required
def view(id):
    """查看题册"""
    workbook = Workbook.query.get_or_404(id)
    items = workbook.items.order_by(WorkbookItem.order).all()
    templates = WorkbookTemplate.query.all()
    institution = Institution.get_instance()
    
    return render_template('workbooks/view.html',
                          workbook=workbook,
                          items=items,
                          templates=templates,
                          institution=institution)


@workbooks_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑题册"""
    workbook = Workbook.query.get_or_404(id)
    
    if request.method == 'POST':
        workbook.name = request.form.get('name', '').strip()
        workbook.description = request.form.get('description', '').strip()
        workbook.category = request.form.get('category', '')
        
        db.session.commit()
        flash('题册更新成功', 'success')
        return redirect(url_for('workbooks.view', id=id))
    
    # 获取已添加的题目
    items = workbook.items.order_by(WorkbookItem.order).all()
    
    # 获取可添加的题目（排除已添加的）
    added_ids = [item.question_id for item in items]
    if added_ids:
        questions = Question.query.filter(~Question.id.in_(added_ids)).order_by(Question.id.desc()).limit(100).all()
    else:
        questions = Question.query.order_by(Question.id.desc()).limit(100).all()
    
    categories = db.session.query(Question.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('workbooks/edit.html',
                          workbook=workbook,
                          items=items,
                          questions=questions,
                          categories=categories)


@workbooks_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除题册"""
    workbook = Workbook.query.get_or_404(id)
    db.session.delete(workbook)
    db.session.commit()
    
    flash(f'题册 "{workbook.name}" 已删除', 'success')
    return redirect(url_for('workbooks.index'))


@workbooks_bp.route('/<int:id>/add_questions', methods=['POST'])
@login_required
def add_questions(id):
    """添加题目到题册"""
    workbook = Workbook.query.get_or_404(id)
    question_ids = request.form.getlist('question_ids')
    
    current_order = workbook.items.count()
    
    for qid in question_ids:
        # 检查是否已存在
        existing = WorkbookItem.query.filter_by(workbook_id=id, question_id=int(qid)).first()
        if not existing:
            current_order += 1
            item = WorkbookItem(
                workbook_id=workbook.id,
                question_id=int(qid),
                order=current_order
            )
            db.session.add(item)
    
    workbook.update_question_count()
    db.session.commit()
    
    flash(f'已添加 {len(question_ids)} 道题目', 'success')
    return redirect(url_for('workbooks.edit', id=id))


@workbooks_bp.route('/<int:id>/remove_question/<int:item_id>', methods=['POST'])
@login_required
def remove_question(id, item_id):
    """从题册移除题目"""
    item = WorkbookItem.query.get_or_404(item_id)
    
    if item.workbook_id != id:
        flash('操作无效', 'error')
        return redirect(url_for('workbooks.edit', id=id))
    
    db.session.delete(item)
    
    # 重新排序
    workbook = Workbook.query.get(id)
    items = workbook.items.order_by(WorkbookItem.order).all()
    for i, itm in enumerate(items, 1):
        itm.order = i
    
    workbook.update_question_count()
    db.session.commit()
    
    flash('题目已移除', 'success')
    return redirect(url_for('workbooks.edit', id=id))


@workbooks_bp.route('/<int:id>/generate', methods=['POST'])
@login_required
def generate_pdf(id):
    """生成PDF"""
    workbook = Workbook.query.get_or_404(id)
    embed_mode = request.form.get('embed_mode', 'standard')
    
    try:
        if embed_mode == 'by_category':
            # 按分类生成模式（每个分类一个二维码）
            from app.services.question.generator import generate_workbook_pdf_by_category
            pdf_path = generate_workbook_pdf_by_category(workbook)
        elif embed_mode == 'single_qr':
            # 单二维码模式（整本题册一个二维码）
            from app.services.question.generator import generate_workbook_pdf_single_qr
            pdf_path = generate_workbook_pdf_single_qr(workbook)
        elif embed_mode.startswith('enhance_'):
            # 增强模式：在原PDF/Word上添加封面和二维码
            from app.services.question.generator import enhance_existing_pdf
            from werkzeug.utils import secure_filename
            import uuid
            
            # 优先处理上传的文件
            uploaded_file = request.files.get('source_file')
            source_file = request.form.get('source_pdf', '')
            
            if uploaded_file and uploaded_file.filename:
                filename = uploaded_file.filename
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext not in ('pdf', 'doc', 'docx'):
                    raise ValueError("仅支持 PDF、DOC、DOCX 格式的文件")
                
                upload_dir = os.path.join(current_app.root_path, '..', 'data/uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
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
            
            # 解析分类范围
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
            from app.services.question.generator import generate_workbook_pdf
            pdf_path = generate_workbook_pdf(workbook)
        
        workbook.pdf_path = pdf_path
        db.session.commit()
        
        flash('PDF生成成功', 'success')
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'PDF生成失败: {str(e)}', 'error')
    
    return redirect(url_for('workbooks.view', id=id))


@workbooks_bp.route('/<int:id>/download')
@login_required
def download_pdf(id):
    """下载PDF"""
    workbook = Workbook.query.get_or_404(id)
    
    if not workbook.pdf_path:
        flash('PDF文件不存在，请先生成', 'error')
        return redirect(url_for('workbooks.view', id=id))
    
    # 处理相对路径和绝对路径
    pdf_path = workbook.pdf_path
    if not os.path.isabs(pdf_path):
        # 相对路径，基于app目录
        pdf_path = os.path.join(current_app.root_path, '..', pdf_path)
    
    if not os.path.exists(pdf_path):
        flash('PDF文件不存在，请重新生成', 'error')
        return redirect(url_for('workbooks.view', id=id))
    
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{workbook.name}.pdf'
    )


# ==================== 模板管理 ====================

@workbooks_bp.route('/templates')
@login_required
def templates():
    """模板列表"""
    templates = WorkbookTemplate.query.all()
    return render_template('workbooks/templates.html', templates=templates)


@workbooks_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """创建模板"""
    if request.method == 'POST':
        template = WorkbookTemplate(
            name=request.form.get('name'),
            answer_mode=request.form.get('answer_mode', 'hidden'),
            questions_per_page=request.form.get('questions_per_page', 5, type=int),
            brand_enabled=request.form.get('brand_enabled') == 'on',
            show_cover=request.form.get('show_cover') == 'on',
            show_qrcode=request.form.get('show_qrcode') == 'on'
        )
        db.session.add(template)
        db.session.commit()
        
        flash('模板创建成功', 'success')
        return redirect(url_for('workbooks.templates'))
    
    return render_template('workbooks/template_form.html', template=None)


# ==================== 机构设置 ====================

@workbooks_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """机构设置"""
    institution = Institution.get_instance()
    
    if request.method == 'POST':
        institution.name = request.form.get('name', '').strip()
        institution.slogan = request.form.get('slogan', '').strip()
        institution.phone = request.form.get('phone', '').strip()
        institution.wechat = request.form.get('wechat', '').strip()
        institution.address = request.form.get('address', '').strip()
        institution.website = request.form.get('website', '').strip()
        institution.primary_color = request.form.get('primary_color', '#1a73e8')
        institution.secondary_color = request.form.get('secondary_color', '#34a853')
        institution.header_text = request.form.get('header_text', '').strip()
        institution.footer_text = request.form.get('footer_text', '').strip()
        
        db.session.commit()
        flash('机构设置已更新', 'success')
        return redirect(url_for('workbooks.settings'))
    
    return render_template('workbooks/settings.html', institution=institution)
