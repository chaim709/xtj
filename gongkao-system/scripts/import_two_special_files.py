#!/usr/bin/env python3
"""
直接导入池州市和歙县两个文件
"""
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.position import Position


def import_chizhou():
    """导入池州市数据"""
    print("="*70)
    print("导入池州市数据")
    print("="*70)
    
    file = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/池州岗位表/2026年池州市市直事业单位公开招聘工作人员岗位计划表.xls"
    
    # 读取原始数据，行5开始是数据
    df_raw = pd.read_excel(file, header=None)
    
    # 设置列名（根据行2和行4）
    df_data = df_raw.iloc[5:, :14].copy()  # 从行5开始，取前14列
    df_data.columns = ['序号', '主管部门', '用人单位', '招聘人数', '招聘岗位', '岗位代码', 
                       '学历', '学位', '专业', '年龄', '其他条件', '公共科目类别', '岗位描述', '备注']
    
    df_data = df_data.dropna(how='all').reset_index(drop=True)
    
    print(f"  读取数据: {len(df_data)} 行")
    
    # 转换为Position记录
    records = []
    
    for idx, row in df_data.iterrows():
        # 跳过无效数据
        if pd.isna(row['岗位代码']):
            continue
        
        # 向下填充用人单位（处理合并单元格）
        if idx == 0:
            current_dept = row['用人单位']
        else:
            if pd.notna(row['用人单位']):
                current_dept = row['用人单位']
        
        record = {
            'year': 2026,
            'exam_type': '事业单位',
            'city': '池州市',
            'affiliation': '市',
            'region_name': None,
            'system_type': None,
            'department_code': None,
            'department_name': current_dept if pd.notna(current_dept) else None,
            'position_code': str(int(row['岗位代码'])) if pd.notna(row['岗位代码']) else None,
            'position_name': str(row['招聘岗位']) if pd.notna(row['招聘岗位']) else None,
            'position_desc': None,
            'exam_category': '综合管理类(A类)' if pd.isna(row['公共科目类别']) else str(row['公共科目类别']),
            'open_ratio': 3,
            'recruit_count': int(row['招聘人数']) if pd.notna(row['招聘人数']) else 1,
            'education': str(row['学历']) if pd.notna(row['学历']) else None,
            'major_requirement': str(row['专业']) if pd.notna(row['专业']) else None,
            'other_requirements': None,
            'apply_count': None,
            'competition_ratio': None,
            'min_entry_score': None,
            'max_entry_score': None,
            'max_xingce_score': None,
            'max_shenlun_score': None,
            'max_police_score': None,
            'min_police_score': None
        }
        
        # 合并年龄和其他条件
        conditions = []
        if pd.notna(row['年龄']):
            conditions.append(str(row['年龄']))
        if pd.notna(row['其他条件']):
            conditions.append(str(row['其他条件']))
        if pd.notna(row['学位']):
            conditions.append(f"学位：{row['学位']}")
        
        if conditions:
            record['other_requirements'] = '；'.join(conditions)
        
        # 验证必填字段
        if record['department_name'] and record['position_name'] and record['position_code']:
            records.append(record)
    
    print(f"  有效记录: {len(records)} 条")
    print(f"  招聘人数: {sum(r['recruit_count'] for r in records)} 人")
    
    return records


