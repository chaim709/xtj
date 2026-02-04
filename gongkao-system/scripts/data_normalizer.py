"""
数据标准化器 - 标准化各字段的数据格式
"""
import pandas as pd
import re
from typing import Optional


class DataNormalizer:
    """数据标准化器"""
    
    @staticmethod
    def normalize(df: pd.DataFrame, city: str, is_provincial: bool) -> pd.DataFrame:
        """
        标准化整个DataFrame
        
        Args:
            df: 映射后的DataFrame
            city: 城市名称
            is_provincial: 是否省级文件
            
        Returns:
            标准化后的DataFrame
        """
        result_df = pd.DataFrame(index=df.index)
        
        # 固定字段
        result_df['year'] = pd.Series([2026] * len(df), index=df.index)
        result_df['exam_type'] = pd.Series(['事业单位'] * len(df), index=df.index)
        result_df['city'] = pd.Series([DataNormalizer.normalize_city_name(city)] * len(df), index=df.index)
        result_df['affiliation'] = pd.Series(['省' if is_provincial else '市'] * len(df), index=df.index)
        
        # 从原数据映射和标准化
        result_df['region_name'] = df.get('region_name')  # 可能为空
        result_df['system_type'] = df.get('unit_type')  # 单位类别
        result_df['department_code'] = df.get('department_code')
        
        # 单位名称（优先使用"招聘单位"，其次"主管部门"）
        # 处理合并单元格的情况：向下填充空值
        dept_name = df.get('department_name')
        if dept_name is not None:
            dept_name = dept_name.fillna(method='ffill')  # 向下填充
        result_df['department_name'] = dept_name
        
        # 如果还是全空，使用主管部门
        if result_df['department_name'].isna().all():
            dept_alt = df.get('department_name_alt')
            if dept_alt is not None:
                dept_alt = dept_alt.fillna(method='ffill')
            result_df['department_name'] = dept_alt
        
        result_df['position_code'] = df.get('position_code')
        result_df['position_name'] = df.get('position_name')
        
        # 职位简介（使用备注字段）
        result_df['position_desc'] = df.get('remark')
        
        # 考试类别标准化
        result_df['exam_category'] = df.get('exam_category').apply(
            DataNormalizer.normalize_exam_category
        )
        
        result_df['open_ratio'] = 3  # 默认1:3开考比例
        
        # 招聘人数标准化
        result_df['recruit_count'] = df.get('recruit_count').apply(
            DataNormalizer.normalize_recruit_count
        )
        
        # 学历标准化
        result_df['education'] = df.get('education').apply(
            DataNormalizer.normalize_education
        )
        
        # 专业要求
        result_df['major_requirement'] = df.get('major_requirement')
        
        # 其他条件（合并年龄、学位、其他条件）
        result_df['other_requirements'] = df.apply(
            lambda row: DataNormalizer.combine_requirements(
                row.get('age'),
                row.get('other_requirements'),
                row.get('degree')
            ), axis=1
        )
        
        # 竞争数据字段（暂时为空，报名后更新）
        result_df['apply_count'] = None
        result_df['competition_ratio'] = None
        result_df['min_entry_score'] = None
        result_df['max_entry_score'] = None
        result_df['max_xingce_score'] = None
        result_df['max_shenlun_score'] = None
        result_df['max_police_score'] = None
        result_df['min_police_score'] = None
        
        return result_df
    
    @staticmethod
    def normalize_education(value) -> Optional[str]:
        """学历标准化"""
        if pd.isna(value):
            return None
        
        value = str(value).strip()
        
        # 标准化映射
        if '博士' in value:
            return '博士及以上'
        elif '硕士' in value or ('研究生' in value and '本科' not in value):
            return '研究生及以上'
        elif '本科' in value:
            if '及以上' in value or '以上' in value:
                return '本科及以上'
            elif '仅限' in value or '限' in value:
                return '仅限本科'
            else:
                return '本科及以上'
        elif '大专' in value or '专科' in value:
            return '大专及以上'
        
        # 保持原样
        return value
    
    @staticmethod
    def normalize_exam_category(value) -> Optional[str]:
        """考试类别标准化"""
        if pd.isna(value):
            return None
        
        value = str(value).strip()
        
        # 标准化格式
        if 'A' in value or '综合管理' in value:
            return '综合管理类(A类)'
        elif 'B' in value or '社会科学' in value:
            return '社会科学专技类(B类)'
        elif 'C' in value or '自然科学' in value:
            return '自然科学专技类(C类)'
        elif 'D' in value or '教师' in value or '中小学' in value:
            return '中小学教师类(D类)'
        elif 'E' in value or '医疗' in value or '卫生' in value:
            return '医疗卫生类(E类)'
        
        # 保持原样
        return value
    
    @staticmethod
    def normalize_recruit_count(value) -> int:
        """招聘人数标准化"""
        if pd.isna(value):
            return 1  # 默认1人
        
        try:
            count = int(float(value))
            return max(count, 1)  # 至少1人
        except:
            return 1
    
    @staticmethod
    def normalize_city_name(value: str) -> str:
        """城市名称标准化"""
        if not value or pd.isna(value):
            return None
        
        value = str(value).strip()
        
        # 省直保持不变
        if value == '省直':
            return value
        
        # 确保以"市"结尾
        if not value.endswith('市'):
            value = value + '市'
        
        return value
    
    @staticmethod
    def combine_requirements(age, other, degree) -> Optional[str]:
        """合并其他条件"""
        parts = []
        
        if pd.notna(age):
            age_str = str(age).strip()
            if age_str:
                parts.append(age_str)
        
        if pd.notna(degree):
            degree_str = str(degree).strip()
            if degree_str:
                parts.append(f"学位：{degree_str}")
        
        if pd.notna(other):
            other_str = str(other).strip()
            if other_str:
                parts.append(other_str)
        
        return '；'.join(parts) if parts else None


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts')
    from excel_parser import ExcelParser
    from field_mapper import FieldMapper
    
    # 测试文件
    test_file = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/蚌埠市岗位表/蚌埠市事业单位2026年度公开招聘工作人员岗位计划表.xlsx"
    config_file = "/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_field_mapping.json"
    
    print("="*60)
    print("测试数据标准化器")
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
    print(f"\n标准化后的列名: {list(normalized_df.columns)}")
    print(f"\n前3行数据:")
    
    # 只显示关键字段
    key_fields = ['year', 'exam_type', 'city', 'department_name', 'position_name', 
                  'recruit_count', 'education', 'exam_category']
    print(normalized_df[key_fields].head(3).to_string())
