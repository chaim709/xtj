#!/usr/bin/env python3
"""
修复池州市和歙县两个特殊格式的Excel文件
"""
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from field_mapper import FieldMapper
from data_normalizer import DataNormalizer
from data_validator import DataValidator
from app import create_app, db
from app.models.position import Position


def process_chizhou_file():
    """处理池州市文件（特殊格式）"""
    print("="*80)
    print("处理池州市文件")
    print("="*80)
    
    file_path = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/池州岗位表/2026年池州市市直事业单位公开招聘工作人员岗位计划表.xls"
    
    # 读取原始数据
    df_raw = pd.read_excel(file_path, header=None)
    
    # 池州市文件的表头分两行：行2和行4
    # 行2: 序号、主管部门、用人单位、招聘人数、招聘岗位、岗位代码、公共科目...
    # 行4: （空）、（空）、（空）、（空）、（空）、（空）、学历、学位、专业、年龄、其他条件...
    
    # 合并行2和行4的列名
    header1 = df_raw.iloc[2].values
    header2 = df_raw.iloc[4].values
    
    # 创建新列名
    new_columns = []
    for i in range(len(header1)):
        h1 = str(header1[i]) if pd.notna(header1[i]) and str(header1[i]) != 'nan' else ''
        h2 = str(header2[i]) if pd.notna(header2[i]) and str(header2[i]) != 'nan' else ''
        
        if h1 and h2:
            new_columns.append(f"{h1}_{h2}")
        elif h1:
            new_columns.append(h1)
        elif h2:
            new_columns.append(h2)
        else:
            new_columns.append(f"Unnamed_{i}")
    
    print(f"  合并后的列名: {new_columns}")
    
    # 从行5开始读取数据
    df_data = df_raw.iloc[5:].copy()
    df_data.columns = new_columns[:len(df_data.columns)]
    df_data = df_data.reset_index(drop=True)
    
    # 移除空行
    df_data = df_data.dropna(how='all')
    
    print(f"  数据行数: {len(df_data)}")
    
    # 手动映射字段
    result_df = pd.DataFrame()
    
    result_df['year'] = 2026
    result_df['exam_type'] = '事业单位'
    result_df['city'] = '池州市'
    result_df['affiliation'] = '市'
    result_df['region_name'] = None
    
    # 查找各字段
    for col in df_data.columns:
        col_lower = col.lower()
        if '用人单位' in col or '招聘单位' in col:
            result_df['department_name'] = df_data[col]
        elif '岗位名称' in col or ('招聘岗位' in col and '岗位代码' not in col):
            result_df['position_name'] = df_data[col]
        elif '岗位代码' in col:
            result_df['position_code'] = df_data[col]
        elif '招聘人数' in col or '人数' in col:
            result_df['recruit_count'] = df_data[col].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 1)
        elif col == '学历' or '学历' in col:
            result_df['education'] = df_data[col]
        elif col == '专业' or ('专业' in col and '公共' not in col):
            result_df['major_requirement'] = df_data[col]
        elif '公共科目' in col or '考试类别' in col:
            result_df['exam_category'] = df_data[col]
        elif '年龄' in col:
            result_df['age'] = df_data[col]
        elif '其他' in col:
            result_df['other_requirements'] = df_data[col]
    
    # 填充缺失字段
    if 'department_name' not in result_df.columns or result_df['department_name'].isna().all():
        result_df['department_name'] = None
    if 'position_name' not in result_df.columns:
        result_df['position_name'] = None
    if 'position_code' not in result_df.columns:
        result_df['position_code'] = None
    if 'recruit_count' not in result_df.columns:
        result_df['recruit_count'] = 1
    if 'education' not in result_df.columns:
        result_df['education'] = None
    if 'major_requirement' not in result_df.columns:
        result_df['major_requirement'] = None
    if 'exam_category' not in result_df.columns:
        result_df['exam_category'] = None
    
    # 标准化学历
    result_df['education'] = result_df['education'].apply(
        lambda x: '本科及以上' if pd.notna(x) and '本科' in str(x) else str(x) if pd.notna(x) else None
    )
    
    # 标准化考试类别
    result_df['exam_category'] = result_df['exam_category'].apply(
        lambda x: '综合管理类(A类)' if pd.notna(x) and ('A' in str(x) or '11' in str(x) or '综合' in str(x)) else str(x) if pd.notna(x) else '综合管理类(A类)'
    )
    
    # 合并其他条件
    if 'age' in result_df.columns and 'other_requirements' in result_df.columns:
        result_df['other_requirements'] = result_df.apply(
            lambda row: '；'.join([str(v) for v in [row.get('age'), row.get('other_requirements')] if pd.notna(v)]) or None,
            axis=1
        )
    
    # 添加其他必需字段
    result_df['system_type'] = None
    result_df['department_code'] = None
    result_df['position_desc'] = None
    result_df['open_ratio'] = 3
    result_df['apply_count'] = None
    result_df['competition_ratio'] = None
    result_df['min_entry_score'] = None
    result_df['max_entry_score'] = None
    result_df['max_xingce_score'] = None
    result_df['max_shenlun_score'] = None
    result_df['max_police_score'] = None
    result_df['min_police_score'] = None
    
    # 验证数据
    validator = DataValidator()
    validation = validator.validate_dataframe(result_df)
    
    print(f"\n✓ 处理完成")
    print(f"  总行数: {len(result_df)}")
    print(f"  有效行: {validation['valid']}")
    print(f"  无效行: {validation['invalid']}")
    print(f"  招聘人数: {result_df['recruit_count'].sum()}")
    
    return validator.get_valid_rows(result_df)


