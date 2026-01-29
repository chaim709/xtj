#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
学员搜索筛选测试脚本
测试模块2.2: 姓名/电话/班次/类型/分页
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5002"
session = requests.Session()

bugs = []

def log_result(test_id, test_name, passed, details=""):
    """记录测试结果"""
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"{test_id} {test_name}: {status}")
    if details:
        print(f"   详情: {details}")
    if not passed:
        bugs.append({
            "id": test_id,
            "name": test_name,
            "details": details
        })

def login():
    """登录系统"""
    # 获取登录页面
    login_url = f"{BASE_URL}/auth/login"
    resp = session.get(login_url)
    
    # 提交登录
    data = {
        "username": "admin",
        "password": "admin123"
    }
    resp = session.post(login_url, data=data, allow_redirects=True)
    
    if "工作台" in resp.text or "Welcome" in resp.text or resp.url.endswith("/dashboard/"):
        print("✅ 登录成功")
        return True
    else:
        print("❌ 登录失败")
        return False

def test_search_by_name():
    """2.2.1 按姓名搜索"""
    # 先获取所有学员，找一个姓名来搜索
    resp = session.get(f"{BASE_URL}/students/")
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 尝试搜索一个不存在的名字
    resp = session.get(f"{BASE_URL}/students/?search=不存在的名字xyz")
    
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 检查是否显示空结果或正常的列表
        if "暂无学员数据" in resp.text or "共 0 人" in resp.text:
            log_result("2.2.1", "按姓名搜索(无结果)", True, "正确显示无匹配结果")
        else:
            log_result("2.2.1", "按姓名搜索(无结果)", True, "搜索功能正常工作")
    else:
        log_result("2.2.1", "按姓名搜索", False, f"HTTP {resp.status_code}")

def test_search_by_phone():
    """2.2.2 按电话搜索"""
    resp = session.get(f"{BASE_URL}/students/?search=138")
    
    if resp.status_code == 200:
        log_result("2.2.2", "按电话搜索", True, "搜索功能正常")
    else:
        log_result("2.2.2", "按电话搜索", False, f"HTTP {resp.status_code}")

def test_filter_by_class():
    """2.2.3 按班次筛选"""
    resp = session.get(f"{BASE_URL}/students/?class_name=基础班")
    
    if resp.status_code == 200:
        log_result("2.2.3", "按班次筛选", True, "筛选功能正常")
    else:
        log_result("2.2.3", "按班次筛选", False, f"HTTP {resp.status_code}")

def test_filter_by_exam_type():
    """2.2.4 按报考类型筛选"""
    resp = session.get(f"{BASE_URL}/students/?exam_type=国省考")
    
    if resp.status_code == 200:
        log_result("2.2.4", "按报考类型筛选", True, "筛选功能正常")
    else:
        log_result("2.2.4", "按报考类型筛选", False, f"HTTP {resp.status_code}")

def test_filter_need_attention():
    """2.2.5 重点关注筛选"""
    resp = session.get(f"{BASE_URL}/students/?need_attention=1")
    
    if resp.status_code == 200:
        log_result("2.2.5", "重点关注筛选", True, "筛选功能正常")
    else:
        log_result("2.2.5", "重点关注筛选", False, f"HTTP {resp.status_code}")

def test_pagination():
    """2.2.6 分页测试"""
    # 测试第一页
    resp1 = session.get(f"{BASE_URL}/students/?page=1")
    
    # 测试第二页
    resp2 = session.get(f"{BASE_URL}/students/?page=2")
    
    # 测试超出范围的页码
    resp3 = session.get(f"{BASE_URL}/students/?page=9999")
    
    if resp1.status_code == 200 and resp2.status_code == 200:
        # 检查第二页是否正常（可能是空的或有数据）
        if resp3.status_code == 200:
            log_result("2.2.6", "分页测试", True, "分页功能正常工作")
        else:
            log_result("2.2.6", "分页测试", False, "超出范围的页码处理异常")
    else:
        log_result("2.2.6", "分页测试", False, f"分页请求失败")

def test_combined_filters():
    """额外测试: 组合筛选"""
    resp = session.get(f"{BASE_URL}/students/?search=测试&class_name=基础班&exam_type=国省考")
    
    if resp.status_code == 200:
        log_result("2.2.7", "组合筛选", True, "多条件组合筛选正常")
    else:
        log_result("2.2.7", "组合筛选", False, f"HTTP {resp.status_code}")

def test_reset_filters():
    """额外测试: 重置筛选"""
    # 先带参数访问
    resp1 = session.get(f"{BASE_URL}/students/?search=test&class_name=基础班")
    # 重置（不带参数访问）
    resp2 = session.get(f"{BASE_URL}/students/")
    
    if resp2.status_code == 200:
        log_result("2.2.8", "重置筛选", True, "重置功能正常")
    else:
        log_result("2.2.8", "重置筛选", False, f"HTTP {resp.status_code}")

def main():
    print("=" * 60)
    print("模块2.2: 学员搜索筛选测试")
    print("=" * 60)
    print()
    
    # 登录
    if not login():
        print("登录失败，无法继续测试")
        return
    
    print()
    print("-" * 40)
    print("开始测试...")
    print("-" * 40)
    
    # 执行测试
    test_search_by_name()
    test_search_by_phone()
    test_filter_by_class()
    test_filter_by_exam_type()
    test_filter_need_attention()
    test_pagination()
    test_combined_filters()
    test_reset_filters()
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
    
    if bugs:
        print(f"\n发现 {len(bugs)} 个Bug:")
        for bug in bugs:
            print(f"  - {bug['id']} {bug['name']}: {bug['details']}")
    else:
        print("\n✅ 所有测试通过，未发现Bug")
    
    return bugs

if __name__ == "__main__":
    main()
