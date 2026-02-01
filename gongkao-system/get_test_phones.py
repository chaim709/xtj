#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查询测试用手机号"""
from app import create_app, db
from app.models.student import Student

app = create_app()

with app.app_context():
    students = Student.query.filter(Student.phone.isnot(None)).limit(5).all()
    
    print("=" * 50)
    print("可用的测试手机号:")
    print("=" * 50)
    
    for s in students:
        print(f"姓名: {s.name:10} | 手机: {s.phone} | 班级: {s.class_name or '无'}")
    
    print("=" * 50)
    print(f"总共 {Student.query.count()} 个学员")