def process_shexian_file():
    """处理歙县文件（多行表头）"""
    print("\n" + "="*80)
    print("处理歙县文件")
    print("="*80)
    
    file_path = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/黄山市岗位表/2026年度歙县事业单位统一公开招聘岗位汇总表.xls"
    
    # 读取原始数据
    df_raw = pd.read_excel(file_path, header=None)
    
    # 行2和行3是表头
    header1 = df_raw.iloc[2].values  # 序号、主管部门、招聘单位、岗位名称、岗位代码、聘用人数...
    header2 = df_raw.iloc[3].values  # （空）、（空）、（空）、（空）、（空）、（空）、专业、学历...
    
    # 合并表头
    new_columns = []
    for i in range(len(header1)):
        h1 = str(header1[i]) if pd.notna(header1[i]) and str(header1[i]) != 'nan' else ''
        h2 = str(header2[i]) if i < len(header2) and pd.notna(header2[i]) and str(header2[i]) != 'nan' else ''
        
        # 清理换行符
        h1 = h1.replace('\n', '').strip()
        h2 = h2.replace('\n', '').strip()
        
        if h1 and h2:
            new_columns.append(f"{h1}_{h2}")
        elif h1:
            new_columns.append(h1)
        elif h2:
            new_columns.append(h2)
        else:
            new_columns.append(f"Col_{i}")
    
    print(f"  合并后的列名: {new_columns[:10]}")
    
    # 从行4开始读取数据
    df_data = df_raw.iloc[4:].copy()
    df_data.columns = new_columns[:len(df_data.columns)]
    df_data = df_data.reset_index(drop=True)
    df_data = df_data.dropna(how='all')
    
    print(f"  数据行数: {len(df_data)}")
    
    # 手动映射字段
    result_df = pd.DataFrame()
    
    result_df['year'] = 2026
    result_df['exam_type'] = '事业单位'
    result_df['city'] = '黄山市'
    result_df['affiliation'] = '市'
    result_df['region_name'] = '歙县'
    
    # 映射各字段
    for col in df_data.columns:
        if '招聘单位' in col:
            result_df['department_name'] = df_data[col]
        elif '岗位名称' in col:
            result_df['position_name'] = df_data[col]
        elif '岗位代码' in col:
            result_df['position_code'] = df_data[col]
        elif '聘用人数' in col or '人数' in col:
            result_df['recruit_count'] = df_data[col].apply(lambda x: int(x) if pd.notna(x) and str(x).replace('.','').isdigit() else 1)
        elif col == '学历' or '学历' in col:
            result_df['education'] = df_data[col]
        elif col == '专业' or ('专业' in col and '公共' not in col):
            result_df['major_requirement'] = df_data[col]
        elif '笔试科目' in col:
            result_df['exam_category'] = df_data[col]
        elif '年龄' in col:
            result_df['age'] = df_data[col]
        elif '其他' in col:
            result_df['other_requirements'] = df_data[col]
    
    # 处理合并单元格
    if 'department_name' in result_df.columns:
        result_df['department_name'] = result_df['department_name'].ffill()
    
    # 标准化
    if 'education' in result_df.columns:
        result_df['education'] = result_df['education'].apply(
            lambda x: '本科及以上' if pd.notna(x) and '本科' in str(x) else 
                     '研究生及以上' if pd.notna(x) and '研究生' in str(x) else 
                     str(x) if pd.notna(x) else None
        )
    
    if 'exam_category' in result_df.columns:
        result_df['exam_category'] = result_df['exam_category'].apply(
            lambda x: '综合管理类(A类)' if pd.notna(x) and 'A' in str(x) else
                     '社会科学专技类(B类)' if pd.notna(x) and 'B' in str(x) else
                     '自然科学专技类(C类)' if pd.notna(x) and 'C' in str(x) else
                     '综合管理类(A类)'  # 默认
        )
    
    # 合并其他条件
    if 'age' in result_df.columns:
        result_df['other_requirements'] = result_df.apply(
            lambda row: '；'.join([str(v) for v in [row.get('age'), row.get('other_requirements')] if pd.notna(v)]) or None,
            axis=1
        )
    
    # 添加其他必需字段
    result_df['system_type'] = None
    result_df['department_code'] = None
    result_df['position_desc'] = None
    result_df['open_ratio'] = 3
    result_df['apply_count'] = None
    result_df['competition_ratio'] = None
    result_df['min_entry_score'] = None
    result_df['max_entry_score'] = None
    result_df['max_xingce_score'] = None
    result_df['max_shenlun_score'] = None
    result_df['max_police_score'] = None
    result_df['min_police_score'] = None
    
    # 验证
    validator = DataValidator()
    validation = validator.validate_dataframe(result_df)
    
    print(f"\n✓ 池州市处理完成")
    print(f"  总行数: {len(result_df)}")
    print(f"  有效行: {validation['valid']}")
    print(f"  招聘人数: {result_df['recruit_count'].sum()}")
    
    return validator.get_valid_rows(result_df)


