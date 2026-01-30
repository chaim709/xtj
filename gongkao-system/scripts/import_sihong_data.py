#!/usr/bin/env python3
"""
泗洪2026事业单位数据导入脚本

导入内容：
1. 学员名单
2. 课表（含项目、班型、班次）
3. 录播课链接

使用方法：
    cd gongkao-system
    python scripts/import_sihong_data.py
"""
import os
import sys
import re
import glob
from datetime import datetime, date

import pandas as pd

# 将项目根目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.student import Student
from app.models.course import (
    Project, Package, ClassType, ClassBatch, Schedule, 
    CourseRecording, Subject, StudentBatch
)
from app.models.teacher import Teacher


# 数据文件路径
DATA_PATH = glob.glob("/Users/chaim/CodeBuddy/公考项目/公考培训机构管理系统/职位表和进面分数线/学员*")[0]


def clean_phone(phone):
    """清理电话号码"""
    if pd.isna(phone):
        return None
    # 处理科学计数法
    if isinstance(phone, float):
        phone = str(int(phone))
    else:
        phone = str(phone).strip()
    # 只保留数字
    phone = re.sub(r'[^\d]', '', phone)
    return phone if len(phone) >= 10 else None


def clean_id_number(id_num):
    """清理身份证号"""
    if pd.isna(id_num):
        return None
    # 处理科学计数法
    if isinstance(id_num, float):
        id_num = f"{int(id_num)}"
    return str(id_num).strip()


def import_students():
    """导入学员数据"""
    print("\n=== 导入学员数据 ===")
    
    file_path = os.path.join(DATA_PATH, '学员名单.xlsx')
    df = pd.read_excel(file_path)
    
    imported = 0
    updated = 0
    skipped = 0
    
    for _, row in df.iterrows():
        name = str(row.get('姓名', '')).strip()
        if not name or pd.isna(row.get('姓名')):
            skipped += 1
            continue
        
        phone = clean_phone(row.get('联系电话'))
        
        # 检查是否已存在（按姓名+电话匹配）
        existing = None
        if phone:
            existing = Student.query.filter_by(name=name, phone=phone).first()
        else:
            existing = Student.query.filter_by(name=name).first()
        
        if existing:
            # 更新现有学员
            if pd.notna(row.get('家长联系电话')):
                existing.parent_phone = clean_phone(row.get('家长联系电话'))
            if pd.notna(row.get('身份证号')):
                existing.id_number = clean_id_number(row.get('身份证号'))
            if pd.notna(row.get('学历')):
                existing.education = str(row.get('学历')).strip()
            if pd.notna(row.get('家庭住址')):
                existing.address = str(row.get('家庭住址')).strip()
            if pd.notna(row.get('课程报名')):
                existing.class_name = str(row.get('课程报名')).strip()
            updated += 1
            print(f"  更新: {name}")
        else:
            # 创建新学员
            student = Student(
                name=name,
                phone=phone,
                parent_phone=clean_phone(row.get('家长联系电话')),
                id_number=clean_id_number(row.get('身份证号')),
                education=str(row.get('学历')).strip() if pd.notna(row.get('学历')) else None,
                address=str(row.get('家庭住址')).strip() if pd.notna(row.get('家庭住址')) else None,
                class_name=str(row.get('课程报名')).strip() if pd.notna(row.get('课程报名')) else None,
                exam_type='2026年江苏事业编',
                enrollment_date=date.today(),
                status='active'
            )
            db.session.add(student)
            imported += 1
            print(f"  新增: {name}")
    
    db.session.commit()
    print(f"\n学员导入完成: 新增 {imported}, 更新 {updated}, 跳过 {skipped}")
    return imported, updated


