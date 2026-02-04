#!/usr/bin/env python3
"""
修复省直单位数据导入问题
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from excel_parser import ExcelParser
from field_mapper import FieldMapper
from data_normalizer import DataNormalizer
from data_validator import DataValidator

# 省直事业单位文件
file_path = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/安徽省2026年度省直事业单位统一公开招聘岗位汇总表.xlsx"
config_path = "./shiye_field_mapping.json"

print("="*70)
print("修复省直事业单位数据")
print("="*70)

# 1. 解析
parser = ExcelParser()
df, result = parser.parse_excel(file_path)

print(f"\n✓ 解析完成:")
print(f"  原始行数: {result.rows}")
print(f"  列名: {list(df.columns)}")

# 2. 字段映射
mapper = FieldMapper(config_path)
mapped_df, mapping_log = mapper.map_fields(df)

print(f"\n✓ 字段映射完成")
print(f"  映射的字段:")
for field, log in mapping_log.items():
    if log['found']:
        print(f"    {field}: {log['source']}")

# 3. 标准化
normalizer = DataNormalizer()
normalized_df = normalizer.normalize(mapped_df, '省直', True)

print(f"\n✓ 标准化完成")
print(f"  标准化后行数: {len(normalized_df)}")

# 检查必填字段的填充情况
print(f"\n  必填字段填充情况:")
for field in ['year', 'exam_type', 'city', 'department_name', 'position_name', 'recruit_count']:
    na_count = normalized_df[field].isna().sum()
    fill_rate = (len(normalized_df) - na_count) / len(normalized_df) * 100
    print(f"    {field}: {fill_rate:.1f}% 填充 ({na_count} 个空值)")
    
    if na_count > 0 and na_count <= 5:
        print(f"      空值行: {normalized_df[normalized_df[field].isna()].index.tolist()}")

# 4. 验证
validator = DataValidator()
validation = validator.validate_dataframe(normalized_df)

print(f"\n✓ 验证结果:")
print(f"  有效: {validation['valid']} 行")
print(f"  无效: {validation['invalid']} 行")

if validation['error_rows']:
    print(f"\n  前10个错误示例:")
    for error in validation['error_rows'][:10]:
        print(f"    行{error['row']}: {error['errors']}")

# 5. 获取有效数据
valid_df = validator.get_valid_rows(normalized_df)

print(f"\n✓ 有效数据统计:")
print(f"  有效行数: {len(valid_df)}")
print(f"  招聘人数: {valid_df['recruit_count'].sum()}")

print(f"\n按单位统计（TOP 20）:")
dept_stats = valid_df.groupby('department_name').agg({
    'position_name': 'count',
    'recruit_count': 'sum'
}).sort_values('recruit_count', ascending=False)

for idx, (dept, row) in enumerate(dept_stats.head(20).iterrows(), 1):
    print(f"  {idx}. {dept[:40]}: {int(row['recruit_count'])}人, {int(row['position_name'])}岗位")

# 保存有效数据供导入
valid_df.to_csv('/tmp/provincial_valid_data.csv', index=False, encoding='utf-8-sig')
print(f"\n✓ 有效数据已保存到: /tmp/provincial_valid_data.csv")
