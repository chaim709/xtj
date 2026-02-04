#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第九章报告：数据洞察与隐藏机会
"""

import pandas as pd
import numpy as np
import re
from collections import Counter

# 读取数据
df = pd.read_csv('安徽省事业单位/整合后总表_2026年安徽省事业单位岗位.csv')

# 数据预处理
df['is_base_service'] = df['position_desc'].str.contains('服务基层|三支一扶|大学生村官|西部计划|特岗教师', na=False, case=False)
df['is_veteran'] = df['other_requirements'].str.contains('退役|军人|服役', na=False, case=False) | \
                   df['position_desc'].str.contains('退役|军人|服役', na=False, case=False)
df['is_fresh'] = df['position_desc'].str.contains('应届|毕业生|专项招聘应届', na=False, case=False) | \
                 df['other_requirements'].str.contains('应届|毕业生', na=False, case=False)
df['is_disabled'] = df['other_requirements'].str.contains('残疾', na=False, case=False) | \
                    df['position_desc'].str.contains('残疾', na=False, case=False)
df['is_local'] = df['other_requirements'].str.contains('户籍|本地|本市|本县|本区', na=False, case=False)
df['is_no_major'] = df['major_requirement'].isna() | \
                     df['major_requirement'].str.contains('不限|专业不限', na=False, case=False)

# 地区经济排名（基于GDP，2024年数据）
city_gdp_rank = {
    '合肥市': 1, '芜湖市': 2, '滁州市': 3, '阜阳市': 4, '安庆市': 5,
    '马鞍山市': 6, '蚌埠市': 7, '六安市': 8, '宣城市': 9, '淮南市': 10,
    '淮北市': 11, '铜陵市': 12, '宿州市': 13, '黄山市': 14, '池州市': 15,
    '省直': 0  # 省直单独处理
}

df['city_gdp_rank'] = df['city'].map(city_gdp_rank).fillna(16)

# 计算性价比评分（简化版）
def calculate_value_score(row):
    score = 0
    
    # 地区得分（GDP排名越低越好，得分越高）
    if row['city'] == '省直':
        score += 30
    elif row['city'] == '合肥市':
        score += 25
    elif row['city'] in ['芜湖市', '滁州市']:
        score += 20
    elif row['city'] in ['阜阳市', '安庆市', '马鞍山市']:
        score += 15
    else:
        score += 10
    
    # 招聘人数（越多越好）
    if row['recruit_count'] >= 3:
        score += 15
    elif row['recruit_count'] == 2:
        score += 10
    else:
        score += 5
    
    # 专业限制（有专业限制竞争小）
    if not row['is_no_major']:
        score += 10
    
    # 学历要求（本科及以上适中）
    if pd.notna(row['education']):
        if '本科及以上' in str(row['education']):
            score += 10
        elif '大专及以上' in str(row['education']):
            score += 8
        elif '研究生' in str(row['education']):
            score += 5
    
    # 定向岗位加分
    if row['is_base_service'] or row['is_veteran'] or row['is_fresh']:
        score += 15
    
    return score

df['value_score'] = df.apply(calculate_value_score, axis=1)

# 找出黄金岗位（好单位+冷门专业）
def is_good_unit(row):
    """判断是否是好单位"""
    good_keywords = ['省', '市', '中心', '局', '院', '校', '馆', '所']
    dept = str(row['department_name']) if pd.notna(row['department_name']) else ''
    return any(kw in dept for kw in good_keywords)

df['is_good_unit'] = df.apply(is_good_unit, axis=1)

# 冷门专业判断（招聘人数<5的专业）
major_counts = df[~df['is_no_major']].groupby('major_requirement')['recruit_count'].sum()
cold_majors = set(major_counts[major_counts < 5].index)
df['is_cold_major'] = df['major_requirement'].isin(cold_majors)

# 黄金岗位：好单位 + 冷门专业
df['is_golden'] = df['is_good_unit'] & df['is_cold_major'] & (~df['is_no_major'])

# 保存分析结果供报告使用
analysis_results = {
    'total_positions': len(df),
    'total_recruit': int(df['recruit_count'].sum()),
    'base_service': {'count': int(df['is_base_service'].sum()), 'recruit': int(df[df['is_base_service']]['recruit_count'].sum())},
    'veteran': {'count': int(df['is_veteran'].sum()), 'recruit': int(df[df['is_veteran']]['recruit_count'].sum())},
    'fresh': {'count': int(df['is_fresh'].sum()), 'recruit': int(df[df['is_fresh']]['recruit_count'].sum())},
    'disabled': {'count': int(df['is_disabled'].sum()), 'recruit': int(df[df['is_disabled']]['recruit_count'].sum())},
    'local': {'count': int(df['is_local'].sum()), 'recruit': int(df[df['is_local']]['recruit_count'].sum())},
    'no_major': {'count': int(df['is_no_major'].sum()), 'recruit': int(df[df['is_no_major']]['recruit_count'].sum())},
    'golden_positions': df[df['is_golden']].head(30),
    'top50_value': df.nlargest(50, 'value_score'),
    'city_stats': df.groupby('city').agg({
        'recruit_count': ['sum', 'mean'],
        'position_code': 'count'
    }).round(2)
}

print("分析完成！")
print(f"黄金岗位数量: {df['is_golden'].sum()}")
print(f"TOP50性价比岗位已识别")

# 保存详细数据到CSV供报告参考
df[df['is_golden']].to_csv('scripts/golden_positions.csv', index=False, encoding='utf-8-sig')
df.nlargest(50, 'value_score').to_csv('scripts/top50_value_positions.csv', index=False, encoding='utf-8-sig')

print("数据已保存到 scripts/ 目录")