def create_project_and_classes():
    """创建项目、班型、班次"""
    print("\n=== 创建项目和班次 ===")
    
    # 1. 创建或获取项目
    project = Project.query.filter_by(
        name='泗洪2026事业单位',
        year=2026
    ).first()
    
    if not project:
        project = Project(
            name='泗洪2026事业单位',
            exam_type='career',  # 事业编
            year=2026,
            start_date=date(2026, 1, 19),
            end_date=date(2026, 4, 30),
            description='泗洪2026年事业单位考试培训项目',
            status='recruiting'
        )
        db.session.add(project)
        db.session.flush()
        print(f"  创建项目: {project.name}")
    else:
        print(f"  项目已存在: {project.name}")
    
    # 2. 创建班型
    class_types = [
        {'name': '基础夯实课', 'planned_days': 18, 'sort_order': 1},
        {'name': '系统刷题提升', 'planned_days': 12, 'sort_order': 2},
    ]
    
    type_map = {}
    for ct_data in class_types:
        ct = ClassType.query.filter_by(
            project_id=project.id,
            name=ct_data['name']
        ).first()
        
        if not ct:
            ct = ClassType(
                project_id=project.id,
                name=ct_data['name'],
                planned_days=ct_data['planned_days'],
                sort_order=ct_data['sort_order'],
                status='active'
            )
            db.session.add(ct)
            db.session.flush()
            print(f"  创建班型: {ct.name}")
        else:
            print(f"  班型已存在: {ct.name}")
        type_map[ct.name] = ct
    
    # 3. 创建班次
    batches_data = [
        {
            'class_type': '基础夯实课',
            'name': '寒假二期班--泗洪',
            'batch_number': 2,
            'start_date': date(2026, 1, 19),
            'end_date': date(2026, 2, 9),
            'actual_days': 22
        },
        {
            'class_type': '系统刷题提升',
            'name': '刷题一期班--泗洪',
            'batch_number': 1,
            'start_date': date(2026, 2, 17),
            'end_date': date(2026, 3, 15),
            'actual_days': 27
        },
        {
            'class_type': '系统刷题提升',
            'name': '刷题二期班--泗洪',
            'batch_number': 2,
            'start_date': date(2026, 3, 6),
            'end_date': date(2026, 3, 24),
            'actual_days': 19
        }
    ]
    
    batch_map = {}
    for batch_data in batches_data:
        ct = type_map.get(batch_data['class_type'])
        if not ct:
            continue
        
        batch = ClassBatch.query.filter_by(
            class_type_id=ct.id,
            name=batch_data['name']
        ).first()
        
        if not batch:
            batch = ClassBatch(
                class_type_id=ct.id,
                name=batch_data['name'],
                batch_number=batch_data['batch_number'],
                start_date=batch_data['start_date'],
                end_date=batch_data['end_date'],
                actual_days=batch_data['actual_days'],
                status='recruiting'
            )
            db.session.add(batch)
            db.session.flush()
            print(f"  创建班次: {batch.name}")
        else:
            print(f"  班次已存在: {batch.name}")
        batch_map[batch.name] = batch
    
    db.session.commit()
    return project, type_map, batch_map


def ensure_subjects():
    """确保科目存在"""
    print("\n=== 确保科目存在 ===")
    
    subjects_data = [
        {'name': '言语理解', 'short_name': '言语', 'exam_type': 'common'},
        {'name': '数量关系', 'short_name': '数资', 'exam_type': 'common'},
        {'name': '资料分析', 'short_name': '数资', 'exam_type': 'common'},
        {'name': '判断推理', 'short_name': '判断', 'exam_type': 'common'},
        {'name': '常识判断', 'short_name': '常识', 'exam_type': 'common'},
        {'name': '申论', 'short_name': '申论', 'exam_type': 'common'},
        {'name': '时政', 'short_name': '时政', 'exam_type': 'common'},
        {'name': '材料处理', 'short_name': '材料', 'exam_type': 'career'},
    ]
    
    subject_map = {}
    for subj_data in subjects_data:
        subj = Subject.query.filter_by(name=subj_data['name']).first()
        if not subj:
            subj = Subject(
                name=subj_data['name'],
                short_name=subj_data['short_name'],
                exam_type=subj_data['exam_type'],
                is_preset=True,
                status='active'
            )
            db.session.add(subj)
            db.session.flush()
            print(f"  创建科目: {subj.name}")
        subject_map[subj.name] = subj
        subject_map[subj.short_name] = subj  # 也用简称映射
    
    db.session.commit()
    return subject_map


def excel_date_to_python(excel_date):
    """将Excel日期序号转换为Python日期"""
    if pd.isna(excel_date):
        return None
    if isinstance(excel_date, (datetime, date)):
        return excel_date.date() if isinstance(excel_date, datetime) else excel_date
    if isinstance(excel_date, (int, float)):
        # Excel日期序号（从1900-01-01开始）
        from datetime import timedelta
        base_date = date(1899, 12, 30)  # Excel基准日期
        return base_date + timedelta(days=int(excel_date))
    return None


