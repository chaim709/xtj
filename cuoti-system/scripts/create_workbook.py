#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建题册脚本

使用方法:
    python3 scripts/create_workbook.py --name "言语理解专项一" --source "言语理解专项一"
"""
import os
import sys
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_workbook_from_source(name, source, description=None, category='专项练习'):
    """根据题目来源创建题册"""
    from app import create_app, db
    from app.models import Question, Workbook, WorkbookItem, WorkbookPage, WorkbookTemplate
    
    app = create_app('development')
    
    with app.app_context():
        # 查找对应来源的题目
        questions = Question.query.filter(Question.source.like(f'%{source}%')).order_by(Question.id).all()
        
        if not questions:
            print(f"未找到来源包含 '{source}' 的题目")
            return
        
        print(f"找到 {len(questions)} 道题目")
        
        # 检查题册是否已存在
        existing = Workbook.query.filter_by(name=name).first()
        if existing:
            print(f"题册 '{name}' 已存在 (ID: {existing.id})")
            return existing.id
        
        # 获取默认模板
        template = WorkbookTemplate.get_default()
        
        # 创建题册
        workbook = Workbook(
            name=name,
            description=description or f'{name} 专项练习题册',
            category=category,
            template_id=template.id,
            answer_mode='hidden',
            questions_per_page=template.questions_per_page,
            total_questions=len(questions)
        )
        
        db.session.add(workbook)
        db.session.flush()  # 获取ID
        
        # 添加题目到题册
        for i, q in enumerate(questions):
            item = WorkbookItem(
                workbook_id=workbook.id,
                question_id=q.id,
                order=i + 1,
                page_num=(i // template.questions_per_page) + 1
            )
            db.session.add(item)
        
        # 计算总页数
        total_pages = (len(questions) + template.questions_per_page - 1) // template.questions_per_page
        workbook.total_pages = total_pages
        
        # 创建页面记录
        for page_num in range(1, total_pages + 1):
            start_order = (page_num - 1) * template.questions_per_page + 1
            end_order = min(page_num * template.questions_per_page, len(questions))
            
            page = WorkbookPage(
                workbook_id=workbook.id,
                page_num=page_num,
                start_order=start_order,
                end_order=end_order,
                qr_code=f'WB{workbook.id}P{page_num}'
            )
            db.session.add(page)
        
        db.session.commit()
        
        print(f"\n题册创建成功！")
        print(f"  - 名称: {workbook.name}")
        print(f"  - ID: {workbook.id}")
        print(f"  - 题目数: {workbook.total_questions}")
        print(f"  - 页数: {workbook.total_pages}")
        
        return workbook.id


def main():
    parser = argparse.ArgumentParser(description='创建题册工具')
    parser.add_argument('--name', type=str, required=True, help='题册名称')
    parser.add_argument('--source', type=str, required=True, help='题目来源关键词')
    parser.add_argument('--description', type=str, help='题册描述')
    parser.add_argument('--category', type=str, default='专项练习', help='题册分类')
    
    args = parser.parse_args()
    
    create_workbook_from_source(
        name=args.name,
        source=args.source,
        description=args.description,
        category=args.category
    )


if __name__ == '__main__':
    main()
