"""
添加智能选岗相关数据库表

运行方式：python add_position_tables.py
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.position import Position, StudentPosition
from app.models.major import MajorCategory, Major, MAJOR_CATEGORIES

def create_tables():
    """创建智能选岗相关表"""
    app = create_app()
    with app.app_context():
        # 创建表
        db.create_all()
        print("✅ 数据库表创建成功")
        
        # 检查是否已有专业大类数据
        existing_count = MajorCategory.query.count()
        if existing_count == 0:
            # 初始化50个专业大类
            print("正在初始化专业大类...")
            for code, name in MAJOR_CATEGORIES:
                category = MajorCategory(code=code, name=name, year=2026)
                db.session.add(category)
            
            db.session.commit()
            print(f"✅ 已初始化 {len(MAJOR_CATEGORIES)} 个专业大类")
        else:
            print(f"ℹ️ 已存在 {existing_count} 个专业大类，跳过初始化")
        
        # 打印表信息
        print("\n📊 数据库表状态：")
        print(f"  - positions: {Position.query.count()} 条岗位数据")
        print(f"  - major_categories: {MajorCategory.query.count()} 个专业大类")
        print(f"  - majors: {Major.query.count()} 个具体专业")
        print(f"  - student_positions: {StudentPosition.query.count()} 条关联数据")

if __name__ == '__main__':
    create_tables()