def import_schedule(batch_map, subject_map):
    """导入课表"""
    print("\n=== 导入课表 ===")
    
    file_path = os.path.join(DATA_PATH, '泗洪2026事业单位课表.xlsx')
    df = pd.read_excel(file_path)
    
    # 解析课表数据
    current_batch = None
    batch_mapping = {
        '基础夯实课(18天）---寒假二期班--泗洪': '寒假二期班--泗洪',
        '系统刷题提升(12天）---泗洪--一期班': '刷题一期班--泗洪',
        '系统刷题提升(12天）---泗洪--二期班': '刷题二期班--泗洪',
    }
    
    # 科目名称映射
    subject_mapping = {
        '言语理解': '言语理解',
        '言语巩固练习': '言语理解',
        '数资': '数量关系',
        '数资巩固练习': '数量关系',
        '判断推理': '判断推理',
        '判断巩固练习': '判断推理',
        '常识': '常识判断',
        '时政': '时政',
        '申论素材': '申论',
        '材料处理': '材料处理',
    }
    
    imported = 0
    
    for _, row in df.iterrows():
        first_col = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
        
        # 检查是否是班次标题行
        for pattern, batch_name in batch_mapping.items():
            if pattern in first_col:
                current_batch = batch_map.get(batch_name)
                if current_batch:
                    print(f"\n  处理班次: {batch_name}")
                break
        
        if not current_batch:
            continue
        
        # 检查是否是有效的课表行
        day_str = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
        if not day_str.startswith('第') or '天' not in day_str:
            continue
        
        # 提取天数
        day_match = re.search(r'第(\d+)天', day_str)
        if not day_match:
            continue
        day_number = int(day_match.group(1))
        
        # 提取日期
        schedule_date = excel_date_to_python(row.iloc[1])
        if not schedule_date:
            continue
        
        # 提取科目（上午列，索引3）
        morning_subject = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None
        
        # 休息日跳过
        if morning_subject in ['休', '过年放假', None] or pd.isna(row.iloc[3]):
            continue
        
        # 查找科目
        subject_name = subject_mapping.get(morning_subject, morning_subject)
        subject = subject_map.get(subject_name)
        
        if not subject:
            print(f"    警告: 未找到科目 '{morning_subject}'")
            continue
        
        # 检查是否已存在
        existing = Schedule.query.filter_by(
            batch_id=current_batch.id,
            schedule_date=schedule_date,
            day_number=day_number
        ).first()
        
        if existing:
            continue
        
        # 创建课表记录
        schedule = Schedule(
            batch_id=current_batch.id,
            schedule_date=schedule_date,
            day_number=day_number,
            subject_id=subject.id,
            evening_type='exercise',  # 晚间为练习
            remark=''
        )
        db.session.add(schedule)
        imported += 1
    
    db.session.commit()
    print(f"\n课表导入完成: 新增 {imported} 条")
    return imported


def import_recordings(batch_map, subject_map):
    """导入录播课链接"""
    print("\n=== 导入录播课链接 ===")
    
    file_path = os.path.join(DATA_PATH, '录播课链接.xlsx')
    df = pd.read_excel(file_path)
    
    # 使用基础夯实课班次作为默认班次
    default_batch = batch_map.get('寒假二期班--泗洪')
    if not default_batch:
        print("  错误: 未找到默认班次")
        return 0
    
    # 科目映射
    subject_mapping = {
        '言语基础': '言语理解',
        '数资基础': '数量关系',
        '判断基础': '判断推理',
    }
    
    imported = 0
    
    for _, row in df.iterrows():
        date_str = str(row.get('日期', '')).strip()
        course_name = str(row.get('课程', '')).strip()
        content = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
        
        if not content or not date_str:
            continue
        
        # 解析内容
        # 格式: 录制: xxx<br/>日期: 2026-01-19 08:59:06<br/>录制文件：https://xxx
        
        # 提取标题
        title_match = re.search(r'录制:\s*(.+?)<br/>', content)
        title = title_match.group(1).strip() if title_match else course_name
        
        # 提取日期时间
        datetime_match = re.search(r'日期:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2})', content)
        if not datetime_match:
            continue
        
        recording_date = datetime.strptime(datetime_match.group(1), '%Y-%m-%d').date()
        hour = int(datetime_match.group(2))
        
        # 根据时间判断时段
        if hour < 12:
            period = 'morning'
        elif hour < 18:
            period = 'afternoon'
        else:
            period = 'evening'
        
        # 提取链接
        url_match = re.search(r'https://[^\s<]+', content)
        if not url_match:
            continue
        recording_url = url_match.group(0)
        
        # 查找科目
        subject_name = subject_mapping.get(course_name, course_name)
        subject = subject_map.get(subject_name)
        
        # 检查是否已存在
        existing = CourseRecording.query.filter_by(
            batch_id=default_batch.id,
            recording_date=recording_date,
            recording_url=recording_url
        ).first()
        
        if existing:
            continue
        
        # 创建录播记录
        recording = CourseRecording(
            batch_id=default_batch.id,
            recording_date=recording_date,
            period=period,
            title=title,
            recording_url=recording_url,
            subject_id=subject.id if subject else None,
            remark=f'{course_name} - {date_str}'
        )
        db.session.add(recording)
        imported += 1
        print(f"  导入: {recording_date} - {title}")
    
    db.session.commit()
    print(f"\n录播课导入完成: 新增 {imported} 条")
    return imported


def main():
    """主函数"""
    print("=" * 60)
    print("泗洪2026事业单位数据导入")
    print("=" * 60)
    print(f"数据目录: {DATA_PATH}")
    
    # 创建应用上下文
    app = create_app('development')
    
    with app.app_context():
        try:
            # 1. 导入学员
            students_imported, students_updated = import_students()
            
            # 2. 创建项目和班次
            project, type_map, batch_map = create_project_and_classes()
            
            # 3. 确保科目存在
            subject_map = ensure_subjects()
            
            # 4. 导入课表
            schedules_imported = import_schedule(batch_map, subject_map)
            
            # 5. 导入录播课
            recordings_imported = import_recordings(batch_map, subject_map)
            
            # 汇总
            print("\n" + "=" * 60)
            print("导入完成汇总:")
            print("=" * 60)
            print(f"学员: 新增 {students_imported}, 更新 {students_updated}")
            print(f"课表: 新增 {schedules_imported}")
            print(f"录播: 新增 {recordings_imported}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n错误: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
