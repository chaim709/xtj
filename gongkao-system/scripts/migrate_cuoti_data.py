#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从cuoti-system迁移数据到gongkao-system
"""
import sys
import os
import sqlite3
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    Question, Workbook, WorkbookItem, WorkbookPage,
    Institution, WorkbookTemplate
)


def migrate_questions(cuoti_db_path):
    """迁移题目数据"""
    conn = sqlite3.connect(cuoti_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取题目
    cursor.execute("SELECT * FROM questions")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        # 检查是否已存在
        existing = Question.query.filter_by(
            stem=row['stem'][:200]
        ).first()
        
        if not existing:
            question = Question(
                stem=row['stem'],
                option_a=row['option_a'],
                option_b=row['option_b'],
                option_c=row['option_c'],
                option_d=row['option_d'],
                answer=row['answer'],
                analysis=row['analysis'],
                category=row['category'],
                subcategory=row['subcategory'],
                knowledge_point=row['knowledge_point'],
                difficulty=row['difficulty'] or 3,
                source=row['source'],
                is_image_question=bool(row['is_image_question']) if 'is_image_question' in row.keys() else False,
                image_path=row['image_path'] if 'image_path' in row.keys() else None
            )
            db.session.add(question)
            count += 1
    
    db.session.commit()
    conn.close()
    print(f"迁移题目: {count} 条")
    return count


def migrate_workbooks(cuoti_db_path):
    """迁移题册数据"""
    conn = sqlite3.connect(cuoti_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取题册
    cursor.execute("SELECT * FROM workbooks")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        existing = Workbook.query.filter_by(name=row['name']).first()
        
        if not existing:
            workbook = Workbook(
                name=row['name'],
                description=row['description'],
                category=row['category'],
                total_questions=row['total_questions']
            )
            db.session.add(workbook)
            db.session.flush()
            
            # 迁移题册题目
            cursor.execute(
                "SELECT * FROM workbook_items WHERE workbook_id = ? ORDER BY `order`",
                (row['id'],)
            )
            items = cursor.fetchall()
            
            for item in items:
                # 找到对应的新题目
                old_question_id = item['question_id']
                cursor2 = conn.cursor()
                cursor2.execute("SELECT stem FROM questions WHERE id = ?", (old_question_id,))
                q_row = cursor2.fetchone()
                
                if q_row:
                    new_question = Question.query.filter(
                        Question.stem.like(q_row['stem'][:200] + '%')
                    ).first()
                    
                    if new_question:
                        wb_item = WorkbookItem(
                            workbook_id=workbook.id,
                            question_id=new_question.id,
                            order=item['order']
                        )
                        db.session.add(wb_item)
            
            count += 1
    
    db.session.commit()
    conn.close()
    print(f"迁移题册: {count} 本")
    return count


def migrate_institution(cuoti_db_path):
    """迁移机构配置"""
    conn = sqlite3.connect(cuoti_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM institution LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            inst = Institution.get_instance()
            inst.name = row['name'] or inst.name
            inst.slogan = row['slogan']
            inst.phone = row['phone']
            inst.wechat = row['wechat']
            inst.address = row['address']
            inst.website = row['website']
            inst.primary_color = row['primary_color'] or '#1a73e8'
            inst.secondary_color = row['secondary_color'] or '#34a853'
            inst.header_text = row['header_text']
            inst.footer_text = row['footer_text']
            
            db.session.commit()
            print("迁移机构配置: 成功")
    except Exception as e:
        print(f"迁移机构配置失败: {e}")
    
    conn.close()


def migrate_templates(cuoti_db_path):
    """迁移模板配置"""
    conn = sqlite3.connect(cuoti_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM workbook_templates")
        rows = cursor.fetchall()
        
        count = 0
        for row in rows:
            existing = WorkbookTemplate.query.filter_by(name=row['name']).first()
            
            if not existing:
                template = WorkbookTemplate(
                    name=row['name'],
                    answer_mode=row['answer_mode'],
                    questions_per_page=row['questions_per_page'],
                    brand_enabled=bool(row['brand_enabled']),
                    show_cover=bool(row['show_cover']),
                    show_qrcode=bool(row['show_qrcode']),
                    is_default=bool(row['is_default'])
                )
                db.session.add(template)
                count += 1
        
        db.session.commit()
        print(f"迁移模板: {count} 个")
    except Exception as e:
        print(f"迁移模板失败: {e}")
    
    conn.close()


def main():
    # cuoti数据库路径
    cuoti_db_path = '/Users/chaim/CodeBuddy/公考项目/cuoti-system/cuoti_dev.db'
    
    if not os.path.exists(cuoti_db_path):
        print(f"错误: 找不到cuoti数据库: {cuoti_db_path}")
        return
    
    app = create_app('development')
    
    with app.app_context():
        # 创建表
        db.create_all()
        print("数据库表已创建")
        
        # 迁移数据
        print("\n开始迁移数据...")
        migrate_institution(cuoti_db_path)
        migrate_templates(cuoti_db_path)
        migrate_questions(cuoti_db_path)
        migrate_workbooks(cuoti_db_path)
        
        print("\n迁移完成!")
        print(f"- 题目总数: {Question.query.count()}")
        print(f"- 题册总数: {Workbook.query.count()}")
        print(f"- 模板总数: {WorkbookTemplate.query.count()}")


if __name__ == '__main__':
    main()
