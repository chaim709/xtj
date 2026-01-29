# -*- coding: utf-8 -*-
"""
图形推理习题册生成器 - 嵌入原始图片版本
用于生成包含图片的PDF习题册
"""
import os
import uuid
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
from flask import current_app

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, KeepTogether, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app import db
from app.models import Workbook, WorkbookItem, WorkbookPage, Institution, WorkbookTemplate
from app.utils.generator import (
    CHINESE_FONT, CHINESE_FONT_BOLD, hex_to_color, 
    generate_qr_image, HorizontalLine, create_cover_page
)

# 图形推理700题的图片目录
TUXING_IMAGES_DIR = 'data/parsed/图形推理700题/images'


def get_question_image_path(question):
    """
    获取题目对应的图片路径
    对于图形推理700题，根据题号计算所在页面
    """
    if not question.uid or not question.uid.startswith('TX700-'):
        return None
    
    try:
        # 从UID提取题号: TX700-001 -> 1
        q_num = int(question.uid.split('-')[1])
        
        # 计算页码：每页约3题，从第7页开始
        # 题目1-3在第7页，4-6在第8页...
        page_num = 7 + (q_num - 1) // 3
        
        image_path = os.path.join(
            current_app.root_path, '..', 
            TUXING_IMAGES_DIR, 
            f'page_{page_num:03d}.png'
        )
        
        if os.path.exists(image_path):
            return image_path
        
        return None
    except:
        return None


def crop_question_from_page(image_path, question_num, questions_per_page=3):
    """
    从整页图片中裁剪出单个题目区域
    
    Args:
        image_path: 整页图片路径
        question_num: 题目在PDF中的绝对编号 (1-700)
        questions_per_page: 每页题目数量
    
    Returns:
        BytesIO 对象包含裁剪后的图片
    """
    try:
        img = PILImage.open(image_path)
        width, height = img.size
        
        # 计算题目在当前页的位置 (0, 1, 2)
        position_in_page = (question_num - 1) % questions_per_page
        
        # 页面布局：
        # - 顶部标题区：约8%
        # - 题目区：约82%（3题平分）
        # - 底部页码区：约10%
        
        header_ratio = 0.08
        footer_ratio = 0.10
        content_ratio = 1 - header_ratio - footer_ratio
        
        # 每个题目的高度
        question_height_ratio = content_ratio / questions_per_page
        
        # 计算裁剪区域
        top = int(height * (header_ratio + position_in_page * question_height_ratio))
        bottom = int(height * (header_ratio + (position_in_page + 1) * question_height_ratio))
        
        # 左右边距保留
        left_margin = int(width * 0.03)
        right_margin = int(width * 0.03)
        
        # 裁剪
        cropped = img.crop((left_margin, top, width - right_margin, bottom))
        
        # 保存到BytesIO
        buffer = BytesIO()
        cropped.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"裁剪图片失败: {e}")
        return None


