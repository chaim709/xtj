# -*- coding: utf-8 -*-
"""数据批量导入工具"""
import os
from datetime import datetime
from io import BytesIO

from app import db
from app.models import Student, Submission, Mistake, Question, Workbook, WorkbookItem, StudentStats


def import_student_records_from_excel(file_path_or_buffer):
    """
    从Excel导入学员做题记录
    
    Excel格式：
    | 学员姓名 | 手机号 | 题册名称 | 板块 | 做题数 | 错题数 | 日期 |
    
    返回：导入结果统计
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("请先安装pandas: pip install pandas openpyxl")
    
    # 读取Excel
    df = pd.read_excel(file_path_or_buffer)
    
    # 标准化列名
    column_mapping = {
        '学员姓名': 'name',
        '姓名': 'name',
        '手机号': 'phone',
        '电话': 'phone',
        '题册名称': 'workbook_name',
        '题册': 'workbook_name',
        '板块': 'subcategory',
        '分类': 'subcategory',
        '做题数': 'total_attempted',
        '做了多少题': 'total_attempted',
        '错题数': 'mistake_count',
        '错了多少题': 'mistake_count',
        '日期': 'date',
        '提交日期': 'date',
        '正确率': 'accuracy_rate'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 验证必需列
    required_cols = ['name', 'total_attempted', 'mistake_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必需列: {missing_cols}")
    
    results = {
        'total_rows': len(df),
        'success': 0,
        'failed': 0,
        'new_students': 0,
        'errors': []
    }
    
    for idx, row in df.iterrows():
        try:
            # 获取或创建学员
            name = str(row['name']).strip()
            phone = str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else ''
            
            if not name:
                results['errors'].append(f"第{idx+2}行: 姓名不能为空")
                results['failed'] += 1
                continue
            
            # 查找学员
            if phone:
                student = Student.query.filter_by(phone=phone).first()
            else:
                student = Student.query.filter_by(name=name).first()
            
            if not student:
                # 创建新学员
                student = Student(name=name, phone=phone or f"auto_{datetime.now().timestamp()}")
                db.session.add(student)
                db.session.flush()
                results['new_students'] += 1
            
            # 获取题册（可选）
            workbook_id = None
            if 'workbook_name' in row and pd.notna(row['workbook_name']):
                workbook = Workbook.query.filter(
                    Workbook.name.contains(str(row['workbook_name']))
                ).first()
                if workbook:
                    workbook_id = workbook.id
            
            # 获取数据
            total_attempted = int(row['total_attempted']) if pd.notna(row['total_attempted']) else 0
            mistake_count = int(row['mistake_count']) if pd.notna(row['mistake_count']) else 0
            subcategory = str(row.get('subcategory', '')).strip() if pd.notna(row.get('subcategory')) else None
            
            # 计算正确率
            if 'accuracy_rate' in row and pd.notna(row['accuracy_rate']):
                accuracy_rate = float(row['accuracy_rate'])
                if accuracy_rate > 1:  # 如果是百分比形式
                    accuracy_rate = accuracy_rate
                else:
                    accuracy_rate = accuracy_rate * 100
            else:
                accuracy_rate = round((total_attempted - mistake_count) / total_attempted * 100, 1) if total_attempted > 0 else 0
            
            correct_count = total_attempted - mistake_count
            
            # 获取日期
            if 'date' in row and pd.notna(row['date']):
                if isinstance(row['date'], str):
                    try:
                        created_at = datetime.strptime(row['date'], '%Y-%m-%d')
                    except:
                        created_at = datetime.now()
                else:
                    created_at = pd.to_datetime(row['date']).to_pydatetime()
            else:
                created_at = datetime.now()
            
            # 创建提交记录
            submission = Submission(
                student_id=student.id,
                workbook_id=workbook_id,
                total_attempted=total_attempted,
                correct_count=correct_count,
                mistake_count=mistake_count,
                accuracy_rate=accuracy_rate,
                subcategory=subcategory,
                created_at=created_at
            )
            db.session.add(submission)
            
            # 更新学员统计
            update_student_stats_from_import(student.id, submission, subcategory)
            
            results['success'] += 1
            
        except Exception as e:
            results['errors'].append(f"第{idx+2}行: {str(e)}")
            results['failed'] += 1
    
    db.session.commit()
    return results


def update_student_stats_from_import(student_id, submission, subcategory=None):
    """更新学员统计数据"""
    # 更新总体统计
    total_stat = StudentStats.get_or_create(student_id, 'total', None, 'all')
    total_stat.total_attempted += submission.total_attempted
    total_stat.total_correct += submission.correct_count
    total_stat.total_mistakes += submission.mistake_count
    total_stat.submission_count += 1
    total_stat.calculate_accuracy()
    
    # 更新板块统计
    if subcategory:
        subcat_stat = StudentStats.get_or_create(student_id, 'subcategory', subcategory, 'all')
        subcat_stat.total_attempted += submission.total_attempted
        subcat_stat.total_correct += submission.correct_count
        subcat_stat.total_mistakes += submission.mistake_count
        subcat_stat.submission_count += 1
        subcat_stat.calculate_accuracy()


def generate_import_template():
    """生成导入模板Excel"""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("请先安装pandas: pip install pandas openpyxl")
    
    # 示例数据
    data = {
        '学员姓名': ['张三', '李四', '王五'],
        '手机号': ['13800138001', '13800138002', '13800138003'],
        '题册名称': ['言语理解专项一', '言语理解专项一', '图形推理700题'],
        '板块': ['片段阅读', '语句表达', '图形推理'],
        '做题数': [40, 35, 50],
        '错题数': [5, 8, 12],
        '日期': ['2026-01-15', '2026-01-20', '2026-01-25']
    }
    
    df = pd.DataFrame(data)
    
    # 保存到BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='学员做题记录')
        
        # 添加说明sheet
        instructions = pd.DataFrame({
            '字段说明': [
                '学员姓名 - 必填，学员姓名',
                '手机号 - 选填，用于识别学员',
                '题册名称 - 选填，关联的题册',
                '板块 - 选填，如：片段阅读、语句表达',
                '做题数 - 必填，本次做了多少题',
                '错题数 - 必填，本次错了多少题',
                '日期 - 选填，格式：YYYY-MM-DD'
            ]
        })
        instructions.to_excel(writer, index=False, sheet_name='填写说明')
    
    output.seek(0)
    return output


def import_mistakes_from_excel(file_path_or_buffer, student_id, workbook_id):
    """
    从Excel导入错题（题号列表）
    
    Excel格式：
    | 错题题号 |
    | 3 |
    | 7 |
    | 15 |
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("请先安装pandas")
    
    df = pd.read_excel(file_path_or_buffer)
    
    # 获取题号列
    if '错题题号' in df.columns:
        orders = df['错题题号'].dropna().astype(int).tolist()
    elif '题号' in df.columns:
        orders = df['题号'].dropna().astype(int).tolist()
    else:
        # 假设第一列是题号
        orders = df.iloc[:, 0].dropna().astype(int).tolist()
    
    results = {'success': 0, 'failed': 0}
    
    for order in orders:
        item = WorkbookItem.query.filter_by(
            workbook_id=workbook_id,
            order=int(order)
        ).first()
        
        if item:
            # 检查是否已存在
            existing = Mistake.query.filter_by(
                student_id=student_id,
                question_id=item.question_id,
                workbook_id=workbook_id
            ).first()
            
            if not existing:
                mistake = Mistake(
                    student_id=student_id,
                    question_id=item.question_id,
                    workbook_id=workbook_id,
                    question_order=order
                )
                db.session.add(mistake)
                results['success'] += 1
            else:
                results['failed'] += 1
        else:
            results['failed'] += 1
    
    db.session.commit()
    return results
