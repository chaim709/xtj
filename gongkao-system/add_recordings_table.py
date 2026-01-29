"""
添加录播表脚本

执行此脚本将创建 course_recordings 表

使用方法：
    python add_recordings_table.py
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.course import CourseRecording


def add_recordings_table():
    """添加录播表"""
    app = create_app('development')
    
    with app.app_context():
        print("=" * 50)
        print("添加课程录播表")
        print("=" * 50)
        
        # 创建所有表（会自动忽略已存在的表）
        print("\n创建 course_recordings 表...")
        db.create_all()
        print("✅ 表创建完成")
        
        # 检查表状态
        count = CourseRecording.query.count()
        print(f"\ncourse_recordings 表当前有 {count} 条记录")
        
        print("\n" + "=" * 50)
        print("完成！")
        print("=" * 50)
        print("\n现在可以在系统中使用录播管理功能：")
        print("  - 课程管理 -> 录播管理")
        print("  - 班次详情页 -> 课程录播标签")
        print("  - 学员详情页 -> 课程录播区块")


if __name__ == '__main__':
    add_recordings_table()
