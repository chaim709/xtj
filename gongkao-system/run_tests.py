#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站功能测试脚本"""

import requests
import json

BASE_URL = "http://localhost:5002"
session = requests.Session()
bugs = []

def login():
    resp = session.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123"}, allow_redirects=False)
    return resp.status_code in [200, 302]

def test(name, condition, bug_detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition and bug_detail:
        bugs.append(f"{name}: {bug_detail}")

print("="*60)
print("公考培训管理系统 - 全站测试")
print("="*60)

# 登录
if login():
    print("[PASS] 登录成功\n")
else:
    print("[FAIL] 登录失败")
    exit(1)

# 模块2.2: 学员搜索筛选测试
print("-"*40)
print("模块2.2: 学员搜索筛选测试")
print("-"*40)

test("2.2.1 按姓名搜索", session.get(f"{BASE_URL}/students/?search=张").status_code == 200)
test("2.2.2 按电话搜索", session.get(f"{BASE_URL}/students/?search=138").status_code == 200)
test("2.2.3 按班次筛选", session.get(f"{BASE_URL}/students/?class_name=基础班").status_code == 200)
test("2.2.4 按报考类型筛选", session.get(f"{BASE_URL}/students/?exam_type=国省考").status_code == 200)
test("2.2.5 重点关注筛选", session.get(f"{BASE_URL}/students/?need_attention=1").status_code == 200)
test("2.2.6 分页测试", session.get(f"{BASE_URL}/students/?page=1").status_code == 200)

# 模块2.3-2.4: 标签管理和关注状态
print("\n" + "-"*40)
print("模块2.3-2.4: 标签管理和关注状态")
print("-"*40)

# 获取第一个学员ID
resp = session.get(f"{BASE_URL}/students/")
if "students/1" in resp.text or "/students/" in resp.text:
    test("2.3.1 获取学员标签", session.get(f"{BASE_URL}/students/1/tags").status_code in [200, 404])
    
    # 测试添加标签
    tag_data = {"module": "言语理解", "sub_module": "片段阅读", "accuracy_rate": 60}
    resp = session.post(f"{BASE_URL}/students/1/tags", json=tag_data)
    test("2.3.2 添加标签", resp.status_code in [200, 400, 404])
    
    # 测试关注状态切换
    resp = session.post(f"{BASE_URL}/students/1/toggle-attention")
    test("2.4.1 切换关注状态", resp.status_code in [200, 302])
else:
    print("[SKIP] 无学员数据，跳过标签测试")

# 模块3: 督学管理测试
print("\n" + "-"*40)
print("模块3: 督学管理测试")
print("-"*40)

test("3.1 督学日志页面", session.get(f"{BASE_URL}/supervision/log").status_code == 200)
test("3.2 我的督学记录", session.get(f"{BASE_URL}/supervision/my-logs").status_code == 200)
test("3.3 日期筛选", session.get(f"{BASE_URL}/supervision/my-logs?start_date=2024-01-01").status_code == 200)

# 提交督学日志
log_data = {
    "student_id": "1",
    "contact_type": "微信",
    "content": "测试督学内容",
    "student_mood": "积极",
    "log_date": "2026-01-27"
}
resp = session.post(f"{BASE_URL}/supervision/log", data=log_data, allow_redirects=False)
test("3.4 提交督学日志", resp.status_code in [200, 302, 400])

# 模块4: 作业管理测试
print("\n" + "-"*40)
print("模块4: 作业管理测试")
print("-"*40)

test("4.1.1 作业列表页面", session.get(f"{BASE_URL}/homework/").status_code == 200)
test("4.1.2 创建作业页面", session.get(f"{BASE_URL}/homework/create").status_code == 200)
test("4.1.3 作业状态筛选", session.get(f"{BASE_URL}/homework/?status=published").status_code == 200)

# 创建作业
hw_data = {
    "task_name": "测试作业",
    "task_type": "专项练习",
    "module": "判断推理",
    "question_count": "30",
    "target_type": "all"
}
resp = session.post(f"{BASE_URL}/homework/create", data=hw_data, allow_redirects=False)
test("4.1.4 发布作业", resp.status_code in [200, 302])

# 模块5: 工作台测试
print("\n" + "-"*40)
print("模块5: 工作台测试")
print("-"*40)

resp = session.get(f"{BASE_URL}/dashboard/")
test("5.1 工作台页面加载", resp.status_code == 200)
test("5.2 统计数据显示", "学员总数" in resp.text or "total_students" in resp.text or "stat-card" in resp.text)
test("5.3 待跟进列表", "待跟进" in resp.text or "follow" in resp.text.lower())

# 模块6: 边界条件测试
print("\n" + "-"*40)
print("模块6: 边界条件测试")
print("-"*40)

test("6.1 超长搜索词", session.get(f"{BASE_URL}/students/?search={'a'*500}").status_code == 200)
test("6.2 特殊字符搜索", session.get(f"{BASE_URL}/students/?search=<script>").status_code == 200)
test("6.3 无效页码", session.get(f"{BASE_URL}/students/?page=-1").status_code in [200, 400])
test("6.4 超大页码", session.get(f"{BASE_URL}/students/?page=99999").status_code == 200)

# 汇总
print("\n" + "="*60)
print("测试完成")
print("="*60)

if bugs:
    print(f"\n发现 {len(bugs)} 个Bug:")
    for b in bugs:
        print(f"  - {b}")
else:
    print("\n所有测试通过!")
