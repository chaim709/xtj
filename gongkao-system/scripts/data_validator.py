"""
数据验证器 - 验证数据完整性和正确性
"""
import pandas as pd
from typing import Dict, List


class DataValidator:
    """数据验证器"""
    
    # 必填字段
    REQUIRED_FIELDS = [
        'year', 'exam_type', 'city', 'department_name', 
        'position_name', 'recruit_count'
    ]
    
    @staticmethod
    def validate_row(row: pd.Series, row_idx: int) -> Dict:
        """
        验证单行数据
        
        Args:
            row: 数据行
            row_idx: 行索引
            
        Returns:
            验证结果字典
        """
        errors = []
        warnings = []
        
        # 1. 必填字段检查
        for field in DataValidator.REQUIRED_FIELDS:
            if pd.isna(row.get(field)) or row.get(field) == '':
                errors.append(f"缺少必填字段: {field}")
        
        # 2. 招聘人数检查
        recruit_count = row.get('recruit_count')
        if pd.notna(recruit_count):
            try:
                count = int(recruit_count)
                if count <= 0:
                    errors.append("招聘人数必须大于0")
            except:
                errors.append("招聘人数格式错误")
        
        # 3. 年份检查
        year = row.get('year')
        if pd.notna(year):
            try:
                year_int = int(year)
                if year_int != 2026:
                    warnings.append(f"年份异常: {year_int}")
            except:
                errors.append("年份格式错误")
        
        # 4. 岗位代码检查（警告）
        if pd.isna(row.get('position_code')):
            warnings.append("缺少岗位代码")
        
        # 5. 专业要求检查（警告）
        if pd.isna(row.get('major_requirement')):
            warnings.append("缺少专业要求")
        
        # 6. 学历检查（警告）
        if pd.isna(row.get('education')):
            warnings.append("缺少学历要求")
        
        return {
            'row_idx': row_idx,
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Dict:
        """
        验证整个DataFrame
        
        Args:
            df: 待验证的DataFrame
            
        Returns:
            验证结果字典
        """
        results = {
            'total': len(df),
            'valid': 0,
            'invalid': 0,
            'warnings_count': 0,
            'error_rows': [],
            'warning_rows': []
        }
        
        for idx, row in df.iterrows():
            validation = DataValidator.validate_row(row, idx)
            
            if validation['valid']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
                results['error_rows'].append({
                    'row': idx,
                    'errors': validation['errors']
                })
            
            if validation['warnings']:
                results['warnings_count'] += 1
                results['warning_rows'].append({
                    'row': idx,
                    'warnings': validation['warnings']
                })
        
        return results
    
    @staticmethod
    def print_validation_summary(results: Dict):
        """打印验证摘要"""
        print(f"\n数据验证结果:")
        print(f"  总行数: {results['total']}")
        print(f"  有效行: {results['valid']} ({results['valid']/results['total']*100:.1f}%)")
        print(f"  无效行: {results['invalid']} ({results['invalid']/results['total']*100:.1f}%)")
        print(f"  警告行: {results['warnings_count']} ({results['warnings_count']/results['total']*100:.1f}%)")
        
        # 显示错误详情（最多显示5个）
        if results['error_rows']:
            print(f"\n  错误详情 (显示前5个):")
            for error in results['error_rows'][:5]:
                print(f"    行 {error['row']}: {'; '.join(error['errors'])}")
        
        # 显示警告详情（最多显示3个）
        if results['warning_rows']:
            print(f"\n  警告详情 (显示前3个):")
            for warning in results['warning_rows'][:3]:
                print(f"    行 {warning['row']}: {'; '.join(warning['warnings'])}")
    
    @staticmethod
    def get_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
        """
        获取所有有效的行
        
        Args:
            df: DataFrame
            
        Returns:
            只包含有效行的DataFrame
        """
        valid_indices = []
        
        for idx, row in df.iterrows():
            validation = DataValidator.validate_row(row, idx)
            if validation['valid']:
                valid_indices.append(idx)
        
        return df.loc[valid_indices]


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts')
    from excel_parser import ExcelParser
    from field_mapper import FieldMapper
    from data_normalizer import DataNormalizer
    
    # 测试文件
    test_file = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/蚌埠市岗位表/蚌埠市事业单位2026年度公开招聘工作人员岗位计划表.xlsx"
    config_file = "/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_field_mapping.json"
    
    print("="*60)
    print("测试数据验证器")
    print("="*60)
    
    # 1. 解析Excel
    parser = ExcelParser()
    df, result = parser.parse_excel(test_file)
    print(f"✓ 解析完成: {result.rows} 行")
    
    # 2. 字段映射
    mapper = FieldMapper(config_file)
    mapped_df, mapping_log = mapper.map_fields(df)
    print(f"✓ 字段映射完成")
    
    # 3. 数据标准化
    normalizer = DataNormalizer()
    normalized_df = normalizer.normalize(mapped_df, '蚌埠市', False)
    print(f"✓ 数据标准化完成")
    
    # 4. 数据验证
    validator = DataValidator()
    validation_results = validator.validate_dataframe(normalized_df)
    
    validator.print_validation_summary(validation_results)
    
    # 5. 获取有效行
    valid_df = validator.get_valid_rows(normalized_df)
    print(f"\n有效数据: {len(valid_df)} 行")