def process_shexian_file():
    """处理歙县文件（多行表头）"""
    print("\n" + "="*80)
    print("处理歙县文件")
    print("="*80)
    
    file_path = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/黄山市岗位表/2026年度歙县事业单位统一公开招聘岗位汇总表.xls"
    
    # 使用行2作为表头，但实际数据从行4开始
    df_raw = pd.read_excel(file_path, header=None)
    
    # 行2和行3是表头
    header1 = df_raw.iloc[2].values
    header2 = df_raw.iloc[3].values
    
    # 合并列名
    new_columns = []
    for i in range(len(header1)):
        h1 = str(header1[i]).replace('\n', '').strip() if pd.notna(header1[i]) else ''
        h2 = str(header2[i]).replace('\n', '').strip() if i < len(header2) and pd.notna(header2[i]) else ''
        
        if h1 and h2 and h1 != 'nan' and h2 != 'nan':
            new_columns.append(f"{h1}_{h2}")
        elif h1 and h1 != 'nan':
            new_columns.append(h1)
        elif h2 and h2 != 'nan':
            new_columns.append(h2)
        else:
            new_columns.append(f"Col_{i}")
    
    print(f"  合并后的列名: {new_columns[:10]}")
    
    # 从行4开始读取数据
    df_data = df_raw.iloc[4:].copy()
    df_data.columns = new_columns[:len(df_data.columns)]
    df_data = df_data.reset_index(drop=True)
    df_data = df_data.dropna(how='all')
    
    print(f"  数据行数: {len(df_data)}")
    
    # 手动映射
    result_df = pd.DataFrame()
    
    result_df['year'] = 2026
    result_df['exam_type'] = '事业单位'
    result_df['city'] = '黄山市'
    result_df['affiliation'] = '市'
    result_df['region_name'] = '歙县'
    
    # 映射字段
    for col in df_data.columns:
        if '招聘单位' in col:
            result_df['department_name'] = df_data[col].ffill()  # 向下填充合并单元格
        elif '岗位名称' in col:
            result_df['position_name'] = df_data[col]
        elif '岗位代码' in col:
            result_df['position_code'] = df_data[col]
        elif '聘用人数' in col:
            result_df['recruit_count'] = df_data[col].apply(lambda x: int(float(x)) if pd.notna(x) else 1)
        elif col == '学历' or (col.endswith('学历') and '招聘' not in col):
            result_df['education'] = df_data[col]
        elif col == '专业' or (col.endswith('专业') and '公共' not in col):
            result_df['major_requirement'] = df_data[col]
        elif '笔试科目' in col:
            result_df['exam_category'] = df_data[col]
        elif '年龄' in col:
            result_df['age'] = df_data[col]
        elif '其他' in col:
            result_df['other_requirements'] = df_data[col]
    
    # 标准化
    if 'education' in result_df.columns:
        result_df['education'] = result_df['education'].apply(
            lambda x: '本科及以上' if pd.notna(x) and '本科' in str(x) else 
                     '研究生及以上' if pd.notna(x) and '研究生' in str(x) else 
                     str(x) if pd.notna(x) else None
        )
    
    if 'exam_category' in result_df.columns:
        result_df['exam_category'] = result_df['exam_category'].apply(
            lambda x: '综合管理类(A类)' if pd.notna(x) and 'A' in str(x) else
                     '社会科学专技类(B类)' if pd.notna(x) and 'B' in str(x) else
                     '综合管理类(A类)'
        )
    
    # 合并其他条件
    if 'age' in result_df.columns:
        result_df['other_requirements'] = result_df.apply(
            lambda row: '；'.join([str(v) for v in [row.get('age'), row.get('other_requirements')] if pd.notna(v)]) or None,
            axis=1
        )
    
    # 添加其他必需字段
    for field in ['system_type', 'department_code', 'position_desc', 'apply_count', 
                  'competition_ratio', 'min_entry_score', 'max_entry_score',
                  'max_xingce_score', 'max_shenlun_score', 'max_police_score', 'min_police_score']:
        if field not in result_df.columns:
            result_df[field] = None
    
    if 'open_ratio' not in result_df.columns:
        result_df['open_ratio'] = 3
    
    # 验证
    validator = DataValidator()
    validation = validator.validate_dataframe(result_df)
    
    print(f"\n✓ 歙县处理完成")
    print(f"  总行数: {len(result_df)}")
    print(f"  有效行: {validation['valid']}")
    print(f"  招聘人数: {result_df['recruit_count'].sum()}")
    
    return validator.get_valid_rows(result_df)


