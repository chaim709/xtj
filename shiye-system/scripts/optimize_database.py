"""
数据库优化脚本 - 创建索引提升查询性能
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend'))

from app import create_app, db


def create_indexes():
    """创建数据库索引"""
    app = create_app('development')
    
    with app.app_context():
        print("=" * 60)
        print("数据库性能优化 - 创建索引")
        print("=" * 60)
        
        # 创建索引SQL
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_positions_year_exam ON positions(year, exam_type);",
            "CREATE INDEX IF NOT EXISTS idx_positions_city ON positions(city);",
            "CREATE INDEX IF NOT EXISTS idx_positions_system ON positions(system_type);",
            "CREATE INDEX IF NOT EXISTS idx_positions_education ON positions(education);",
            "CREATE INDEX IF NOT EXISTS idx_positions_category ON positions(exam_category);",
            "CREATE INDEX IF NOT EXISTS idx_positions_dept_name ON positions(department_name);",
            "CREATE INDEX IF NOT EXISTS idx_positions_competition ON positions(estimated_competition_ratio);",
            "CREATE INDEX IF NOT EXISTS idx_positions_score ON positions(recommendation_score);",
            "CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_favorites_position ON favorites(position_id);",
            "CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_recommendations_created ON recommendations(created_at);"
        ]
        
        for idx_sql in indexes:
            try:
                db.session.execute(db.text(idx_sql))
                print(f"✅ {idx_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                print(f"⚠️ 索引创建失败: {e}")
        
        db.session.commit()
        
        print("\n✅ 索引创建完成！")
        print("=" * 60)


if __name__ == '__main__':
    create_indexes()
