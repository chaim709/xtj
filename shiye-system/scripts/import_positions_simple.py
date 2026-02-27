"""
简化的数据导入脚本 - 使用csv模块
"""
import sys
import os
import csv
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend'))

from app import create_app, db
from app.models.position import Position
from app.services.analysis_service import AnalysisService


def import_positions_from_csv():
    """从CSV导入岗位数据（简化版）"""
    app = create_app('development')
    
    with app.app_context():
        csv_path = project_root.parent / '安徽省事业单位' / '整合后总表_2026年安徽省事业单位岗位.csv'
        
        print("=" * 60)
        print("安徽事业单位岗位数据导入（简化版）")
        print("=" * 60)
        print(f"\nCSV文件: {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"❌ 文件不存在")
            return
        
        print("\n[1/4] 读取CSV文件...")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"✅ 读取 {len(rows)} 条记录")
        
        print("\n[2/4] 清空现有数据...")
        Position.query.delete()
        db.session.commit()
        print("✅ 已清空")
        
        print("\n[3/4] 导入数据...")
        imported = 0
        
        for row in rows:
            try:
                position = Position(
                    year=int(row['year']) if row.get('year') and row['year'].strip() else 2026,
                    exam_type='事业单位',
                    city=row.get('city', '').strip() or None,
                    affiliation=row.get('affiliation', '').strip() or None,
                    region_name=row.get('region_name', '').strip() or None,
                    system_type=row.get('system_type', '').strip() or None,
                    department_code=row.get('department_code', '').strip() or None,
                    department_name=row.get('department_name', '').strip() or None,
                    position_code=row.get('position_code', '').strip() or None,
                    position_name=row.get('position_name', '').strip() or None,
                    position_desc=row.get('position_desc', '').strip() or None,
                    exam_category=row.get('exam_category', '').strip() or None,
                    recruit_count=int(float(row.get('recruit_count', 1))) if row.get('recruit_count', '').strip() else 1,
                    education=row.get('education', '').strip() or None,
                    major_requirement=row.get('major_requirement', '').strip() or None,
                    other_requirements=row.get('other_requirements', '').strip() or None
                )
                
                db.session.add(position)
                imported += 1
                
                if imported % 100 == 0:
                    db.session.commit()
                    print(f"  已导入 {imported}/{len(rows)}...")
            
            except Exception as e:
                print(f"  ⚠️ 跳过错误行: {e}")
                continue
        
        db.session.commit()
        print(f"✅ 成功导入 {imported} 条记录")
        
        print("\n[4/4] 预估数据...")
        count = AnalysisService.estimate_position_data()
        print(f"✅ 预估完成: {count} 个岗位")
        
        # 统计
        print("\n" + "=" * 60)
        print("导入统计:")
        print("=" * 60)
        
        total_positions = Position.query.count()
        total_recruit = db.session.query(db.func.sum(Position.recruit_count)).scalar() or 0
        cities_count = db.session.query(db.func.count(db.func.distinct(Position.city))).scalar() or 0
        
        print(f"  总岗位数: {total_positions}")
        print(f"  总招聘人数: {total_recruit}")
        print(f"  覆盖城市: {cities_count}")
        print("\n✅ 数据导入完成！")


if __name__ == '__main__':
    import_positions_from_csv()
