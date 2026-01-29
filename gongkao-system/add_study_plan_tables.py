#!/usr/bin/env python
"""
数据库迁移脚本 - 添加学习计划相关表

运行方式:
1. 激活虚拟环境: source venv/bin/activate
2. 运行脚本: python add_study_plan_tables.py
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.study_plan import StudyPlan, PlanGoal, PlanTask, PlanProgress

def add_tables():
    """添加学习计划相关表"""
    app = create_app()
    
    with app.app_context():
        # 检查表是否已存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        tables_to_create = ['study_plans', 'plan_goals', 'plan_tasks', 'plan_progress']
        tables_needed = [t for t in tables_to_create if t not in existing_tables]
        
        if not tables_needed:
            print("所有学习计划相关表已存在，无需创建。")
            return
        
        print(f"需要创建的表: {tables_needed}")
        
        # 创建表
        db.create_all()
        
        # 验证表是否创建成功
        inspector = inspect(db.engine)
        new_tables = inspector.get_table_names()
        
        created = []
        for table in tables_to_create:
            if table in new_tables:
                created.append(table)
                print(f"✓ 表 '{table}' 创建成功")
            else:
                print(f"✗ 表 '{table}' 创建失败")
        
        print(f"\n总计: {len(created)}/{len(tables_to_create)} 个表创建成功")

if __name__ == '__main__':
    add_tables()
