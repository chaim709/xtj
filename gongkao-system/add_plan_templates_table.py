"""
数据库迁移脚本 - 添加 plan_templates 表
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.study_plan import PlanTemplate

def add_plan_templates_table():
    """添加计划模板表"""
    app = create_app()
    
    with app.app_context():
        # 检查表是否存在
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'plan_templates' in existing_tables:
            print("✓ plan_templates 表已存在")
        else:
            # 创建表
            PlanTemplate.__table__.create(db.engine)
            print("✓ 成功创建 plan_templates 表")
        
        # 添加一些默认模板
        if PlanTemplate.query.count() == 0:
            default_templates = [
                {
                    'name': '基础阶段30天计划',
                    'phase': 'foundation',
                    'duration_days': 30,
                    'description': '适合刚开始备考的学员，重点打好基础知识',
                },
                {
                    'name': '提高阶段45天计划',
                    'phase': 'improvement',
                    'duration_days': 45,
                    'description': '适合有一定基础的学员，强化薄弱环节',
                },
                {
                    'name': '冲刺阶段15天计划',
                    'phase': 'sprint',
                    'duration_days': 15,
                    'description': '考前冲刺，模拟训练和查漏补缺',
                },
            ]
            
            for t_data in default_templates:
                template = PlanTemplate(
                    name=t_data['name'],
                    phase=t_data['phase'],
                    duration_days=t_data['duration_days'],
                    description=t_data['description'],
                )
                db.session.add(template)
            
            db.session.commit()
            print(f"✓ 添加了 {len(default_templates)} 个默认模板")
        else:
            print(f"✓ 已有 {PlanTemplate.query.count()} 个模板")
        
        print("\n迁移完成！")

if __name__ == '__main__':
    add_plan_templates_table()
