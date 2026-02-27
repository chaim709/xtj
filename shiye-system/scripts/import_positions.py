"""
数据导入脚本 - 导入事业单位岗位数据
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend'))

import pandas as pd
from app import create_app, db
from app.models.position import Position
from app.services.analysis_service import AnalysisService

def import_positions_from_csv():
    """从CSV导入岗位数据"""
    app = create_app('development')
    
    with app.app_context():
        # CSV文件路径
        csv_path = app.config['POSITIONS_CSV']
        
        print("=" * 60)
        print("安徽事业单位岗位数据导入")
        print("=" * 60)
        print(f"\nCSV文件路径: {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"❌ 文件不存在: {csv_path}")
            return
        
        # 读取CSV
        print("\n[1/4] 读取CSV文件...")
        df = pd.read_csv(csv_path)
        print(f"✅ 成功读取 {len(df)} 条记录")
        
        # 数据清洗
        print("\n[2/4] 数据清洗...")
        df = df.fillna('')
        
        # 清空现有数据
        print("\n[3/4] 清空现有数据...")
        Position.query.delete()
        db.session.commit()
        print("✅ 已清空")
        
        # 批量导入
        print("\n[4/4] 批量导入数据...")
        imported = 0
        batch_size = 100
        
        for idx, row in df.iterrows():
            position = Position(
                year=int(row['year']) if row['year'] else 2026,
                exam_type='事业单位',
                city=row['city'] if row['city'] else None,
                affiliation=row['affiliation'] if row['affiliation'] else None,
                region_name=row['region_name'] if row['region_name'] else None,
                system_type=row['system_type'] if row['system_type'] else None,
                department_code=str(row['department_code']) if row['department_code'] else None,
                department_name=row['department_name'] if row['department_name'] else None,
                position_code=str(row['position_code']) if row['position_code'] else None,
                position_name=row['position_name'] if row['position_name'] else None,
                position_desc=row['position_desc'] if row['position_desc'] else None,
                exam_category=row['exam_category'] if row['exam_category'] else None,
                open_ratio=int(row['open_ratio']) if row['open_ratio'] and str(row['open_ratio']).replace('.','').isdigit() else None,
                recruit_count=int(row['recruit_count']) if row['recruit_count'] and str(row['recruit_count']).replace('.','').isdigit() else 1,
                education=row['education'] if row['education'] else None,
                major_requirement=row['major_requirement'] if row['major_requirement'] else None,
                other_requirements=row['other_requirements'] if row['other_requirements'] else None,
                apply_count=int(row['apply_count']) if row.get('apply_count') and str(row['apply_count']).replace('.','').isdigit() else None,
                competition_ratio=float(row['competition_ratio']) if row.get('competition_ratio') and str(row['competition_ratio']).replace('.','').replace('-','').isdigit() else None,
                min_entry_score=float(row['min_entry_score']) if row.get('min_entry_score') and str(row['min_entry_score']).replace('.','').isdigit() else None,
                max_entry_score=float(row['max_entry_score']) if row.get('max_entry_score') and str(row['max_entry_score']).replace('.','').isdigit() else None
            )
            
            db.session.add(position)
            imported += 1
            
            # 批量提交
            if imported % batch_size == 0:
                db.session.commit()
                print(f"  已导入 {imported}/{len(df)} 条记录...")
        
        # 最后提交
        db.session.commit()
        print(f"✅ 成功导入 {imported} 条记录")
        
        # 预估数据
        print("\n[5/5] 预估薪资、竞争比、难度...")
        count = AnalysisService.estimate_position_data()
        print(f"✅ 已为 {count} 个岗位预估数据")
        
        # 统计
        print("\n" + "=" * 60)
        print("导入统计:")
        print("=" * 60)
        
        stats = {
            '总岗位数': Position.query.count(),
            '总招聘人数': db.session.query(db.func.sum(Position.recruit_count)).scalar() or 0,
            '城市数量': db.session.query(db.func.count(db.func.distinct(Position.city))).scalar() or 0,
            '单位数量': db.session.query(db.func.count(db.func.distinct(Position.department_name))).scalar() or 0
        }
        
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 数据导入完成！")


if __name__ == '__main__':
    import_positions_from_csv()
