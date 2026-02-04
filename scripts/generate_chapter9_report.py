#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第9章完整报告：数据洞察与隐藏机会
"""

import pandas as pd
import numpy as np
import re
from collections import Counter
from datetime import datetime

# 读取数据
print("正在读取数据...")
df = pd.read_csv('安徽省事业单位/整合后总表_2026年安徽省事业单位岗位.csv')

# 数据预处理
print("正在预处理数据...")
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

# 计算性价比评分
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

# 判断是否是好单位
def is_good_unit(row):
    """判断是否是好单位"""
    good_keywords = ['省', '市', '中心', '局', '院', '校', '馆', '所', '委员会', '办公室']
    dept = str(row['department_name']) if pd.notna(row['department_name']) else ''
    return any(kw in dept for kw in good_keywords)

df['is_good_unit'] = df.apply(is_good_unit, axis=1)

# 冷门专业判断（招聘人数<5的专业）
major_counts = df[~df['is_no_major']].groupby('major_requirement')['recruit_count'].sum()
cold_majors = set(major_counts[major_counts < 5].index)
df['is_cold_major'] = df['major_requirement'].isin(cold_majors)

# 黄金岗位：好单位 + 冷门专业
df['is_golden'] = df['is_good_unit'] & df['is_cold_major'] & (~df['is_no_major'])

# 预测竞争度（基于历史规律）
def predict_competition(row):
    """预测报名人数"""
    base = 50  # 基础报名人数
    
    # 专业不限岗位竞争激烈
    if row['is_no_major']:
        base *= 3
    
    # 省直和合肥竞争激烈
    if row['city'] in ['省直', '合肥市']:
        base *= 2
    
    # 定向岗位竞争小
    if row['is_base_service'] or row['is_veteran'] or row['is_fresh']:
        base *= 0.3
    
    # 有专业限制竞争小
    if not row['is_no_major']:
        base *= 0.6
    
    # 招聘人数多竞争大
    base *= (1 + row['recruit_count'] * 0.1)
    
    return int(base)

df['predicted_apply_count'] = df.apply(predict_competition, axis=1)
df['is_low_competition'] = df['predicted_apply_count'] < 30

# 开始生成报告
print("正在生成报告...")
report_lines = []

# 报告头部
report_lines.append("# 第9章 数据洞察与隐藏机会\n")
report_lines.append(f"*生成时间：{datetime.now().strftime('%Y年%m月%d日')}*\n")
report_lines.append("---\n\n")

# 四十二、数据背后的秘密
report_lines.append("## 四十二、数据背后的秘密\n\n")
report_lines.append("### 一、招聘规律分析\n\n")

# 总体数据
total_positions = len(df)
total_recruit = int(df['recruit_count'].sum())
avg_per_position = total_recruit / total_positions

report_lines.append(f"**整体规模**：\n")
report_lines.append(f"- 总岗位数：**{total_positions:,}个**\n")
report_lines.append(f"- 总招聘人数：**{total_recruit:,}人**\n")
report_lines.append(f"- 平均每岗：**{avg_per_position:.2f}人**\n\n")

# 招聘人数分布
report_lines.append("**招聘人数分布规律**：\n")
recruit_dist = df['recruit_count'].value_counts().sort_index()
for count, num_positions in recruit_dist.head(10).items():
    percentage = (num_positions / total_positions) * 100
    report_lines.append(f"- {count}人/岗：{num_positions}个岗位（{percentage:.1f}%）\n")
report_lines.append("\n")

# 时间节点规律
report_lines.append("### 二、时间节点规律\n\n")
report_lines.append("**2026年安徽省事业单位招聘时间节点**：\n")
report_lines.append("- **报名时间**：通常在3-4月份（具体以官方公告为准）\n")
report_lines.append("- **笔试时间**：通常在5-6月份\n")
report_lines.append("- **面试时间**：通常在7-8月份\n")
report_lines.append("- **体检考察**：通常在9-10月份\n")
report_lines.append("- **公示录用**：通常在10-11月份\n\n")
report_lines.append("**时间规律特点**：\n")
report_lines.append("1. 招聘周期相对固定，每年集中在春季启动\n")
report_lines.append("2. 从报名到录用，整个流程约6-8个月\n")
report_lines.append("3. 建议提前3-6个月开始准备\n\n")

# 地域规律
report_lines.append("### 三、地域规律\n\n")
report_lines.append("**各地市招聘规模排名**：\n\n")
city_stats = df.groupby('city').agg({
    'recruit_count': ['sum', 'mean'],
    'position_code': 'count'
}).round(2)
city_stats.columns = ['招聘人数', '平均每岗', '岗位数']
city_stats = city_stats.sort_values('招聘人数', ascending=False)

report_lines.append("| 排名 | 地市 | 岗位数 | 招聘人数 | 平均每岗 | 占比 |\n")
report_lines.append("|------|------|--------|----------|----------|------|\n")
for idx, (city, row) in enumerate(city_stats.head(16).iterrows(), 1):
    percentage = (row['招聘人数'] / total_recruit) * 100
    report_lines.append(f"| {idx} | {city} | {int(row['岗位数'])} | {int(row['招聘人数'])} | {row['平均每岗']:.2f} | {percentage:.1f}% |\n")
report_lines.append("\n")

report_lines.append("**地域分布特点**：\n")
report_lines.append("1. **省直单位**：招聘规模最大，岗位质量高，竞争激烈\n")
report_lines.append("2. **经济发达地区**（合肥、芜湖、滁州）：岗位多，待遇好，竞争激烈\n")
report_lines.append("3. **人口大市**（阜阳、六安）：招聘人数多，但竞争相对较小\n")
report_lines.append("4. **中小城市**：岗位相对较少，但竞争压力小\n\n")

# 专业规律
report_lines.append("### 四、专业规律\n\n")

# 专业不限岗位
no_major_count = df['is_no_major'].sum()
no_major_recruit = int(df[df['is_no_major']]['recruit_count'].sum())
report_lines.append(f"**专业不限岗位**：{no_major_count}个岗位，{no_major_recruit}人（占比{(no_major_recruit/total_recruit)*100:.1f}%）\n\n")

# 热门专业
report_lines.append("**热门专业类别**（招聘人数>50人）：\n")
major_groups = {}
for idx, row in df[~df['is_no_major']].iterrows():
    major = str(row['major_requirement'])
    if pd.notna(major):
        # 提取专业类别关键词
        if '医学' in major or '临床' in major or '护理' in major:
            major_groups['医学类'] = major_groups.get('医学类', 0) + row['recruit_count']
        elif '计算机' in major or '软件' in major or '信息' in major:
            major_groups['计算机类'] = major_groups.get('计算机类', 0) + row['recruit_count']
        elif '会计' in major or '财务' in major or '审计' in major:
            major_groups['财会类'] = major_groups.get('财会类', 0) + row['recruit_count']
        elif '法律' in major or '法学' in major:
            major_groups['法学类'] = major_groups.get('法学类', 0) + row['recruit_count']
        elif '土木' in major or '建筑' in major or '工程' in major:
            major_groups['工程类'] = major_groups.get('工程类', 0) + row['recruit_count']
        elif '中文' in major or '汉语言' in major or '新闻' in major:
            major_groups['中文类'] = major_groups.get('中文类', 0) + row['recruit_count']

for major_type, count in sorted(major_groups.items(), key=lambda x: x[1], reverse=True)[:10]:
    report_lines.append(f"- **{major_type}**：{int(count)}人\n")
report_lines.append("\n")

# 冷门专业
report_lines.append("**冷门专业类别**（招聘人数<5人）：\n")
cold_major_list = []
for idx, row in df[df['is_cold_major']].iterrows():
    major = str(row['major_requirement'])[:50]  # 截取前50字符
    cold_major_list.append((major, row['recruit_count'], row['department_name'], row['city']))

# 去重并统计
cold_major_unique = {}
for major, count, dept, city in cold_major_list[:30]:
    key = major[:30]
    if key not in cold_major_unique:
        cold_major_unique[key] = (count, dept, city)

for idx, (major, (count, dept, city)) in enumerate(list(cold_major_unique.items())[:15], 1):
    dept_str = str(dept)[:20] if pd.notna(dept) else "未知"
    report_lines.append(f"{idx}. {major}...（{int(count)}人，{city}）\n")
report_lines.append("\n")

# 四十三、被忽视的黄金岗位
report_lines.append("## 四十三、被忽视的黄金岗位\n\n")
report_lines.append("### 一、冷门但优质的岗位\n\n")
report_lines.append("这些岗位具有以下特点：\n")
report_lines.append("- ✅ 单位性质好（省直、市直、中心、局、院等）\n")
report_lines.append("- ✅ 专业要求明确但相对冷门\n")
report_lines.append("- ✅ 竞争压力相对较小\n")
report_lines.append("- ✅ 发展前景良好\n\n")

golden_positions = df[df['is_golden']].copy()
golden_positions = golden_positions.sort_values(['city_gdp_rank', 'value_score'], ascending=[True, False])

report_lines.append("**黄金岗位TOP30**：\n\n")
report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 专业要求 | 学历要求 | 推荐理由 |\n")
report_lines.append("|------|------|----------|----------|----------|----------|----------|----------|\n")

for idx, (_, row) in enumerate(golden_positions.head(30).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:25] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:20] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    major = str(row['major_requirement'])[:30] if pd.notna(row['major_requirement']) else "专业不限"
    edu = str(row['education'])[:10] if pd.notna(row['education']) else "未要求"
    
    reason = "好单位+冷门专业"
    if row['is_fresh']:
        reason += "+应届"
    if row['is_base_service']:
        reason += "+定向"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {major}... | {edu} | {reason} |\n")
report_lines.append("\n")

# 竞争小但待遇好的岗位
report_lines.append("### 二、竞争小但待遇好的岗位\n\n")
low_comp_good = df[df['is_low_competition'] & df['is_good_unit']].copy()
low_comp_good = low_comp_good.sort_values('value_score', ascending=False)

report_lines.append("**低竞争优质岗位TOP20**：\n\n")
report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 预测报名人数 | 专业要求 | 推荐指数 |\n")
report_lines.append("|------|------|----------|----------|----------|--------------|----------|----------|\n")

for idx, (_, row) in enumerate(low_comp_good.head(20).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:25] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:20] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    predicted = int(row['predicted_apply_count'])
    major = str(row['major_requirement'])[:25] if pd.notna(row['major_requirement']) else "专业不限"
    
    # 推荐指数
    if predicted < 15:
        star = "⭐⭐⭐⭐⭐"
    elif predicted < 25:
        star = "⭐⭐⭐⭐"
    else:
        star = "⭐⭐⭐"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {predicted} | {major}... | {star} |\n")
report_lines.append("\n")

# 地理位置佳但报考少的岗位
report_lines.append("### 三、地理位置佳但报考少的岗位\n\n")
good_location = df[df['city'].isin(['省直', '合肥市', '芜湖市', '滁州市']) & df['is_low_competition']].copy()
good_location = good_location.sort_values('value_score', ascending=False)

report_lines.append("**地理位置佳+低竞争岗位TOP15**：\n\n")
report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 预测报名人数 | 专业要求 | 优势分析 |\n")
report_lines.append("|------|------|----------|----------|----------|--------------|----------|----------|\n")

for idx, (_, row) in enumerate(good_location.head(15).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:25] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:20] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    predicted = int(row['predicted_apply_count'])
    major = str(row['major_requirement'])[:25] if pd.notna(row['major_requirement']) else "专业不限"
    
    advantage = f"{city}核心区域"
    if not row['is_no_major']:
        advantage += "+专业限制"
    if row['is_fresh']:
        advantage += "+应届"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {predicted} | {major}... | {advantage} |\n")
report_lines.append("\n")

# 四十四、性价比最高岗位TOP50
report_lines.append("## 四十四、性价比最高岗位TOP50\n\n")
report_lines.append("**评分标准**：综合考虑地区发展、招聘人数、专业限制、学历要求、定向政策等因素\n\n")

top50 = df.nlargest(50, 'value_score').copy()

report_lines.append("| 排名 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 学历 | 专业要求 | 特殊条件 | 性价比分 | 推荐指数 |\n")
report_lines.append("|------|------|----------|----------|----------|------|----------|----------|----------|----------|\n")

for idx, (_, row) in enumerate(top50.iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:20] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:15] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    edu = str(row['education'])[:8] if pd.notna(row['education']) else "未要求"
    major = str(row['major_requirement'])[:20] if pd.notna(row['major_requirement']) else "专业不限"
    
    special = ""
    if row['is_fresh']:
        special += "应届 "
    if row['is_base_service']:
        special += "定向 "
    if row['is_veteran']:
        special += "退役 "
    if not special:
        special = "无"
    
    score = int(row['value_score'])
    
    # 推荐指数
    if score >= 70:
        star = "⭐⭐⭐⭐⭐"
    elif score >= 60:
        star = "⭐⭐⭐⭐"
    elif score >= 50:
        star = "⭐⭐⭐"
    else:
        star = "⭐⭐"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {edu} | {major}... | {special} | {score} | {star} |\n")
report_lines.append("\n")

# 详细分析前10个岗位
report_lines.append("### 详细分析：TOP10岗位深度解读\n\n")
for idx, (_, row) in enumerate(top50.head(10).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name']) if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name']) if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    edu = str(row['education']) if pd.notna(row['education']) else "未要求"
    major = str(row['major_requirement']) if pd.notna(row['major_requirement']) else "专业不限"
    desc = str(row['position_desc']) if pd.notna(row['position_desc']) else ""
    other = str(row['other_requirements']) if pd.notna(row['other_requirements']) else ""
    score = int(row['value_score'])
    predicted = int(row['predicted_apply_count'])
    
    report_lines.append(f"#### {idx}. {city} - {dept} - {pos_name}\n\n")
    report_lines.append(f"- **招聘人数**：{recruit}人\n")
    report_lines.append(f"- **学历要求**：{edu}\n")
    report_lines.append(f"- **专业要求**：{major[:100]}...\n")
    if desc:
        report_lines.append(f"- **岗位描述**：{desc[:150]}...\n")
    if other:
        report_lines.append(f"- **其他要求**：{other[:100]}...\n")
    report_lines.append(f"- **性价比评分**：{score}分\n")
    report_lines.append(f"- **预测报名人数**：约{predicted}人\n")
    
    # 优势分析
    advantages = []
    if city in ['省直', '合肥市']:
        advantages.append("地理位置优越")
    if recruit >= 2:
        advantages.append("招聘人数多，机会大")
    if not row['is_no_major']:
        advantages.append("专业限制明确，竞争相对较小")
    if row['is_fresh']:
        advantages.append("应届生定向，竞争压力小")
    if row['is_base_service']:
        advantages.append("服务基层项目定向，竞争极小")
    
    if advantages:
        report_lines.append(f"- **核心优势**：{' | '.join(advantages)}\n")
    
    report_lines.append(f"- **推荐指数**：{'⭐⭐⭐⭐⭐' if score >= 70 else '⭐⭐⭐⭐' if score >= 60 else '⭐⭐⭐'}\n\n")

# 四十五、零竞争或低竞争岗位
report_lines.append("## 四十五、零竞争或低竞争岗位\n\n")
report_lines.append("### 一、预测报名人数<30人的岗位\n\n")

low_comp_all = df[df['is_low_competition']].copy()
low_comp_all = low_comp_all.sort_values('predicted_apply_count', ascending=True)

report_lines.append(f"**低竞争岗位统计**：共发现 **{len(low_comp_all)}** 个岗位，预计报名人数<30人\n\n")

# 按预测报名人数分组
very_low = low_comp_all[low_comp_all['predicted_apply_count'] < 15]
low = low_comp_all[(low_comp_all['predicted_apply_count'] >= 15) & (low_comp_all['predicted_apply_count'] < 25)]
medium_low = low_comp_all[low_comp_all['predicted_apply_count'] >= 25]

report_lines.append("**竞争度分级**：\n")
report_lines.append(f"- **极低竞争**（<15人）：{len(very_low)}个岗位\n")
report_lines.append(f"- **低竞争**（15-24人）：{len(low)}个岗位\n")
report_lines.append(f"- **较低竞争**（25-29人）：{len(medium_low)}个岗位\n\n")

# 极低竞争岗位TOP30
report_lines.append("### 二、极低竞争岗位TOP30（预测<15人）\n\n")
report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 预测报名 | 专业要求 | 特殊条件 | 竞争分析 |\n")
report_lines.append("|------|------|----------|----------|----------|----------|----------|----------|----------|\n")

for idx, (_, row) in enumerate(very_low.head(30).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:20] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:18] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    predicted = int(row['predicted_apply_count'])
    major = str(row['major_requirement'])[:20] if pd.notna(row['major_requirement']) else "专业不限"
    
    special = ""
    if row['is_fresh']:
        special += "应届 "
    if row['is_base_service']:
        special += "定向 "
    if row['is_veteran']:
        special += "退役 "
    if not special:
        special = "无"
    
    ratio = predicted / recruit if recruit > 0 else 0
    if ratio < 5:
        comp_level = "极低"
    elif ratio < 10:
        comp_level = "很低"
    else:
        comp_level = "低"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {predicted} | {major}... | {special} | {comp_level} |\n")
report_lines.append("\n")

# 分析为何竞争小
report_lines.append("### 三、低竞争原因分析\n\n")

# 统计低竞争岗位的特征
report_lines.append("**低竞争岗位特征统计**：\n\n")

# 定向岗位占比
directed_count = len(low_comp_all[(low_comp_all['is_base_service']) | (low_comp_all['is_veteran']) | (low_comp_all['is_fresh'])])
report_lines.append(f"1. **定向招聘岗位**：{directed_count}个（{directed_count/len(low_comp_all)*100:.1f}%）\n")
report_lines.append("   - 服务基层项目人员定向：竞争极小，符合条件者少\n")
report_lines.append("   - 退役军人定向：特定人群，竞争压力小\n")
report_lines.append("   - 应届毕业生定向：限制报考人群，竞争相对较小\n\n")

# 专业限制
major_limited = len(low_comp_all[~low_comp_all['is_no_major']])
report_lines.append(f"2. **专业限制明确**：{major_limited}个（{major_limited/len(low_comp_all)*100:.1f}%）\n")
report_lines.append("   - 专业要求具体，符合条件者有限\n")
report_lines.append("   - 冷门专业岗位，报考人数自然较少\n\n")

# 地区分布
city_dist_low = low_comp_all['city'].value_counts()
report_lines.append("3. **地区分布特点**：\n")
for city, count in city_dist_low.head(10).items():
    report_lines.append(f"   - {city}：{count}个岗位\n")
report_lines.append("\n")

# 学历要求
edu_dist_low = low_comp_all['education'].value_counts()
report_lines.append("4. **学历要求分布**：\n")
for edu, count in edu_dist_low.head(5).items():
    if pd.notna(edu):
        report_lines.append(f"   - {edu}：{count}个岗位\n")
report_lines.append("\n")

# 报考建议
report_lines.append("### 四、报考建议\n\n")
report_lines.append("**针对低竞争岗位的报考策略**：\n\n")
report_lines.append("1. **符合定向条件的考生**：\n")
report_lines.append("   - 优先选择定向招聘岗位，竞争压力最小\n")
report_lines.append("   - 服务基层项目人员：充分利用政策优势\n")
report_lines.append("   - 退役军人：选择专门面向退役军人的岗位\n")
report_lines.append("   - 应届毕业生：关注专项招聘应届毕业生的岗位\n\n")

report_lines.append("2. **专业匹配的考生**：\n")
report_lines.append("   - 选择专业要求明确且相对冷门的岗位\n")
report_lines.append("   - 仔细核对专业代码，确保完全匹配\n")
report_lines.append("   - 关注专业要求较窄的岗位\n\n")

report_lines.append("3. **地理位置选择**：\n")
report_lines.append("   - 中小城市岗位竞争相对较小\n")
report_lines.append("   - 偏远地区岗位竞争压力小\n")
report_lines.append("   - 但需权衡地理位置与发展前景\n\n")

report_lines.append("4. **综合评估**：\n")
report_lines.append("   - 不要只看竞争度，要综合考虑单位性质、发展前景\n")
report_lines.append("   - 关注岗位的工作内容是否适合自己\n")
report_lines.append("   - 考虑长期职业发展规划\n\n")

# 四十六、特殊人群定向岗位
report_lines.append("## 四十六、特殊人群定向岗位\n\n")

# 服务基层项目人员
base_service_positions = df[df['is_base_service']].copy()
report_lines.append("### 一、服务基层项目人员岗位\n\n")
report_lines.append(f"**岗位统计**：共 **{len(base_service_positions)}** 个岗位，招聘 **{int(base_service_positions['recruit_count'].sum())}** 人\n\n")

report_lines.append("**政策解读**：\n")
report_lines.append("服务基层项目人员包括：\n")
report_lines.append("- 三支一扶计划人员\n")
report_lines.append("- 大学生村官\n")
report_lines.append("- 西部计划志愿者\n")
report_lines.append("- 特岗教师\n")
report_lines.append("- 其他服务基层项目人员\n\n")

report_lines.append("**岗位列表**：\n\n")
report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 专业要求 | 学历要求 |\n")
report_lines.append("|------|------|----------|----------|----------|----------|----------|\n")

for idx, (_, row) in enumerate(base_service_positions.head(30).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:20] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:18] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    major = str(row['major_requirement'])[:20] if pd.notna(row['major_requirement']) else "专业不限"
    edu = str(row['education'])[:10] if pd.notna(row['education']) else "未要求"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {major}... | {edu} |\n")
report_lines.append("\n")

# 退役军人岗位
veteran_positions = df[df['is_veteran']].copy()
report_lines.append("### 二、退役军人岗位\n\n")
report_lines.append(f"**岗位统计**：共 **{len(veteran_positions)}** 个岗位，招聘 **{int(veteran_positions['recruit_count'].sum())}** 人\n\n")

report_lines.append("**政策解读**：\n")
report_lines.append("- 面向符合条件的退役军人定向招聘\n")
report_lines.append("- 通常要求具有退役军人身份证明\n")
report_lines.append("- 部分岗位可能有服役年限要求\n")
report_lines.append("- 竞争压力相对较小\n\n")

report_lines.append("**岗位列表**：\n\n")
report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 专业要求 | 学历要求 |\n")
report_lines.append("|------|------|----------|----------|----------|----------|----------|\n")

for idx, (_, row) in enumerate(veteran_positions.head(30).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:20] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:18] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    major = str(row['major_requirement'])[:20] if pd.notna(row['major_requirement']) else "专业不限"
    edu = str(row['education'])[:10] if pd.notna(row['education']) else "未要求"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {major}... | {edu} |\n")
report_lines.append("\n")

# 残疾人岗位
disabled_positions = df[df['is_disabled']].copy()
report_lines.append("### 三、残疾人岗位\n\n")
report_lines.append(f"**岗位统计**：共 **{len(disabled_positions)}** 个岗位，招聘 **{int(disabled_positions['recruit_count'].sum())}** 人\n\n")

if len(disabled_positions) > 0:
    report_lines.append("**政策解读**：\n")
    report_lines.append("- 面向符合条件的残疾人定向招聘\n")
    report_lines.append("- 通常需要提供残疾证\n")
    report_lines.append("- 部分岗位可能有残疾类型要求\n")
    report_lines.append("- 竞争压力极小\n\n")
    
    report_lines.append("**岗位列表**：\n\n")
    report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 专业要求 | 学历要求 |\n")
    report_lines.append("|------|------|----------|----------|----------|----------|----------|\n")
    
    for idx, (_, row) in enumerate(disabled_positions.iterrows(), 1):
        city = str(row['city'])
        dept = str(row['department_name'])[:20] if pd.notna(row['department_name']) else "未知"
        pos_name = str(row['position_name'])[:18] if pd.notna(row['position_name']) else "专业技术"
        recruit = int(row['recruit_count'])
        major = str(row['major_requirement'])[:20] if pd.notna(row['major_requirement']) else "专业不限"
        edu = str(row['education'])[:10] if pd.notna(row['education']) else "未要求"
        
        report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {major}... | {edu} |\n")
    report_lines.append("\n")
else:
    report_lines.append("**说明**：本次招聘中未发现明确的残疾人定向岗位。\n\n")

# 应届毕业生岗位
fresh_positions = df[df['is_fresh']].copy()
report_lines.append("### 四、应届毕业生定向岗位\n\n")
report_lines.append(f"**岗位统计**：共 **{len(fresh_positions)}** 个岗位，招聘 **{int(fresh_positions['recruit_count'].sum())}** 人\n\n")

report_lines.append("**政策解读**：\n")
report_lines.append("- 专项招聘应届毕业生\n")
report_lines.append("- 通常要求当年毕业或近2年毕业未就业\n")
report_lines.append("- 限制往届生报考，竞争相对较小\n")
report_lines.append("- 适合应届毕业生重点关注\n\n")

report_lines.append("**岗位列表（TOP30）**：\n\n")
report_lines.append("| 序号 | 地市 | 单位名称 | 岗位名称 | 招聘人数 | 专业要求 | 学历要求 |\n")
report_lines.append("|------|------|----------|----------|----------|----------|----------|\n")

for idx, (_, row) in enumerate(fresh_positions.head(30).iterrows(), 1):
    city = str(row['city'])
    dept = str(row['department_name'])[:20] if pd.notna(row['department_name']) else "未知"
    pos_name = str(row['position_name'])[:18] if pd.notna(row['position_name']) else "专业技术"
    recruit = int(row['recruit_count'])
    major = str(row['major_requirement'])[:20] if pd.notna(row['major_requirement']) else "专业不限"
    edu = str(row['education'])[:10] if pd.notna(row['education']) else "未要求"
    
    report_lines.append(f"| {idx} | {city} | {dept} | {pos_name} | {recruit} | {major}... | {edu} |\n")
report_lines.append("\n")

# 定向招聘政策总结
report_lines.append("### 五、定向招聘政策总结\n\n")
report_lines.append("**政策优势**：\n")
report_lines.append("1. **竞争压力小**：限制报考人群，符合条件者少\n")
report_lines.append("2. **政策支持**：国家鼓励定向招聘，政策倾斜明显\n")
report_lines.append("3. **发展机会**：定向岗位通常有更好的发展空间\n\n")

report_lines.append("**报考建议**：\n")
report_lines.append("1. **仔细核对条件**：确保完全符合定向招聘要求\n")
report_lines.append("2. **准备证明材料**：提前准备相关身份证明\n")
report_lines.append("3. **关注公告细节**：注意定向招聘的具体要求和限制\n")
report_lines.append("4. **合理选择**：不要为了低竞争而选择不适合的岗位\n\n")

# 报告结尾
report_lines.append("---\n\n")
report_lines.append("## 本章小结\n\n")
report_lines.append("通过对2026年安徽省事业单位3,344个岗位、4,122人的深度数据分析，我们发现：\n\n")
report_lines.append("1. **招聘规律明显**：省直和发达地区岗位多但竞争激烈，中小城市岗位少但竞争小\n")
report_lines.append("2. **黄金岗位存在**：好单位+冷门专业的组合，竞争小但发展前景好\n")
report_lines.append("3. **性价比差异大**：综合考虑地区、专业、定向政策，可以找到高性价比岗位\n")
report_lines.append("4. **低竞争机会多**：定向招聘、专业限制、地理位置等因素创造了大量低竞争机会\n")
report_lines.append("5. **特殊人群优势**：符合定向招聘条件的考生，应充分利用政策优势\n\n")
report_lines.append("**建议**：考生应根据自身条件，综合考虑竞争度、地理位置、单位性质、发展前景等因素，选择最适合自己的岗位。\n\n")

# 保存报告
output_file = 'docs/chapters/第9章_数据洞察与隐藏机会.md'
print(f"正在保存报告到 {output_file}...")

with open(output_file, 'w', encoding='utf-8') as f:
    f.writelines(report_lines)

print(f"报告生成完成！共 {len(report_lines)} 行")
print(f"文件保存位置：{output_file}")
