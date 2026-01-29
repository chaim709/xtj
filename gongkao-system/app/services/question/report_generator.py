# -*- coding: utf-8 -*-
"""学员学习分析报告生成器"""
import os
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, 
    Spacer, Image, PageBreak, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from flask import current_app
from app.models import Institution
from app.services.question.stats import StudentStatsService

# 注册中文字体
font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fonts', 'SourceHanSansSC-Regular.otf')
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('SourceHanSans', font_path))
    font_name = 'SourceHanSans'
else:
    font_name = 'Helvetica'


def hex_to_color(hex_str):
    """十六进制颜色转换"""
    hex_str = hex_str.lstrip('#')
    return colors.Color(
        int(hex_str[0:2], 16) / 255,
        int(hex_str[2:4], 16) / 255,
        int(hex_str[4:6], 16) / 255
    )


class HorizontalLine(Flowable):
    """水平线"""
    def __init__(self, width, color=colors.grey, thickness=0.5):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
    
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


def generate_radar_chart(data, labels, title="板块正确率"):
    """生成雷达图"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 数据准备
        N = len(labels)
        if N < 3:
            return None
        
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        data = data + [data[0]]  # 闭合
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        
        # 绘制雷达图
        ax.fill(angles, data, alpha=0.25, color='#667eea')
        ax.plot(angles, data, 'o-', linewidth=2, color='#667eea')
        
        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=10)
        
        # 设置刻度
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8)
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # 保存到BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        buf.seek(0)
        return buf
        
    except Exception as e:
        print(f"生成雷达图失败: {e}")
        return None


def generate_trend_chart(data, title="正确率趋势"):
    """生成趋势折线图"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
        plt.rcParams['axes.unicode_minus'] = False
        
        if not data:
            return None
        
        dates = [d['date'] for d in data]
        rates = [d['accuracy_rate'] for d in data]
        
        fig, ax = plt.subplots(figsize=(8, 3))
        
        ax.plot(dates, rates, 'o-', linewidth=2, color='#667eea', markersize=6)
        ax.fill_between(dates, rates, alpha=0.2, color='#667eea')
        
        ax.set_ylim(0, 100)
        ax.set_ylabel('正确率 (%)', fontsize=10)
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        # 旋转x轴标签
        plt.xticks(rotation=45, ha='right', fontsize=8)
        
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        buf.seek(0)
        return buf
        
    except Exception as e:
        print(f"生成趋势图失败: {e}")
        return None


