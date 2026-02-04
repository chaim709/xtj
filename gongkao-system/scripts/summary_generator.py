"""
总表生成器 - 合并所有数据生成总表
"""
import pandas as pd
import os
from typing import List, Dict


class SummaryGenerator:
    """总表生成器"""
    
    @staticmethod
    def generate(all_data: List[pd.DataFrame], output_dir: str) -> Dict:
        """
        生成总表
        
        Args:
            all_data: 所有标准化后的DataFrame列表
            output_dir: 输出目录
            
        Returns:
            生成结果字典
        """
        if not all_data:
            return {
                'success': False,
                'error': '没有数据可生成'
            }
        
        # 1. 合并所有数据
        print(f"合并 {len(all_data)} 个数据源...")
        summary_df = pd.concat(all_data, ignore_index=True)
        
        # 2. 排序
        summary_df = summary_df.sort_values(
            by=['city', 'department_name', 'position_code'],
            na_position='last'
        )
        
        # 3. 重置索引
        summary_df = summary_df.reset_index(drop=True)
        
        # 4. 生成Excel文件
        excel_path = os.path.join(
            output_dir, 
            '整合后总表_2026年安徽省事业单位岗位.xlsx'
        )
        
        try:
            summary_df.to_excel(excel_path, index=False, engine='openpyxl')
            print(f"✓ Excel总表生成成功: {excel_path}")
        except Exception as e:
            return {
                'success': False,
                'error': f'生成Excel失败: {str(e)}'
            }
        
        # 5. 生成CSV文件
        csv_path = os.path.join(
            output_dir, 
            '整合后总表_2026年安徽省事业单位岗位.csv'
        )
        
        try:
            summary_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✓ CSV总表生成成功: {csv_path}")
        except Exception as e:
            return {
                'success': False,
                'error': f'生成CSV失败: {str(e)}'
            }
        
        # 6. 生成统计信息
        stats = SummaryGenerator.generate_statistics(summary_df)
        
        return {
            'success': True,
            'excel_path': excel_path,
            'csv_path': csv_path,
            'total_rows': len(summary_df),
            'statistics': stats
        }
    
    @staticmethod
    def generate_statistics(df: pd.DataFrame) -> Dict:
        """生成统计信息"""
        stats = {
            'total_positions': len(df),
            'total_recruit': int(df['recruit_count'].sum()),
            'by_city': {},
            'by_exam_category': {}
        }
        
        # 按城市统计
        city_stats = df.groupby('city').agg({
            'position_name': 'count',
            'recruit_count': 'sum'
        }).to_dict('index')
        
        stats['by_city'] = {
            city: {
                'positions': int(data['position_name']),
                'recruits': int(data['recruit_count'])
            }
            for city, data in city_stats.items()
        }
        
        # 按考试类别统计
        if 'exam_category' in df.columns:
            category_stats = df.groupby('exam_category').agg({
                'position_name': 'count',
                'recruit_count': 'sum'
            }).to_dict('index')
            
            stats['by_exam_category'] = {
                category: {
                    'positions': int(data['position_name']),
                    'recruits': int(data['recruit_count'])
                }
                for category, data in category_stats.items()
                if pd.notna(category)
            }
        
        return stats
    
    @staticmethod
    def print_statistics(stats: Dict):
        """打印统计信息"""
        print(f"\n总表统计信息:")
        print(f"  总岗位数: {stats['total_positions']}")
        print(f"  总招聘人数: {stats['total_recruit']}")
        
        print(f"\n按城市分布:")
        for city, data in sorted(stats['by_city'].items()):
            print(f"  {city}: {data['positions']} 个岗位, {data['recruits']} 人")
        
        if stats['by_exam_category']:
            print(f"\n按考试类别分布:")
            for category, data in sorted(stats['by_exam_category'].items()):
                print(f"  {category}: {data['positions']} 个岗位, {data['recruits']} 人")


if __name__ == '__main__':
    # 测试代码
    print("总表生成器模块加载成功")
