"""
数据库导入器 - 将数据导入Position表
"""
import sys
import os
import pandas as pd
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.position import Position


class DatabaseImporter:
    """数据库导入器"""
    
    BATCH_SIZE = 500
    
    def __init__(self):
        """初始化Flask应用上下文"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def __del__(self):
        """清理应用上下文"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def clear_existing_data(self) -> int:
        """
        清空现有事业单位数据
        
        Returns:
            删除的记录数
        """
        try:
            deleted = Position.query.filter(
                Position.year == 2026,
                Position.exam_type == '事业单位'
            ).delete()
            db.session.commit()
            
            print(f"✓ 清空旧数据: {deleted} 条记录")
            return deleted
        
        except Exception as e:
            db.session.rollback()
            print(f"✗ 清空数据失败: {str(e)}")
            raise
    
    def import_data(self, df: pd.DataFrame) -> Dict:
        """
        批量导入数据
        
        Args:
            df: 待导入的DataFrame
            
        Returns:
            导入结果字典
        """
        total = len(df)
        imported = 0
        failed = 0
        errors = []
        
        print(f"\n开始导入数据 (共 {total} 条)...")
        
        # 转换为字典列表
        records = df.to_dict('records')
        
        # 处理NaN值
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        # 分批导入
        for i in range(0, total, self.BATCH_SIZE):
            batch = records[i:i + self.BATCH_SIZE]
            
            try:
                db.session.bulk_insert_mappings(Position, batch)
                db.session.commit()
                imported += len(batch)
                
                # 进度显示
                progress = (i + len(batch)) / total * 100
                print(f"  导入进度: {progress:.1f}% ({i + len(batch)}/{total})")
            
            except Exception as e:
                db.session.rollback()
                failed += len(batch)
                error_msg = str(e)
                errors.append({
                    'batch': i // self.BATCH_SIZE,
                    'start_row': i,
                    'end_row': i + len(batch),
                    'error': error_msg
                })
                print(f"  ✗ 批次 {i // self.BATCH_SIZE} 导入失败: {error_msg}")
        
        print(f"\n导入完成!")
        print(f"  成功: {imported} 条")
        print(f"  失败: {failed} 条")
        
        return {
            'total': total,
            'imported': imported,
            'failed': failed,
            'errors': errors
        }
    
    def verify_data(self) -> Dict:
        """验证导入的数据"""
        try:
            count = Position.query.filter(
                Position.year == 2026,
                Position.exam_type == '事业单位'
            ).count()
            
            # 按城市统计
            city_stats = db.session.query(
                Position.city,
                db.func.count(Position.id),
                db.func.sum(Position.recruit_count)
            ).filter(
                Position.year == 2026,
                Position.exam_type == '事业单位'
            ).group_by(Position.city).all()
            
            return {
                'total_count': count,
                'by_city': {
                    city: {'positions': int(pos_count), 'recruits': int(recruit_sum or 0)}
                    for city, pos_count, recruit_sum in city_stats
                }
            }
        
        except Exception as e:
            print(f"✗ 验证失败: {str(e)}")
            return None


if __name__ == '__main__':
    # 测试代码
    print("数据库导入器模块加载成功")
    
    # 测试数据库连接
    try:
        importer = DatabaseImporter()
        count = Position.query.count()
        print(f"✓ 数据库连接成功，当前Position表共 {count} 条记录")
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
