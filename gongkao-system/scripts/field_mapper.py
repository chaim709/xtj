"""
字段映射器 - 将Excel列名映射到标准字段
"""
import json
import pandas as pd
from typing import Dict, List, Tuple, Optional


class FieldMapper:
    """字段映射器"""
    
    def __init__(self, config_path: str):
        """
        初始化映射器
        
        Args:
            config_path: 映射配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def map_fields(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        字段映射
        
        Args:
            df: 原始DataFrame
            
        Returns:
            (映射后的DataFrame, 映射日志)
        """
        mapped_df = pd.DataFrame()
        mapping_log = {}
        
        columns = list(df.columns)
        
        # 遍历所有标准字段配置
        for field_name, config in self.config.items():
            keywords = config['keywords']
            target_field = config['target_field']
            
            # 查找匹配的列
            matched_col = self.find_matching_column(columns, keywords)
            
            if matched_col:
                mapped_df[target_field] = df[matched_col]
                mapping_log[target_field] = {
                    'source': matched_col,
                    'field_name': field_name,
                    'found': True
                }
            else:
                mapped_df[target_field] = None
                mapping_log[target_field] = {
                    'source': None,
                    'field_name': field_name,
                    'found': False
                }
        
        return mapped_df, mapping_log
    
    def find_matching_column(self, columns: List[str], keywords: List[str]) -> Optional[str]:
        """
        查找匹配的列
        
        Args:
            columns: 列名列表
            keywords: 关键词列表
            
        Returns:
            匹配的列名，如果未找到返回None
        """
        # 精确匹配优先
        for keyword in keywords:
            if keyword in columns:
                return keyword
        
        # 模糊匹配（列名包含关键词）
        for col in columns:
            # 跳过NaN或非字符串列名
            if col is None or not isinstance(col, str):
                continue
            for keyword in keywords:
                if keyword in col:
                    return col
        
        return None
    
    def print_mapping_summary(self, mapping_log: Dict):
        """打印映射摘要"""
        found_count = sum(1 for log in mapping_log.values() if log['found'])
        total_count = len(mapping_log)
        
        print(f"\n字段映射结果:")
        print(f"  成功映射: {found_count}/{total_count} 个字段")
        
        # 显示未找到的字段
        not_found = [log['field_name'] for log in mapping_log.values() if not log['found']]
        if not_found:
            print(f"\n  未找到的字段:")
            for field in not_found:
                print(f"    - {field}")
        
        # 显示映射详情
        print(f"\n  映射详情:")
        for target_field, log in mapping_log.items():
            if log['found']:
                print(f"    {target_field} ← {log['source']}")


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts')
    from excel_parser import ExcelParser
    
    # 测试文件
    test_file = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/蚌埠市岗位表/蚌埠市事业单位2026年度公开招聘工作人员岗位计划表.xlsx"
    config_file = "/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_field_mapping.json"
    
    print("="*60)
    print("测试字段映射器")
    print("="*60)
    
    # 1. 解析Excel
    parser = ExcelParser()
    df, result = parser.parse_excel(test_file)
    
    if not result.success:
        print(f"解析失败: {result.error}")
        sys.exit(1)
    
    print(f"✓ Excel解析成功，共 {result.rows} 行")
    print(f"  原始列名: {list(df.columns)}")
    
    # 2. 字段映射
    mapper = FieldMapper(config_file)
    mapped_df, mapping_log = mapper.map_fields(df)
    
    mapper.print_mapping_summary(mapping_log)
    
    # 3. 显示映射后的数据
    print(f"\n映射后的列名: {list(mapped_df.columns)}")
    print(f"\n前3行数据:")
    print(mapped_df.head(3).to_string())
