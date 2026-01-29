"""
第二阶段数据库初始化脚本

执行此脚本将：
1. 创建第二阶段新增的数据表
2. 添加预设科目数据
3. 不影响现有数据

使用方法：
    python init_phase2_db.py
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Subject, Project, Package, ClassType, ClassBatch,
    Schedule, ScheduleChangeLog, Teacher, StudentBatch, Attendance
)


def init_database():
    """初始化数据库"""
    app = create_app('development')
    
    with app.app_context():
        print("=" * 50)
        print("第二阶段数据库初始化")
        print("=" * 50)
        
        # 创建所有表
        print("\n1. 创建数据表...")
        db.create_all()
        print("   ✅ 数据表创建完成")
        
        # 检查是否需要添加预设科目
        existing_subjects = Subject.query.filter_by(is_preset=True).count()
        if existing_subjects == 0:
            print("\n2. 添加预设科目...")
            add_preset_subjects()
            print("   ✅ 预设科目添加完成")
        else:
            print(f"\n2. 预设科目已存在 ({existing_subjects}个)，跳过")
        
        print("\n" + "=" * 50)
        print("初始化完成！")
        print("=" * 50)
        
        # 显示表状态
        print("\n数据表状态:")
        print(f"  - subjects: {Subject.query.count()} 条")
        print(f"  - projects: {Project.query.count()} 条")
        print(f"  - packages: {Package.query.count()} 条")
        print(f"  - class_types: {ClassType.query.count()} 条")
        print(f"  - class_batches: {ClassBatch.query.count()} 条")
        print(f"  - schedules: {Schedule.query.count()} 条")
        print(f"  - teachers: {Teacher.query.count()} 条")
        print(f"  - student_batches: {StudentBatch.query.count()} 条")
        print(f"  - attendances: {Attendance.query.count()} 条")


def add_preset_subjects():
    """添加预设科目"""
    # 国省考科目
    civil_subjects = [
        {'name': '言语理解与表达', 'short_name': '言语', 'exam_type': 'civil', 'sort_order': 1},
        {'name': '判断推理', 'short_name': '判断', 'exam_type': 'civil', 'sort_order': 2},
        {'name': '数量关系与资料分析', 'short_name': '数资', 'exam_type': 'civil', 'sort_order': 3},
        {'name': '常识判断', 'short_name': '常识', 'exam_type': 'civil', 'sort_order': 4},
        {'name': '申论', 'short_name': '申论', 'exam_type': 'civil', 'sort_order': 5},
    ]
    
    # 事业编科目
    career_subjects = [
        {'name': '公共基础知识', 'short_name': '公基', 'exam_type': 'career', 'sort_order': 10},
        {'name': '职业能力测验', 'short_name': '职测', 'exam_type': 'career', 'sort_order': 11},
        {'name': '综合应用能力', 'short_name': '综应', 'exam_type': 'career', 'sort_order': 12},
    ]
    
    all_subjects = civil_subjects + career_subjects
    
    for data in all_subjects:
        subject = Subject(
            name=data['name'],
            short_name=data['short_name'],
            exam_type=data['exam_type'],
            is_preset=True,
            sort_order=data['sort_order'],
            status='active'
        )
        db.session.add(subject)
        print(f"      添加科目: {data['name']} ({data['short_name']})")
    
    db.session.commit()


def check_tables():
    """检查表是否存在"""
    app = create_app('development')
    
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'subjects', 'projects', 'packages', 'class_types', 'class_batches',
            'schedules', 'schedule_change_logs', 'teachers', 'student_batches', 'attendances'
        ]
        
        print("\n表检查结果:")
        for table in required_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (不存在)")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_tables()
    else:
        init_database()