def generate_student_report(student_id, period='all'):
    """生成学员学习分析报告PDF"""
    
    # 获取统计数据
    stats_service = StudentStatsService(student_id)
    report_data = stats_service.get_full_report_data(period)
    
    # 获取机构信息
    institution = Institution.get_instance()
    primary_color = hex_to_color(institution.primary_color or '#1a73e8')
    
    # 创建PDF
    output_dir = os.path.join(current_app.root_path, '..', 'data', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"学习报告_{report_data['student']['name']}_{datetime.now().strftime('%Y%m%d')}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    # 样式定义
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=24,
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=16
    )
    
    center_style = ParagraphStyle(
        'Center',
        parent=normal_style,
        alignment=TA_CENTER
    )
    
    # 构建内容
    elements = []
    width = A4[0] - 3*cm
    
    # ========== 第1页：封面+总览 ==========
    elements.append(Spacer(1, 2*cm))
    
    # Logo
    if institution.logo_path and os.path.exists(institution.logo_path):
        logo = Image(institution.logo_path, width=3*cm, height=3*cm)
        elements.append(logo)
        elements.append(Spacer(1, 0.5*cm))
    
    # 标题
    elements.append(Paragraph(f"学习分析报告", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # 机构名称
    elements.append(Paragraph(institution.name or '培训机构', center_style))
    elements.append(Spacer(1, 1*cm))
    
    # 学员信息
    info_data = [
        ['学员姓名', report_data['student']['name']],
        ['统计周期', get_period_label(period)],
        ['生成时间', report_data['generated_at']]
    ]
    info_table = Table(info_data, colWidths=[4*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 1.5*cm))
    
    # 总览卡片
    overview = report_data['overview']
    
    card_data = [
        [
            create_stat_card('总刷题数', str(overview['total_attempted']), '题'),
            create_stat_card('正确率', f"{overview['accuracy_rate']}%", ''),
            create_stat_card('学习天数', str(overview['study_days']), '天'),
            create_stat_card('错题数', str(overview['unique_mistakes']), '题')
        ]
    ]
    
    card_table = Table(card_data, colWidths=[width/4]*4)
    card_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (0, 0), 1, primary_color),
        ('BOX', (1, 0), (1, 0), 1, primary_color),
        ('BOX', (2, 0), (2, 0), 1, primary_color),
        ('BOX', (3, 0), (3, 0), 1, primary_color),
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.96, 0.97, 1)),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(card_table)
    
    elements.append(PageBreak())
    
    # ========== 第2页：板块分析 ==========
    elements.append(Paragraph("📊 板块分析", heading_style))
    elements.append(HorizontalLine(width, primary_color, 1))
    elements.append(Spacer(1, 0.5*cm))
    
    subcategory_stats = report_data['subcategory_stats']
    
    # 生成雷达图
    if len(subcategory_stats) >= 3:
        labels = [s['dimension_value'] for s in subcategory_stats[:8]]  # 最多8个
        data = [s['accuracy_rate'] for s in subcategory_stats[:8]]
        
        radar_buf = generate_radar_chart(data, labels, "板块正确率雷达图")
        if radar_buf:
            radar_img = Image(radar_buf, width=10*cm, height=10*cm)
            elements.append(radar_img)
            elements.append(Spacer(1, 0.5*cm))
    
    # 板块明细表
    elements.append(Paragraph("板块明细", normal_style))
    elements.append(Spacer(1, 0.3*cm))
    
    table_data = [['板块', '做题数', '正确数', '错题数', '正确率', '状态']]
    for stat in subcategory_stats:
        rate = stat['accuracy_rate']
        status = '🟢 优秀' if rate >= 85 else ('🟡 良好' if rate >= 70 else '🔴 需加强')
        table_data.append([
            stat['dimension_value'],
            str(stat['total_attempted']),
            str(stat['total_correct']),
            str(stat['total_mistakes']),
            f"{rate}%",
            status
        ])
    
    detail_table = Table(table_data, colWidths=[width*0.25, width*0.12, width*0.12, width*0.12, width*0.15, width*0.24])
    detail_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)])
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 弱项分析
    weakness = report_data['weakness_analysis']
    if weakness:
        elements.append(Paragraph("⚠️ 弱项提示", heading_style))
        for w in weakness[:3]:
            level_color = colors.red if w['level'] == 'danger' else colors.orange
            elements.append(Paragraph(
                f"• <font color='#{level_color.hexval()[2:]}'>{w['name']}</font> 正确率 {w['accuracy_rate']}%，建议加强练习",
                normal_style
            ))
    
    elements.append(PageBreak())
    
    # ========== 第3页：知识点热力图 ==========
    elements.append(Paragraph("🎯 知识点分析", heading_style))
    elements.append(HorizontalLine(width, primary_color, 1))
    elements.append(Spacer(1, 0.5*cm))
    
    kp_stats = report_data['knowledge_point_stats']
    if kp_stats:
        kp_table_data = [['知识点', '所属板块', '错题数', '状态']]
        for kp in kp_stats[:15]:  # 最多15个
            count = kp['mistake_count']
            status = '🔴 重点' if count >= 5 else ('🟡 关注' if count >= 3 else '🟢 正常')
            kp_table_data.append([
                kp['knowledge_point'],
                kp['subcategory'] or '-',
                str(count),
                status
            ])
        
        kp_table = Table(kp_table_data, colWidths=[width*0.35, width*0.25, width*0.15, width*0.25])
        kp_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(kp_table)
    else:
        elements.append(Paragraph("暂无知识点统计数据", center_style))
    
    elements.append(PageBreak())
    
    # ========== 第4页：趋势+高频错题 ==========
    elements.append(Paragraph("📈 学习趋势", heading_style))
    elements.append(HorizontalLine(width, primary_color, 1))
    elements.append(Spacer(1, 0.5*cm))
    
    # 趋势图
    trend_data = report_data['trend_data']
    if trend_data:
        trend_buf = generate_trend_chart(trend_data, "近30天正确率趋势")
        if trend_buf:
            trend_img = Image(trend_buf, width=16*cm, height=6*cm)
            elements.append(trend_img)
    else:
        elements.append(Paragraph("暂无趋势数据", center_style))
    
    elements.append(Spacer(1, 1*cm))
    
    # 高频错题
    elements.append(Paragraph("🔥 高频错题 TOP10", heading_style))
    elements.append(HorizontalLine(width, primary_color, 1))
    elements.append(Spacer(1, 0.3*cm))
    
    frequent = report_data['frequent_mistakes']
    if frequent:
        for i, q in enumerate(frequent, 1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {q['stem']}",
                normal_style
            ))
            elements.append(Paragraph(
                f"<font color='grey'>错{q['count']}次 | {q['subcategory'] or q['category'] or '未分类'} | 答案: {q['answer']}</font>",
                ParagraphStyle('Small', parent=normal_style, fontSize=9, textColor=colors.grey)
            ))
            elements.append(Spacer(1, 0.3*cm))
    else:
        elements.append(Paragraph("暂无错题记录", center_style))
    
    # 生成PDF
    doc.build(elements)
    
    return output_path


def create_stat_card(title, value, unit):
    """创建统计卡片内容"""
    return Paragraph(
        f"<font size='10' color='grey'>{title}</font><br/>"
        f"<font size='24'><b>{value}</b></font>"
        f"<font size='10'>{unit}</font>",
        ParagraphStyle('Card', fontName=font_name, alignment=TA_CENTER, leading=28)
    )


def get_period_label(period):
    """获取时间范围标签"""
    labels = {
        '7d': '最近7天',
        '30d': '最近30天',
        '90d': '最近90天',
        'all': '全部'
    }
    return labels.get(period, '全部')