def import_shexian():
    """导入歙县数据"""
    print("\n" + "="*70)
    print("导入歙县数据")
    print("="*70)
    
    file = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/黄山市岗位表/2026年度歙县事业单位统一公开招聘岗位汇总表.xls"
    
    # 读取原始数据，行4开始是数据
    df_raw = pd.read_excel(file, header=None)
    
    # 从行4开始读取数据
    df_data = df_raw.iloc[4:].copy()
    
    # 根据行2和行3的表头设置列名
    # 列0:序号, 列1:主管部门, 列2:招聘单位, 列3:岗位名称, 列4:岗位代码, 列5:聘用人数
    # 列6:专业, 列7:学历, 列8:学位, 列9:年龄, 列10:其他, 列11:笔试科目...
    
    df_data = df_data.dropna(how='all').reset_index(drop=True)
    
    print(f"  读取数据: {len(df_data)} 行")
    
    # 转换为Position记录
    records = []
    current_dept = None
    
    for idx, row in df_data.iterrows():
        # 跳过无效数据
        if pd.isna(row.iloc[4]):  # 岗位代码列
            continue
        
        # 向下填充招聘单位
        if pd.notna(row.iloc[2]):
            current_dept = row.iloc[2]
        
        record = {
            'year': 2026,
            'exam_type': '事业单位',
            'city': '黄山市',
            'affiliation': '市',
            'region_name': '歙县',
            'system_type': None,
            'department_code': None,
            'department_name': current_dept if current_dept else None,
            'position_code': str(int(float(row.iloc[4]))) if pd.notna(row.iloc[4]) else None,
            'position_name': str(row.iloc[3]).replace('\n', '') if pd.notna(row.iloc[3]) else None,
            'position_desc': None,
            'exam_category': str(row.iloc[11]) if len(row) > 11 and pd.notna(row.iloc[11]) else '综合管理类(A类)',
            'open_ratio': 3,
            'recruit_count': int(float(row.iloc[5])) if pd.notna(row.iloc[5]) else 1,
            'education': str(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) else None,
            'major_requirement': str(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else None,
            'other_requirements': None,
            'apply_count': None,
            'competition_ratio': None,
            'min_entry_score': None,
            'max_entry_score': None,
            'max_xingce_score': None,
            'max_shenlun_score': None,
            'max_police_score': None,
            'min_police_score': None
        }
        
        # 合并其他条件
        conditions = []
        if len(row) > 9 and pd.notna(row.iloc[9]):  # 年龄
            conditions.append(str(row.iloc[9]))
        if len(row) > 8 and pd.notna(row.iloc[8]):  # 学位
            conditions.append(f"学位：{row.iloc[8]}")
        if len(row) > 10 and pd.notna(row.iloc[10]):  # 其他
            conditions.append(str(row.iloc[10]))
        
        if conditions:
            record['other_requirements'] = '；'.join(conditions)
        
        # 标准化考试类别
        if 'A' in record['exam_category']:
            record['exam_category'] = '综合管理类(A类)'
        elif 'B' in record['exam_category']:
            record['exam_category'] = '社会科学专技类(B类)'
        elif 'C' in record['exam_category']:
            record['exam_category'] = '自然科学专技类(C类)'
        else:
            record['exam_category'] = '综合管理类(A类)'
        
        # 验证必填字段
        if record['department_name'] and record['position_name']:
            records.append(record)
    
    print(f"  有效记录: {len(records)} 条")
    print(f"  招聘人数: {sum(r['recruit_count'] for r in records)} 人")
    
    return records


def main():
    """主函数"""
    try:
        # 处理两个文件
        chizhou_records = import_chizhou()
        shexian_records = import_shexian()
        
        all_records = chizhou_records + shexian_records
        
        print("\n" + "="*70)
        print("导入到数据库")
        print("="*70)
        
        print(f"\n总计: {len(all_records)} 条记录, {sum(r['recruit_count'] for r in all_records)} 人")
        
        app = create_app()
        with app.app_context():
            # 导入
            db.session.bulk_insert_mappings(Position, all_records)
            db.session.commit()
            
            print(f"✓ 导入成功！")
            
            # 最终验证
            total = Position.query.filter(
                Position.year == 2026,
                Position.exam_type == '事业单位'
            ).count()
            
            chizhou_count = Position.query.filter(
                Position.year == 2026,
                Position.exam_type == '事业单位',
                Position.city == '池州市'
            ).count()
            
            shexian_count = Position.query.filter(
                Position.year == 2026,
                Position.exam_type == '事业单位',
                Position.region_name == '歙县'
            ).count()
            
            total_recruits = db.session.query(
                db.func.sum(Position.recruit_count)
            ).filter(
                Position.year == 2026,
                Position.exam_type == '事业单位'
            ).scalar()
            
            print(f"\n最终数据库统计:")
            print(f"  事业单位总记录: {total} 条")
            print(f"  总招聘人数: {int(total_recruits)} 人")
            print(f"  池州市: {chizhou_count} 条")
            print(f"  歙县: {shexian_count} 条")
            
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