def create_image_question_block(item, template, styles, image_buffer=None, image_path=None):
    """
    创建带图片的题目块
    
    可以传入裁剪后的image_buffer，或者整页的image_path
    """
    q = item.question
    primary_color = hex_to_color('#1a73e8')
    
    elements = []
    
    # 题目样式
    stem_style = ParagraphStyle(
        'Stem',
        fontName=CHINESE_FONT,
        fontSize=template.stem_font_size if template else 12,
        leading=(template.stem_font_size if template else 12) + 4,
        spaceBefore=8,
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        'Meta',
        fontName=CHINESE_FONT,
        fontSize=9,
        textColor=colors.grey
    )
    
    # 题号和来源
    stem_parts = q.stem.split('] ')
    if len(stem_parts) > 1:
        source_info = stem_parts[1].split(' - ')[0] if ' - ' in stem_parts[1] else ''
    else:
        source_info = ''
    
    stem_text = f"<b>{item.order}.</b> {source_info}"
    
    # 元信息
    meta_parts = []
    if template and template.show_category and q.category:
        meta_parts.append(f"[{q.category}]")
    if template and template.show_difficulty and q.difficulty:
        meta_parts.append(f"难度：{q.difficulty}")
    
    meta_text = ' '.join(meta_parts)
    
    if meta_text:
        header_table = Table([
            [
                Paragraph(stem_text, stem_style),
                Paragraph(meta_text, meta_style)
            ]
        ], colWidths=[13*cm, 4*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(header_table)
    else:
        elements.append(Paragraph(stem_text, stem_style))
    
    # 嵌入图片
    if image_buffer:
        # 从裁剪后的buffer加载
        try:
            img = Image(image_buffer, width=16*cm, height=6*cm)
            img.hAlign = 'CENTER'
            elements.append(img)
        except Exception as e:
            elements.append(Paragraph(f"[图片加载失败: {e}]", meta_style))
    elif image_path and os.path.exists(image_path):
        # 从整页图片加载并裁剪
        try:
            # 获取题目编号
            q_num = int(q.uid.split('-')[1]) if q.uid else 0
            cropped = crop_question_from_page(image_path, q_num)
            if cropped:
                img = Image(cropped, width=16*cm, height=6*cm)
                img.hAlign = 'CENTER'
                elements.append(img)
            else:
                elements.append(Paragraph("[图片裁剪失败]", meta_style))
        except Exception as e:
            elements.append(Paragraph(f"[图片处理失败: {e}]", meta_style))
    else:
        # 无图片，显示提示
        placeholder_style = ParagraphStyle(
            'Placeholder',
            fontName=CHINESE_FONT,
            fontSize=10,
            textColor=colors.grey,
            alignment=1,
            spaceBefore=20,
            spaceAfter=20
        )
        elements.append(Paragraph("[请参考原始题册查看图形]", placeholder_style))
    
    # 选项（如果有的话，图形推理通常选项也是图形，已包含在图片中）
    # 答案提示
    if template and template.answer_mode == 'inline':
        answer_style = ParagraphStyle(
            'Answer',
            fontName=CHINESE_FONT,
            fontSize=10,
            textColor=hex_to_color('#16a34a'),
            spaceBefore=6
        )
        elements.append(Paragraph(f"<b>答案：{q.answer}</b>", answer_style))
    
    elements.append(Spacer(1, 0.3*cm))
    
    return elements


def generate_image_workbook_pdf(workbook, template_id=None, embed_images=True):
    """
    生成包含图片的习题册PDF
    
    Args:
        workbook: Workbook对象
        template_id: 模板ID
        embed_images: 是否嵌入图片
    
    Returns:
        生成的PDF文件路径
    """
    from app.utils.generator import (
        create_page_header, create_page_footer, 
        create_qr_block, create_answer_page
    )
    
    items = workbook.items.order_by(WorkbookItem.order).all()
    
    if not items:
        raise ValueError("题册中没有题目")
    
    # 获取配置
    institution = Institution.get_instance()
    
    if template_id:
        template = WorkbookTemplate.query.get(template_id)
    elif workbook.template_id:
        template = WorkbookTemplate.query.get(workbook.template_id)
    else:
        template = WorkbookTemplate.get_default()
    
    # 对于图形推理题，每页只放2题（因为图片较大）
    has_image_questions = any(
        item.question.uid and item.question.uid.startswith('TX700-') 
        for item in items
    )
    
    questions_per_page = 2 if has_image_questions else (template.questions_per_page if template else 5)
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5005')
    
    # 计算页数
    total_questions = len(items)
    total_pages = (total_questions + questions_per_page - 1) // questions_per_page
    
    # 更新题册信息
    workbook.total_questions = total_questions
    workbook.total_pages = total_pages
    if template:
        workbook.template_id = template.id
        workbook.answer_mode = template.answer_mode
    
    # 清除旧的页面数据
    WorkbookPage.query.filter_by(workbook_id=workbook.id).delete()
    
    # 创建PDF
    output_dir = current_app.config.get('OUTPUT_FOLDER', 'data/output')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{workbook.name}_{workbook.id}_images.pdf"
    filepath = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # 封面页
    if template and template.show_cover and template.brand_enabled:
        story.extend(create_cover_page(workbook, institution, template, styles))
    
    # 内容页
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * questions_per_page
        end_idx = min(start_idx + questions_per_page, total_questions)
        
        page_items = items[start_idx:end_idx]
        
        start_order = page_items[0].order
        end_order = page_items[-1].order
        
        # 生成二维码标识
        qr_code = str(uuid.uuid4())[:8]
        
        # 保存页面数据
        page = WorkbookPage(
            workbook_id=workbook.id,
            page_num=page_num,
            start_order=start_order,
            end_order=end_order,
            qr_code=qr_code
        )
        db.session.add(page)
        
        # 更新题目的页码
        for item in page_items:
            item.page_num = page_num
        
        # 页眉
        if template and template.brand_enabled:
            story.append(create_page_header(workbook, institution, page_num, total_pages, template, styles))
            story.append(Spacer(1, 0.2*cm))
        
        # 题目内容
        for item in page_items:
            q = item.question
            
            # 检查是否为图形推理题
            if embed_images and q.uid and q.uid.startswith('TX700-'):
                image_path = get_question_image_path(q)
                story.extend(create_image_question_block(item, template, styles, image_path=image_path))
            else:
                # 使用标准题目块
                from app.utils.generator import create_question_block
                story.extend(create_question_block(item, template, styles))
        
        # 二维码区域
        story.extend(create_qr_block(qr_code, start_order, end_order, base_url, template, institution))
        
        # 页脚
        if template and template.brand_enabled:
            story.append(Spacer(1, 0.2*cm))
            story.append(create_page_footer(institution, page_num, template))
        
        # 分页
        if page_num < total_pages:
            story.append(PageBreak())
    
    # 答案页（separated模式）
    if template and template.answer_mode == 'separated':
        story.append(PageBreak())
        story.extend(create_answer_page(items, workbook, institution, styles))
    
    workbook.pdf_path = filepath
    db.session.commit()
    
    # 生成PDF
    doc.build(story)
    
    return filepath


def generate_full_page_workbook(workbook, source_images_dir, template_id=None):
    """
    生成整页图片的习题册
    每页显示原PDF的一整页，附带题号索引
    
    适用于图形密集型题库（如图形推理700题）
    """
    from app.utils.generator import create_page_header, create_page_footer, generate_qr_image
    
    institution = Institution.get_instance()
    
    if template_id:
        template = WorkbookTemplate.query.get(template_id)
    else:
        template = WorkbookTemplate.get_default()
    
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5005')
    
    # 获取所有图片
    image_files = sorted([
        f for f in os.listdir(source_images_dir) 
        if f.endswith('.png') and f.startswith('page_')
    ])
    
    if not image_files:
        raise ValueError("没有找到图片文件")
    
    # 创建PDF
    output_dir = current_app.config.get('OUTPUT_FOLDER', 'data/output')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{workbook.name}_{workbook.id}_fullpage.pdf"
    filepath = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=0.5*cm,
        leftMargin=0.5*cm,
        topMargin=0.5*cm,
        bottomMargin=0.5*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # 每个原始页面3题
    questions_per_source_page = 3
    
    for i, img_file in enumerate(image_files):
        img_path = os.path.join(source_images_dir, img_file)
        
        # 计算题号范围
        # 从文件名提取页码: page_007.png -> 7
        try:
            source_page = int(img_file.split('_')[1].split('.')[0])
            # 第7页是第1-3题，第8页是第4-6题...
            start_q = (source_page - 7) * 3 + 1
            end_q = start_q + 2
        except:
            start_q = i * 3 + 1
            end_q = start_q + 2
        
        # 页面标题
        header_style = ParagraphStyle(
            'PageHeader',
            fontName=CHINESE_FONT,
            fontSize=10,
            textColor=colors.grey,
            alignment=1
        )
        story.append(Paragraph(
            f"题目 {start_q} - {end_q}",
            header_style
        ))
        story.append(Spacer(1, 0.2*cm))
        
        # 嵌入整页图片
        try:
            img = Image(img_path, width=19*cm, height=26*cm)
            img.hAlign = 'CENTER'
            story.append(img)
        except Exception as e:
            story.append(Paragraph(f"[图片加载失败: {img_file}]", header_style))
        
        # 分页
        if i < len(image_files) - 1:
            story.append(PageBreak())
    
    workbook.pdf_path = filepath
    db.session.commit()
    
    # 生成PDF
    doc.build(story)
    
    return filepath
