#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第九章数据分析脚本：数据洞察与隐藏机会
"""

import pandas as pd
import numpy as np
import re
from collections import Counter

# 读取数据
df = pd.read_csv('安徽省事业单位/整合后总表_2026年安徽省事业单位岗位.csv')

print("=" * 80)
print("第九章数据分析：数据洞察与隐藏机会")
print("=" * 80)

# 基础统计
print(f"\n【基础数据】")
print(f"总岗位数: {len(df)}")
print(f"总招聘人数: {df['recruit_count'].sum()}")
print(f"平均每岗: {df['recruit_count'].sum() / len(df):.2f}人")

# 1. 定向岗位分析
print(f"\n【定向岗位分析】")

# 服务基层项目人员
df['is_base_service'] = df['position_desc'].str.contains('服务基层|三支一扶|大学生村官|西部计划|特岗教师', na=False, case=False)
base_service_count = df['is_base_service'].sum()
base_service_recruit = df[df['is_base_service']]['recruit_count'].sum()
print(f"服务基层项目人员定向岗: {base_service_count}岗/{base_service_recruit}人")

# 退役军人
df['is_veteran'] = df['other_requirements'].str.contains('退役|军人|服役', na=False, case=False) | \
                   df['position_desc'].str.contains('退役|军人|服役', na=False, case=False)
veteran_count = df['is_veteran'].sum()
veteran_recruit = df[df['is_veteran']]['recruit_count'].sum()
print(f"退役军人定向岗: {veteran_count}岗/{veteran_recruit}人")

# 应届毕业生
df['is_fresh'] = df['position_desc'].str.contains('应届|毕业生|专项招聘应届', na=False, case=False) | \
                 df['other_requirements'].str.contains('应届|毕业生', na=False, case=False)
fresh_count = df['is_fresh'].sum()
fresh_recruit = df[df['is_fresh']]['recruit_count'].sum()
print(f"应届毕业生定向岗: {fresh_count}岗/{fresh_recruit}人")

# 残疾人
df['is_disabled'] = df['other_requirements'].str.contains('残疾', na=False, case=False) | \
                    df['position_desc'].str.contains('残疾', na=False, case=False)
disabled_count = df['is_disabled'].sum()
disabled_recruit = df[df['is_disabled']]['recruit_count'].sum()
print(f"残疾人岗位: {disabled_count}岗/{disabled_recruit}人")

# 本地户籍
df['is_local'] = df['other_requirements'].str.contains('户籍|本地|本市|本县|本区', na=False, case=False)
local_count = df['is_local'].sum()
local_recruit = df[df['is_local']]['recruit_count'].sum()
print(f"本地户籍优先岗位: {local_count}岗/{local_recruit}人")

# 2. 专业不限岗位分析
print(f"\n【专业不限岗位分析】")
df['is_no_major'] = df['major_requirement'].isna() | \
                     df['major_requirement'].str.contains('不限|专业不限', na=False, case=False)
no_major_count = df['is_no_major'].sum()
no_major_recruit = df[df['is_no_major']]['recruit_count'].sum()
print(f"专业不限岗位: {no_major_count}岗/{no_major_recruit}人")

# 3. 招聘人数分布
print(f"\n【招聘人数分布】")
recruit_dist = df['recruit_count'].value_counts().sort_index()
print("每岗招聘人数分布:")
for count, num_positions in recruit_dist.head(10).items():
    print(f"  {count}人: {num_positions}岗")

# 4. 地区分布
print(f"\n【地区分布】")
city_dist = df.groupby('city').agg({
    'recruit_count': 'sum',
    'position_code': 'count'
}).round(2)
city_dist.columns = ['招聘人数', '岗位数']
city_dist = city_dist.sort_values('招聘人数', ascending=False)
print(city_dist.head(10))

# 5. 单位类型分析
print(f"\n【单位类型分析】")
if 'system_type' in df.columns:
    system_dist = df['system_type'].value_counts()
    print(system_dist.head(10))

# 6. 考试类别分布
print(f"\n【考试类别分布】")
exam_dist = df['exam_category'].value_counts()
print(exam_dist)

# 7. 学历要求分布
print(f"\n【学历要求分布】")
edu_dist = df['education'].value_counts()
print(edu_dist.head(10))

print("\n分析完成！")
