# -*- coding: utf-8 -*-
"""题册生成器 - 专业PDF模板"""
import os
import re
import uuid
import qrcode
from io import BytesIO
from datetime import datetime
from flask import current_app
from app import db
from app.models import Workbook, WorkbookItem, WorkbookPage, Institution, WorkbookTemplate, Question

# reportlab
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
from reportlab.graphics.shapes import Drawing, Line

# 注册中文字体
CHINESE_FONT = 'Helvetica'
CHINESE_FONT_BOLD = 'Helvetica-Bold'

try:
    # macOS 系统字体
    pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
    CHINESE_FONT = 'PingFang'
    CHINESE_FONT_BOLD = 'PingFang'
except:
    try:
        pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Light.ttc'))
        CHINESE_FONT = 'STHeiti'
        CHINESE_FONT_BOLD = 'STHeiti'
    except:
        pass


class HorizontalLine(Flowable):
    """水平分隔线"""
    def __init__(self, width, color=colors.lightgrey, thickness=0.5):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
    
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)
    
    def wrap(self, availWidth, availHeight):
        return (self.width, self.thickness + 2)


def hex_to_color(hex_str):
    """将十六进制颜色转换为reportlab颜色"""
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return colors.Color(r, g, b)


def generate_qr_image(url, size=100):
    """生成二维码图片"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


def create_cover_page(workbook, institution, template, styles):
    """创建封面页 - 独立首页，不与题目内容重叠"""
    story = []
    
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    secondary_color = hex_to_color(institution.secondary_color or '#34a853')
    
    # 获取题目数量
    items = workbook.items.all()
    total_questions = len(items)
    
    # ========== 封面顶部区域 ==========
    # 顶部空白（稍微减少）
    story.append(Spacer(1, 2.5*cm))
    
    # Logo 或 机构名称
    if institution.logo_path and os.path.exists(institution.logo_path):
        try:
            logo = Image(institution.logo_path, width=5*cm, height=2.5*cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.8*cm))
        except:
            # Logo加载失败时显示机构名称
            name_style = ParagraphStyle(
                'InstitutionName',
                fontName=CHINESE_FONT_BOLD,
                fontSize=26,
                textColor=primary_color,
                alignment=1,
                spaceAfter=8
            )
            story.append(Paragraph(institution.name or '培训机构', name_style))
    else:
        # 无Logo时显示机构名称
        name_style = ParagraphStyle(
            'InstitutionName',
            fontName=CHINESE_FONT_BOLD,
            fontSize=26,
            textColor=primary_color,
            alignment=1,
            spaceAfter=8
        )
        story.append(Paragraph(institution.name or '培训机构', name_style))
    
    # 标语（如果有）
    if institution.slogan:
        slogan_style = ParagraphStyle(
            'Slogan',
            fontName=CHINESE_FONT,
            fontSize=12,
            textColor=colors.grey,
            alignment=1,
            spaceAfter=15
        )
        story.append(Paragraph(institution.slogan, slogan_style))
    
    # ========== 分隔线 ==========
    story.append(Spacer(1, 1.5*cm))
    story.append(HorizontalLine(14*cm, primary_color, 2))
    story.append(Spacer(1, 1.5*cm))
    
    # ========== 习题册信息区域 ==========
    # 习题册标题
    title_style = ParagraphStyle(
        'WorkbookTitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=28,
        textColor=colors.black,
        alignment=1,
        spaceAfter=15
    )
    story.append(Paragraph(workbook.name, title_style))
    
    # 分类标签
    if workbook.category:
        cat_style = ParagraphStyle(
            'Category',
            fontName=CHINESE_FONT,
            fontSize=14,
            textColor=primary_color,
            alignment=1,
            spaceAfter=8
        )
        story.append(Paragraph(f"【{workbook.category}】", cat_style))
    
    # 描述（限制长度避免溢出）
    if workbook.description:
        desc_text = workbook.description[:100] + ('...' if len(workbook.description) > 100 else '')
        desc_style = ParagraphStyle(
            'Description',
            fontName=CHINESE_FONT,
            fontSize=11,
            textColor=colors.grey,
            alignment=1,
            spaceAfter=20,
            leading=16
        )
        story.append(Paragraph(desc_text, desc_style))
    
    # ========== 统计信息框 ==========
    story.append(Spacer(1, 1.5*cm))
    
    # 创建信息表格
    info_style = ParagraphStyle(
        'Info',
        fontName=CHINESE_FONT,
        fontSize=12,
        textColor=colors.black,
        alignment=1
    )
    
    info_label_style = ParagraphStyle(
        'InfoLabel',
        fontName=CHINESE_FONT,
        fontSize=10,
        textColor=colors.grey,
        alignment=1
    )
    
    info_table = Table([
        [
            Paragraph(f"<b>{total_questions}</b>", info_style),
            Paragraph(f"<b>{workbook.total_pages or ((total_questions + 4) // 5)}</b>", info_style),
            Paragraph(f"<b>{template.questions_per_page if template else 5}</b>", info_style)
        ],
        [
            Paragraph("题目总数", info_label_style),
            Paragraph("总页数", info_label_style),
            Paragraph("每页题数", info_label_style)
        ]
    ], colWidths=[5*cm, 5*cm, 5*cm])
    
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.99)),
        ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.9, 0.9, 0.92)),
    ]))
    
    story.append(info_table)
    
    # ========== 生成日期 ==========
    story.append(Spacer(1, 1.5*cm))
    
    date_style = ParagraphStyle(
        'Date',
        fontName=CHINESE_FONT,
        fontSize=10,
        textColor=colors.darkgrey,
        alignment=1
    )
    story.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}", date_style))
    
    # ========== 底部联系方式 ==========
    story.append(Spacer(1, 2*cm))
    
    contact_parts = []
    if institution.phone:
        contact_parts.append(f"电话：{institution.phone}")
    if institution.wechat:
        contact_parts.append(f"微信：{institution.wechat}")
    if institution.website:
        contact_parts.append(f"网站：{institution.website}")
    
    if contact_parts:
        contact_style = ParagraphStyle(
            'Contact',
            fontName=CHINESE_FONT,
            fontSize=9,
            textColor=colors.grey,
            alignment=1
        )
        story.append(Paragraph(' | '.join(contact_parts), contact_style))
    
    # ========== 强制分页 ==========
    # 确保封面页独立，题目从新页开始
    story.append(PageBreak())
    
    return story


def create_page_header(workbook, institution, page_num, total_pages, template, styles, qr_block=None):
    """创建页眉 - 集成二维码到右上角"""
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    
    # 左侧：题册名称
    title_style = ParagraphStyle(
        'HeaderTitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=10,
        textColor=primary_color
    )
    
    # 中间：机构名称 + 页码
    inst_style = ParagraphStyle(
        'HeaderInst',
        fontName=CHINESE_FONT,
        fontSize=8,
        textColor=colors.Color(0.5, 0.5, 0.5),
        alignment=1
    )
    
    inst_text = institution.name or ''
    page_info = f"第{page_num}/{total_pages}页"
    center_text = f"{inst_text}  {page_info}" if inst_text else page_info
    
    if qr_block is not None:
        # 带二维码的页眉：左侧标题 + 中间信息 + 右侧二维码
        header_table = Table([
            [
                Paragraph(workbook.name, title_style),
                Paragraph(center_text, inst_style),
                qr_block
            ]
        ], colWidths=[6*cm, 6*cm, 5*cm])
        
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, primary_color),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        # 无二维码的页眉
        page_style = ParagraphStyle(
            'HeaderPage',
            fontName=CHINESE_FONT,
            fontSize=9,
            textColor=colors.Color(0.5, 0.5, 0.5),
            alignment=2
        )
        
        header_table = Table([
            [
                Paragraph(workbook.name, title_style),
                Paragraph(inst_text, inst_style),
                Paragraph(page_info, page_style)
            ]
        ], colWidths=[7*cm, 6*cm, 4*cm])
        
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, primary_color),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
    
    return header_table


def create_page_footer(institution, page_num, template, qr_block=None):
    """创建页脚 - 集成二维码"""
    footer_text = institution.footer_text or ''
    if not footer_text and institution.phone:
        footer_text = f"咨询热线：{institution.phone}"
    
    footer_style = ParagraphStyle(
        'Footer',
        fontName=CHINESE_FONT,
        fontSize=8,
        textColor=colors.Color(0.5, 0.5, 0.5),
        alignment=0
    )
    
    if qr_block is not None:
        # 带二维码的页脚：左侧文字 + 右侧二维码
        footer_table = Table([
            [
                Paragraph(footer_text, footer_style),
                qr_block
            ]
        ], colWidths=[11.5*cm, 5.5*cm])
        
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        return footer_table
    else:
        # 无二维码的页脚
        footer_style.alignment = 1
        return Paragraph(footer_text, footer_style)


def create_question_block(item, template, styles):
    """创建单个题目块 - 优化版排版"""
    q = item.question
    
    primary_color = hex_to_color('#1a73e8')
    
    # 获取字体大小设置
    stem_font_size = template.stem_font_size if template else 11
    option_font_size = template.option_font_size if template else 10
    
    # 题号样式 - 使用醒目的蓝色
    number_style = ParagraphStyle(
        'QuestionNumber',
        fontName=CHINESE_FONT_BOLD,
        fontSize=stem_font_size + 1,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4
    )
    
    # 题干样式 - 清晰易读
    stem_style = ParagraphStyle(
        'Stem',
        fontName=CHINESE_FONT,
        fontSize=stem_font_size,
        leading=stem_font_size + 6,  # 增加行高，提高可读性
        spaceBefore=2,
        spaceAfter=8,
        firstLineIndent=0
    )
    
    # 选项样式 - 适当缩进
    option_style = ParagraphStyle(
        'Option',
        fontName=CHINESE_FONT,
        fontSize=option_font_size,
        leading=option_font_size + 5,
        leftIndent=0.5*cm,
        spaceBefore=2,
        spaceAfter=2
    )
    
    # 分类标签样式
    tag_style = ParagraphStyle(
        'Tag',
        fontName=CHINESE_FONT,
        fontSize=8,
        textColor=colors.white,
        alignment=1
    )
    
    elements = []
    
    # ========== 题号行 ==========
    # 显示题号，可选显示分类标签
    number_text = f"<b>第 {item.order} 题</b>"
    
    # 构建题号和分类信息
    if template and (template.show_category or template.show_knowledge_point):
        tag_parts = []
        if template.show_category and q.subcategory:
            tag_parts.append(q.subcategory)
        elif template.show_category and q.category:
            tag_parts.append(q.category)
        if template.show_knowledge_point and q.knowledge_point:
            tag_parts.append(q.knowledge_point)
        
        if tag_parts:
            tag_text = ' · '.join(tag_parts)
            # 创建带标签的题号行
            number_table = Table([
                [
                    Paragraph(number_text, number_style),
                    Paragraph(f"<font color='#6b7280' size='8'>{tag_text}</font>", 
                              ParagraphStyle('TagLine', fontName=CHINESE_FONT, fontSize=8, 
                                           textColor=colors.grey, alignment=2))
                ]
            ], colWidths=[4*cm, 13*cm])
            number_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(number_table)
        else:
            elements.append(Paragraph(number_text, number_style))
    else:
        elements.append(Paragraph(number_text, number_style))
    
    # ========== 题干 ==========
    # 清理题干文本，确保格式正确
    stem_text = q.stem or ''
    # 将多个连续空格转换为下划线（选词填空题的横线）
    stem_text = re.sub(r' {4,}', '____', stem_text)
    stem_text = re.sub(r'（\s*）', '（____）', stem_text)  # 处理空括号
    # 处理可能的特殊字符
    stem_text = stem_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    elements.append(Paragraph(stem_text, stem_style))
    
    # ========== 选项 ==========
    options_data = [
        ('A', q.option_a),
        ('B', q.option_b),
        ('C', q.option_c),
        ('D', q.option_d)
    ]
    
    # 过滤有效选项
    valid_options = [(letter, content) for letter, content in options_data if content]
    
    if valid_options:
        # 判断选项长度，决定布局方式
        max_option_length = max(len(content or '') for _, content in valid_options)
        
        if max_option_length <= 15 and len(valid_options) == 4:
            # 短选项：两列布局
            option_rows = []
            for i in range(0, len(valid_options), 2):
                row = []
                for j in range(2):
                    if i + j < len(valid_options):
                        letter, content = valid_options[i + j]
                        content = (content or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        opt_text = f"<b>{letter}.</b> {content}"
                        row.append(Paragraph(opt_text, option_style))
                    else:
                        row.append(Paragraph('', option_style))
                option_rows.append(row)
            
            option_table = Table(option_rows, colWidths=[8.5*cm, 8.5*cm])
        else:
            # 长选项：单列布局
            option_rows = []
            for letter, content in valid_options:
                content = (content or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                opt_text = f"<b>{letter}.</b> {content}"
                option_rows.append([Paragraph(opt_text, option_style)])
            
            option_table = Table(option_rows, colWidths=[17*cm])
        
        option_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(option_table)
    
    # ========== 答案和解析（仅inline模式）==========
    if template and template.answer_mode == 'inline':
        answer_box_style = ParagraphStyle(
            'AnswerBox',
            fontName=CHINESE_FONT,
            fontSize=10,
            textColor=hex_to_color('#166534'),
            leftIndent=0.5*cm,
            spaceBefore=8,
            spaceAfter=4,
            backColor=colors.Color(0.95, 0.99, 0.95)
        )
        
        answer_text = f"<b>【答案】{q.answer}</b>"
        elements.append(Paragraph(answer_text, answer_box_style))
        
        if q.analysis:
            analysis_style = ParagraphStyle(
                'Analysis',
                fontName=CHINESE_FONT,
                fontSize=9,
                textColor=colors.Color(0.4, 0.4, 0.4),
                leftIndent=0.5*cm,
                leading=13,
                spaceAfter=4
            )
            # 限制解析长度
            analysis_text = q.analysis[:300] + ('...' if len(q.analysis or '') > 300 else '')
            analysis_text = analysis_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(f"【解析】{analysis_text}", analysis_style))
    
    # ========== 分隔线 ==========
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HorizontalLine(17*cm, colors.Color(0.92, 0.92, 0.92), 0.5))
    elements.append(Spacer(1, 0.2*cm))
    
    return elements


def create_qr_block(qr_code, start_order, end_order, base_url, template, institution, compact=True):
    """创建二维码区块
    
    Args:
        compact: True=紧凑模式(页脚内嵌), False=独立区块模式
    """
    if template and not template.show_qrcode:
        return []
    
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    
    qr_url = f"{base_url}/h5/scan/{qr_code}"
    
    if compact:
        # ========== 紧凑模式：适合页脚，不额外占用空间 ==========
        qr_buffer = generate_qr_image(qr_url, 80)
        qr_img = Image(qr_buffer, width=1.5*cm, height=1.5*cm)
        
        # 简洁文字样式
        qr_text_style = ParagraphStyle(
            'QRTextCompact',
            fontName=CHINESE_FONT,
            fontSize=8,
            textColor=colors.Color(0.5, 0.5, 0.5),
            leading=11
        )
        
        # 紧凑布局：二维码 + 简短说明
        qr_table = Table([
            [
                qr_img,
                Paragraph(
                    f"<b>扫码提交错题</b><br/>"
                    f"第{start_order}-{end_order}题",
                    qr_text_style
                )
            ]
        ], colWidths=[1.8*cm, 3.5*cm])
        
        qr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        return qr_table  # 返回表格对象，供页脚集成
    
    else:
        # ========== 独立区块模式：占用单独区域 ==========
        qr_buffer = generate_qr_image(qr_url, 100)
        qr_img = Image(qr_buffer, width=2*cm, height=2*cm)
        
        qr_title_style = ParagraphStyle(
            'QRTitle',
            fontName=CHINESE_FONT_BOLD,
            fontSize=11,
            textColor=primary_color,
            spaceAfter=4
        )
        
        qr_desc_style = ParagraphStyle(
            'QRDesc',
            fontName=CHINESE_FONT,
            fontSize=9,
            textColor=colors.Color(0.5, 0.5, 0.5),
            leading=13
        )
        
        text_content = [
            Paragraph("扫码提交错题", qr_title_style),
            Paragraph(f"本页题目：第 {start_order} - {end_order} 题", qr_desc_style),
            Paragraph("做完后扫码勾选错题，即可查看答案解析", qr_desc_style)
        ]
        
        text_table = Table([[p] for p in text_content], colWidths=[13*cm])
        text_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        qr_table = Table([
            [qr_img, text_table]
        ], colWidths=[2.5*cm, 14.5*cm])
        
        try:
            bg_color = colors.Color(
                int(institution.primary_color[1:3], 16) / 255.0 * 0.08 + 0.96,
                int(institution.primary_color[3:5], 16) / 255.0 * 0.08 + 0.96,
                int(institution.primary_color[5:7], 16) / 255.0 * 0.08 + 0.96
            ) if institution.primary_color else colors.Color(0.96, 0.97, 0.99)
        except:
            bg_color = colors.Color(0.96, 0.97, 0.99)
        
        qr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.90, 0.94)),
            ('LEFTPADDING', (0, 0), (0, 0), 12),
            ('LEFTPADDING', (1, 0), (1, 0), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        return [Spacer(1, 0.6*cm), qr_table]


def create_answer_page(items, workbook, institution, styles):
    """创建答案页"""
    story = []
    
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    
    # 标题
    title_style = ParagraphStyle(
        'AnswerTitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=18,
        textColor=primary_color,
        alignment=1,
        spaceAfter=20
    )
    story.append(Paragraph(f"{workbook.name} - 答案与解析", title_style))
    story.append(HorizontalLine(17*cm, primary_color, 1))
    story.append(Spacer(1, 0.5*cm))
    
    # 答案列表
    answer_style = ParagraphStyle(
        'AnswerItem',
        fontName=CHINESE_FONT,
        fontSize=10,
        leading=14,
        spaceBefore=6
    )
    
    analysis_style = ParagraphStyle(
        'Analysis',
        fontName=CHINESE_FONT,
        fontSize=9,
        textColor=colors.grey,
        leading=13,
        leftIndent=20,
        spaceAfter=8
    )
    
    for item in items:
        q = item.question
        
        # 题号 + 答案
        answer_text = f"<b>{item.order}. 答案：{q.answer}</b>"
        if q.category:
            answer_text += f"  <font color='#888888'>[{q.category}]</font>"
        
        story.append(Paragraph(answer_text, answer_style))
        
        # 解析
        if q.analysis:
            story.append(Paragraph(f"解析：{q.analysis}", analysis_style))
        
        story.append(HorizontalLine(17*cm, colors.Color(0.9, 0.9, 0.9), 0.3))
    
    return story


def generate_workbook_pdf(workbook, template_id=None):
    """生成题册PDF"""
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
    
    questions_per_page = template.questions_per_page if template else 5
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
    
    # 获取现有页面数据（复用二维码，避免旧PDF失效）
    existing_pages = {p.page_num: p for p in WorkbookPage.query.filter_by(workbook_id=workbook.id).all()}
    
    # 创建PDF
    output_dir = current_app.config.get('OUTPUT_FOLDER', 'data/output')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{workbook.name}_{workbook.id}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.2*cm,
        leftMargin=1.2*cm,
        topMargin=1.2*cm,
        bottomMargin=1.2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # 封面页
    if template and template.show_cover and template.brand_enabled:
        story.extend(create_cover_page(workbook, institution, template, styles))
    
    # 记录需要保留的页面ID
    keep_page_ids = set()
    
    # 内容页
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * questions_per_page
        end_idx = min(start_idx + questions_per_page, total_questions)
        
        page_items = items[start_idx:end_idx]
        
        start_order = page_items[0].order
        end_order = page_items[-1].order
        
        # 复用或创建页面记录
        if page_num in existing_pages:
            # 复用现有页面，保持qr_code不变
            page = existing_pages[page_num]
            page.start_order = start_order
            page.end_order = end_order
            qr_code = page.qr_code
            keep_page_ids.add(page.id)
        else:
            # 创建新页面
            qr_code = str(uuid.uuid4())[:8]
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
        
        # 页眉（集成二维码到右上角）
        if template and template.brand_enabled:
            # 创建紧凑二维码（集成到页眉右上角）
            qr_block = None
            if template.show_qrcode:
                qr_block = create_qr_block(qr_code, start_order, end_order, base_url, template, institution, compact=True)
            story.append(create_page_header(workbook, institution, page_num, total_pages, template, styles, qr_block))
            story.append(Spacer(1, 0.3*cm))
        elif template and template.show_qrcode:
            # 如果不显示品牌但需要二维码，单独显示
            qr_elements = create_qr_block(qr_code, start_order, end_order, base_url, template, institution, compact=False)
            if isinstance(qr_elements, list):
                story.extend(qr_elements)
        
        # 题目内容
        for item in page_items:
            story.extend(create_question_block(item, template, styles))
        
        # 页脚（简洁版，只显示联系方式）
        if template and template.brand_enabled:
            story.append(Spacer(1, 0.2*cm))
            story.append(create_page_footer(institution, page_num, template, None))
        
        # 分页
        if page_num < total_pages:
            story.append(PageBreak())
    
    # 答案页（separated模式）
    if template and template.answer_mode == 'separated':
        story.append(PageBreak())
        story.extend(create_answer_page(items, workbook, institution, styles))
    
    # 删除多余的旧页面（如果页数减少了）
    for old_page_num, old_page in existing_pages.items():
        if old_page.id not in keep_page_ids:
            db.session.delete(old_page)
    
    workbook.pdf_path = filepath
    db.session.commit()
    
    # 生成PDF
    doc.build(story)
    
    return filepath


def generate_workbook_pdf_single_qr(workbook, template_id=None):
    """生成单二维码题册PDF - 整本题册只有一个二维码"""
    items = list(workbook.items.order_by(WorkbookItem.order).all())
    
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
    
    questions_per_page = template.questions_per_page if template else 8
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5005')
    
    # 计算页数
    total_questions = len(items)
    total_pages = (total_questions + questions_per_page - 1) // questions_per_page
    
    # 生成唯一二维码（整本题册共用）
    qr_code = f"WB{workbook.id}"
    
    # 清除旧页面数据，创建唯一页面记录
    WorkbookPage.query.filter_by(workbook_id=workbook.id).delete()
    
    page = WorkbookPage(
        workbook_id=workbook.id,
        page_num=1,
        start_order=1,
        end_order=total_questions,
        qr_code=qr_code
    )
    db.session.add(page)
    
    # 创建PDF
    output_dir = current_app.config.get('OUTPUT_FOLDER', 'data/output')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{workbook.name}_{workbook.id}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.2*cm,
        leftMargin=1.2*cm,
        topMargin=1.2*cm,
        bottomMargin=1.2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    
    # ========== 封面页（含二维码）==========
    if template and template.show_cover and template.brand_enabled:
        story.append(Spacer(1, 1*cm))
        
        # Logo和机构名
        if institution.name:
            name_style = ParagraphStyle(
                'InstitutionName',
                fontName=CHINESE_FONT_BOLD,
                fontSize=18,
                textColor=primary_color,
                alignment=1,
                spaceAfter=5
            )
            story.append(Paragraph(institution.name, name_style))
        
        if institution.slogan:
            slogan_style = ParagraphStyle(
                'Slogan',
                fontName=CHINESE_FONT,
                fontSize=10,
                textColor=colors.grey,
                alignment=1,
                spaceAfter=15
            )
            story.append(Paragraph(institution.slogan, slogan_style))
        
        story.append(HorizontalLine(17*cm, primary_color, 1))
        story.append(Spacer(1, 1*cm))
        
        # 题册标题
        title_style = ParagraphStyle(
            'WorkbookTitle',
            fontName=CHINESE_FONT_BOLD,
            fontSize=24,
            alignment=1,
            spaceAfter=20
        )
        story.append(Paragraph(workbook.name, title_style))
        
        # 统计信息
        info_style = ParagraphStyle(
            'Info',
            fontName=CHINESE_FONT,
            fontSize=12,
            textColor=colors.Color(0.4, 0.4, 0.4),
            alignment=1,
            spaceAfter=30
        )
        story.append(Paragraph(f"共 {total_questions} 题  |  {total_pages} 页", info_style))
        
        # 二维码（封面居中显示）
        if template.show_qrcode:
            qr_url = f"{base_url}/h5/scan/{qr_code}"
            qr_buffer = generate_qr_image(qr_url, 200)
            qr_img = Image(qr_buffer, width=5*cm, height=5*cm)
            
            qr_text_style = ParagraphStyle(
                'QRText',
                fontName=CHINESE_FONT,
                fontSize=11,
                textColor=colors.Color(0.4, 0.4, 0.4),
                alignment=1
            )
            
            qr_table = Table([
                [qr_img],
                [Paragraph("扫码提交错题 · 查看答案解析", qr_text_style)]
            ], colWidths=[8*cm])
            
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            centered = Table([[qr_table]], colWidths=[17*cm])
            centered.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            story.append(centered)
        
        story.append(Spacer(1, 1*cm))
        
        # 日期
        date_style = ParagraphStyle(
            'Date',
            fontName=CHINESE_FONT,
            fontSize=10,
            textColor=colors.grey,
            alignment=1
        )
        story.append(Paragraph(datetime.now().strftime('%Y年%m月'), date_style))
        
        story.append(PageBreak())
    
    # ========== 内容页 ==========
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * questions_per_page
        end_idx = min(start_idx + questions_per_page, total_questions)
        
        page_items = items[start_idx:end_idx]
        
        # 页眉（不含二维码，因为封面已有）
        if template and template.brand_enabled:
            story.append(create_page_header(workbook, institution, page_num, total_pages, template, styles, None))
            story.append(Spacer(1, 0.3*cm))
        
        # 题目内容
        for item in page_items:
            story.extend(create_question_block(item, template, styles))
        
        # 页脚
        if template and template.brand_enabled:
            story.append(Spacer(1, 0.2*cm))
            story.append(create_page_footer(institution, page_num, template, None))
        
        # 分页
        if page_num < total_pages:
            story.append(PageBreak())
    
    # 答案页
    if template and template.answer_mode == 'separated':
        story.append(PageBreak())
        story.extend(create_answer_page(items, workbook, institution, styles))
    
    # 更新题册信息
    workbook.total_questions = total_questions
    workbook.total_pages = total_pages
    workbook.pdf_path = filepath
    
    db.session.commit()
    
    # 生成PDF
    doc.build(story)
    
    return filepath


def generate_workbook_pdf_by_category(workbook, template_id=None):
    """生成按分类分组的题册PDF - 每个分类一个二维码"""
    items = list(workbook.items.order_by(WorkbookItem.order).all())
    
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
    
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5005')
    
    # 按分类分组题目
    category_items = {}
    category_order = []  # 保持分类顺序
    for item in items:
        q = item.question
        cat = q.subcategory or q.category or '未分类'
        if cat not in category_items:
            category_items[cat] = []
            category_order.append(cat)
        category_items[cat].append(item)
    
    # 清除旧的页面数据
    WorkbookPage.query.filter_by(workbook_id=workbook.id).delete()
    
    # 创建PDF
    output_dir = current_app.config.get('OUTPUT_FOLDER', 'data/output')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{workbook.name}_{workbook.id}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.2*cm,
        leftMargin=1.2*cm,
        topMargin=1.2*cm,
        bottomMargin=1.2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    
    # 封面页
    if template and template.show_cover and template.brand_enabled:
        story.extend(create_cover_page(workbook, institution, template, styles))
    
    # 分类标题样式
    category_title_style = ParagraphStyle(
        'CategoryTitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=16,
        textColor=primary_color,
        spaceBefore=20,
        spaceAfter=10,
        alignment=1
    )
    
    category_info_style = ParagraphStyle(
        'CategoryInfo',
        fontName=CHINESE_FONT,
        fontSize=11,
        textColor=colors.Color(0.4, 0.4, 0.4),
        alignment=1,
        spaceAfter=15
    )
    
    # 按分类生成内容
    total_categories = len(category_order)
    question_number = 0  # 重新编号
    
    for cat_idx, category in enumerate(category_order):
        cat_items = category_items[category]
        
        # 为该分类生成二维码
        qr_code = f"CAT{workbook.id}_{cat_idx}"
        
        # 计算该分类的题号范围
        start_order = question_number + 1
        end_order = question_number + len(cat_items)
        
        # 保存页面数据（每个分类一个）
        page = WorkbookPage(
            workbook_id=workbook.id,
            page_num=cat_idx + 1,
            start_order=start_order,
            end_order=end_order,
            qr_code=qr_code
        )
        db.session.add(page)
        
        # ========== 分类标题页 ==========
        story.append(PageBreak())
        story.append(Spacer(1, 2*cm))
        
        # 分类标题
        story.append(Paragraph(f"【 {category} 】", category_title_style))
        story.append(Paragraph(
            f"共 {len(cat_items)} 题  |  第 {start_order} - {end_order} 题  |  第 {cat_idx + 1}/{total_categories} 板块",
            category_info_style
        ))
        
        # 二维码
        if template and template.show_qrcode:
            qr_url = f"{base_url}/h5/scan/{qr_code}"
            qr_buffer = generate_qr_image(qr_url, 150)
            qr_img = Image(qr_buffer, width=4*cm, height=4*cm)
            
            qr_text_style = ParagraphStyle(
                'QRText',
                fontName=CHINESE_FONT,
                fontSize=10,
                textColor=colors.Color(0.5, 0.5, 0.5),
                alignment=1
            )
            
            qr_table = Table([
                [qr_img],
                [Paragraph("扫码提交本板块错题", qr_text_style)]
            ], colWidths=[6*cm])
            
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            # 居中显示二维码
            centered_table = Table([[qr_table]], colWidths=[17*cm])
            centered_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(Spacer(1, 1*cm))
            story.append(centered_table)
        
        story.append(PageBreak())
        
        # ========== 该分类的题目 ==========
        for item in cat_items:
            question_number += 1
            # 临时修改order为新编号
            original_order = item.order
            item.order = question_number
            
            story.extend(create_question_block(item, template, styles))
            
            # 恢复原order
            item.order = original_order
    
    # 更新题册信息
    workbook.total_questions = len(items)
    workbook.total_pages = total_categories
    workbook.pdf_path = filepath
    
    db.session.commit()
    
    # 生成PDF
    doc.build(story)
    
    return filepath


def convert_word_to_pdf(word_path, output_dir=None):
    """将Word文档转换为PDF
    
    支持多种转换方式：
    1. docx2pdf（需要Microsoft Word）
    2. LibreOffice
    3. 提示用户手动转换
    """
    import subprocess
    
    # 检查文件类型
    if not word_path.lower().endswith(('.doc', '.docx')):
        return word_path  # 已经是PDF或其他格式
    
    if output_dir is None:
        output_dir = os.path.dirname(word_path)
    
    pdf_path = os.path.join(output_dir, os.path.basename(word_path).rsplit('.', 1)[0] + '.pdf')
    
    # 检查是否已有同名PDF
    if os.path.exists(pdf_path):
        return pdf_path
    
    # 方法1: 使用docx2pdf（需要Microsoft Word）
    try:
        from docx2pdf import convert
        convert(word_path, pdf_path)
        if os.path.exists(pdf_path):
            return pdf_path
    except Exception as e:
        pass
    
    # 方法2: 使用LibreOffice
    libreoffice_paths = [
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
        '/usr/bin/libreoffice',
        '/usr/bin/soffice'
    ]
    
    for lo_path in libreoffice_paths:
        if os.path.exists(lo_path):
            try:
                subprocess.run([
                    lo_path, '--headless', '--convert-to', 'pdf',
                    '--outdir', output_dir, word_path
                ], check=True, capture_output=True)
                if os.path.exists(pdf_path):
                    return pdf_path
            except:
                pass
    
    # 方法3: 使用pandoc（如果安装了）
    try:
        subprocess.run([
            'pandoc', word_path, '-o', pdf_path
        ], check=True, capture_output=True)
        if os.path.exists(pdf_path):
            return pdf_path
    except:
        pass
    
    raise ValueError(
        f"无法自动转换Word文件。请手动将 '{word_path}' 转换为PDF后再试。\n"
        f"或安装 Microsoft Word / LibreOffice 后重试。"
    )


def enhance_existing_pdf(source_path, workbook, qr_mode='single', category_ranges=None):
    """
    在现有PDF/Word上添加封面和二维码，保留原始排版
    
    Args:
        source_path: 原始文件路径（支持PDF/Word）
        workbook: 题册对象
        qr_mode: 二维码模式
            - 'single': 只在封面放一个二维码（整本一个）
            - 'standard': 每页一个二维码（水印模式）
            - 'by_category': 按分类插入二维码页
        category_ranges: 分类模式时的页码范围，如 {'片段阅读': (1, 15), '语句表达': (16, 25), '选词填空': (26, 35)}
    
    Returns:
        生成的PDF文件路径
    """
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    
    # 如果是Word文件，先转换为PDF
    if source_path.lower().endswith(('.doc', '.docx')):
        source_pdf_path = convert_word_to_pdf(source_path)
    else:
        source_pdf_path = source_path
    
    # 获取配置
    institution = Institution.get_instance()
    template = WorkbookTemplate.get_default()
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5005')
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    
    # 读取原始PDF
    reader = PdfReader(source_pdf_path)
    writer = PdfWriter()
    
    total_pages = len(reader.pages)
    
    # 生成二维码
    qr_code = f"WB{workbook.id}"
    qr_url = f"{base_url}/h5/scan/{qr_code}"
    
    # 清除旧页面数据
    WorkbookPage.query.filter_by(workbook_id=workbook.id).delete()
    
    # 创建页面记录
    page = WorkbookPage(
        workbook_id=workbook.id,
        page_num=1,
        start_order=1,
        end_order=workbook.total_questions or 110,
        qr_code=qr_code
    )
    db.session.add(page)
    
    # ========== 生成封面页 ==========
    cover_buffer = BytesIO()
    cover_canvas = canvas.Canvas(cover_buffer, pagesize=A4)
    width, height = A4
    
    # 设置中文字体
    try:
        pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
        font_name = 'PingFang'
    except:
        font_name = 'Helvetica'
    
    # 机构名称
    if institution.name:
        cover_canvas.setFont(font_name, 20)
        cover_canvas.setFillColor(primary_color)
        cover_canvas.drawCentredString(width/2, height - 3*cm, institution.name)
    
    # 标语
    if institution.slogan:
        cover_canvas.setFont(font_name, 11)
        cover_canvas.setFillColor(colors.grey)
        cover_canvas.drawCentredString(width/2, height - 3.8*cm, institution.slogan)
    
    # 分隔线
    cover_canvas.setStrokeColor(primary_color)
    cover_canvas.setLineWidth(1)
    cover_canvas.line(2*cm, height - 4.5*cm, width - 2*cm, height - 4.5*cm)
    
    # 题册标题
    cover_canvas.setFont(font_name, 28)
    cover_canvas.setFillColor(colors.black)
    cover_canvas.drawCentredString(width/2, height - 8*cm, workbook.name)
    
    # 统计信息
    cover_canvas.setFont(font_name, 12)
    cover_canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
    info_text = f"共 {workbook.total_questions or total_pages * 5} 题  |  {total_pages} 页"
    cover_canvas.drawCentredString(width/2, height - 9.5*cm, info_text)
    
    # 二维码
    qr_buffer = generate_qr_image(qr_url, 200)
    from reportlab.lib.utils import ImageReader
    qr_image = ImageReader(qr_buffer)
    qr_size = 5*cm
    cover_canvas.drawImage(qr_image, (width - qr_size)/2, height - 17*cm, qr_size, qr_size)
    
    # 二维码说明
    cover_canvas.setFont(font_name, 11)
    cover_canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
    cover_canvas.drawCentredString(width/2, height - 18*cm, "扫码提交错题 · 查看答案解析")
    
    # 日期
    cover_canvas.setFont(font_name, 10)
    cover_canvas.setFillColor(colors.grey)
    cover_canvas.drawCentredString(width/2, 3*cm, datetime.now().strftime('%Y年%m月'))
    
    # 联系方式
    if institution.phone:
        cover_canvas.drawCentredString(width/2, 2*cm, f"咨询热线：{institution.phone}")
    
    cover_canvas.save()
    
    # 将封面添加到PDF
    cover_buffer.seek(0)
    cover_reader = PdfReader(cover_buffer)
    writer.add_page(cover_reader.pages[0])
    
    # ========== 添加原始PDF的所有页面 ==========
    if qr_mode == 'standard':
        # 标准模式：每页右上角添加小二维码（带页码范围）
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            
            # 为每页生成独立二维码
            page_qr_code = f"WB{workbook.id}P{page_num}"
            page_qr_url = f"{base_url}/h5/scan/{page_qr_code}"
            
            # 保存页面记录
            wp = WorkbookPage(
                workbook_id=workbook.id,
                page_num=page_num,
                start_order=page_num,  # 简化处理，假设每页一个起始
                end_order=page_num,
                qr_code=page_qr_code
            )
            db.session.add(wp)
            
            # 创建水印层
            qr_buffer_small = generate_qr_image(page_qr_url, 80)
            qr_small = ImageReader(qr_buffer_small)
            
            watermark_buffer = BytesIO()
            watermark_canvas = canvas.Canvas(watermark_buffer, pagesize=A4)
            
            # 右上角小二维码
            qr_size = 1.5*cm
            watermark_canvas.drawImage(qr_small, width - qr_size - 0.5*cm, height - qr_size - 0.5*cm, qr_size, qr_size)
            
            # 添加页码文字
            watermark_canvas.setFont(font_name, 7)
            watermark_canvas.setFillColor(colors.grey)
            watermark_canvas.drawString(width - qr_size - 0.3*cm, height - qr_size - 0.8*cm, f"P{page_num}")
            
            watermark_canvas.save()
            watermark_buffer.seek(0)
            
            # 合并水印
            watermark_reader = PdfReader(watermark_buffer)
            page.merge_page(watermark_reader.pages[0])
            writer.add_page(page)
    
    elif qr_mode == 'by_category':
        # 按分类模式：在每个分类开始前插入二维码页
        if not category_ranges:
            # 默认分类（言语理解专项一的分类）
            category_ranges = {
                '片段阅读': (1, 15),
                '语句表达': (16, 25),
                '选词填空': (26, total_pages)
            }
        
        # 创建分类页面记录
        cat_idx = 0
        for cat_name, (start_page, end_page) in category_ranges.items():
            cat_qr_code = f"CAT{workbook.id}_{cat_idx}"
            wp = WorkbookPage(
                workbook_id=workbook.id,
                page_num=cat_idx + 1,
                start_order=start_page,
                end_order=end_page,
                qr_code=cat_qr_code
            )
            db.session.add(wp)
            cat_idx += 1
        
        # 按页码添加内容
        current_cat_idx = 0
        cat_list = list(category_ranges.items())
        
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            
            # 检查是否是新分类的开始
            if current_cat_idx < len(cat_list):
                cat_name, (start_page, end_page) = cat_list[current_cat_idx]
                if page_num == start_page:
                    # 插入分类标题页
                    cat_qr_code = f"CAT{workbook.id}_{current_cat_idx}"
                    cat_qr_url = f"{base_url}/h5/scan/{cat_qr_code}"
                    
                    cat_buffer = BytesIO()
                    cat_canvas = canvas.Canvas(cat_buffer, pagesize=A4)
                    
                    # 分类标题
                    cat_canvas.setFont(font_name, 24)
                    cat_canvas.setFillColor(primary_color)
                    cat_canvas.drawCentredString(width/2, height - 8*cm, f"【 {cat_name} 】")
                    
                    # 页码范围
                    cat_canvas.setFont(font_name, 12)
                    cat_canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
                    cat_canvas.drawCentredString(width/2, height - 9.5*cm, 
                        f"第 {start_page} - {end_page} 页  |  第 {current_cat_idx + 1}/{len(cat_list)} 板块")
                    
                    # 二维码
                    qr_buffer = generate_qr_image(cat_qr_url, 150)
                    qr_img = ImageReader(qr_buffer)
                    qr_size = 4*cm
                    cat_canvas.drawImage(qr_img, (width - qr_size)/2, height - 15*cm, qr_size, qr_size)
                    
                    cat_canvas.setFont(font_name, 11)
                    cat_canvas.drawCentredString(width/2, height - 16*cm, "扫码提交本板块错题")
                    
                    cat_canvas.save()
                    cat_buffer.seek(0)
                    
                    cat_reader = PdfReader(cat_buffer)
                    writer.add_page(cat_reader.pages[0])
                    
                    current_cat_idx += 1
            
            # 添加原始页面
            writer.add_page(page)
    
    else:
        # single模式：直接添加原始页面（封面已有二维码）
        for page in reader.pages:
            writer.add_page(page)
    
    # 保存输出文件
    output_dir = current_app.config.get('OUTPUT_FOLDER', 'data/output')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{workbook.name}_{workbook.id}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'wb') as f:
        writer.write(f)
    
    # 更新题册信息
    workbook.pdf_path = filepath
    workbook.total_pages = total_pages + 1  # 加上封面
    
    db.session.commit()
    
    return filepath