def import_to_database(chizhou_df, shexian_df):
    """导入到数据库"""
    print("\n" + "="*80)
    print("导入到数据库")
    print("="*80)
    
    app = create_app()
    with app.app_context():
        # 合并两个DataFrame
        combined_df = pd.concat([chizhou_df, shexian_df], ignore_index=True)
        
        print(f"\n合并数据:")
        print(f"  池州市: {len(chizhou_df)} 行, {chizhou_df['recruit_count'].sum()} 人")
        print(f"  歙县: {len(shexian_df)} 行, {shexian_df['recruit_count'].sum()} 人")
        print(f"  总计: {len(combined_df)} 行, {combined_df['recruit_count'].sum()} 人")
        
        # 转换为字典
        records = combined_df.to_dict('records')
        
        # 处理NaN
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        # 导入
        try:
            db.session.bulk_insert_mappings(Position, records)
            db.session.commit()
            
            print(f"\n✓ 导入成功！")
            
            # 验证
            total = Position.query.filter(
                Position.year == 2026,
                Position.exam_type == '事业单位'
            ).count()
            
            print(f"  数据库总记录: {total}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ 导入失败: {str(e)}")
            raise


if __name__ == '__main__':
    try:
        # 处理两个文件
        chizhou_df = process_chizhou_file()
        shexian_df = process_shexian_file()
        
        # 导入数据库
        import_to_database(chizhou_df, shexian_df)
        
        print("\n" + "="*80)
        print("✓ 全部完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
