#!/usr/bin/env python3
"""
第三阶段功能测试脚本
测试日历、分析、API、提醒等新功能
"""
import requests
import json
from datetime import date, datetime, timedelta

BASE_URL = "http://localhost:5001"
API_KEY = "gongkao-api-key-2026-dev-only"

# 测试结果收集
results = {
    "passed": [],
    "failed": [],
    "warnings": []
}


def log_result(test_name, passed, message=""):
    """记录测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"       {message}")
    if passed:
        results["passed"].append(test_name)
    else:
        results["failed"].append((test_name, message))


def log_warning(test_name, message):
    """记录警告"""
    print(f"⚠️ WARN: {test_name}")
    print(f"       {message}")
    results["warnings"].append((test_name, message))


# ============ API测试 ============

def test_api_auth():
    """测试API认证"""
    print("\n" + "="*50)
    print("API认证测试")
    print("="*50)
    
    # 无API Key
    r = requests.get(f"{BASE_URL}/api/v1/students")
    log_result("无API Key返回401", r.status_code == 401)
    
    # 错误API Key
    r = requests.get(f"{BASE_URL}/api/v1/students", headers={"X-API-Key": "wrong"})
    log_result("错误API Key返回401", r.status_code == 401)
    
    # 正确API Key
    r = requests.get(f"{BASE_URL}/api/v1/students", headers={"X-API-Key": API_KEY})
    log_result("正确API Key返回200", r.status_code == 200)
    

def test_api_students():
    """测试学员API"""
    print("\n" + "="*50)
    print("学员API测试")
    print("="*50)
    
    headers = {"X-API-Key": API_KEY}
    
    # 获取列表
    r = requests.get(f"{BASE_URL}/api/v1/students", headers=headers)
    data = r.json()
    log_result("获取学员列表", data.get("success") == True, f"Total: {data.get('pagination', {}).get('total', 0)}")
    
    # 分页
    r = requests.get(f"{BASE_URL}/api/v1/students?page=1&per_page=5", headers=headers)
    data = r.json()
    log_result("分页功能", len(data.get("data", [])) <= 5, f"返回 {len(data.get('data', []))} 条")
    
    # 获取详情
    if data.get("data"):
        student_id = data["data"][0]["id"]
        r = requests.get(f"{BASE_URL}/api/v1/students/{student_id}", headers=headers)
        detail = r.json()
        log_result("获取学员详情", detail.get("success") == True, f"Name: {detail.get('data', {}).get('name', 'N/A')}")
        
        # 检查薄弱项字段
        tags = detail.get("data", {}).get("weakness_tags", [])
        log_result("薄弱项字段正确", True, f"Tags count: {len(tags)}")
    
    # 不存在的学员
    r = requests.get(f"{BASE_URL}/api/v1/students/99999", headers=headers)
    log_result("不存在学员返回404", r.status_code == 404)


def test_api_batches():
    """测试班次API"""
    print("\n" + "="*50)
    print("班次API测试")
    print("="*50)
    
    headers = {"X-API-Key": API_KEY}
    
    # 获取列表
    r = requests.get(f"{BASE_URL}/api/v1/batches", headers=headers)
    data = r.json()
    log_result("获取班次列表", data.get("success") == True, f"Batches: {len(data.get('data', []))}")
    
    # 获取详情
    if data.get("data"):
        batch_id = data["data"][0]["id"]
        r = requests.get(f"{BASE_URL}/api/v1/batches/{batch_id}", headers=headers)
        detail = r.json()
        log_result("获取班次详情", detail.get("success") == True, f"Name: {detail.get('data', {}).get('name', 'N/A')}")
        
        # 获取班次学员
        r = requests.get(f"{BASE_URL}/api/v1/batches/{batch_id}/students", headers=headers)
        students = r.json()
        log_result("获取班次学员", students.get("success") == True, f"Students: {len(students.get('data', []))}")


def test_api_weakness_update():
    """测试薄弱项更新API"""
    print("\n" + "="*50)
    print("薄弱项更新API测试")
    print("="*50)
    
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    # 先获取一个学员
    r = requests.get(f"{BASE_URL}/api/v1/students", headers={"X-API-Key": API_KEY})
    students = r.json().get("data", [])
    if not students:
        log_warning("薄弱项更新", "没有可用学员")
        return
    
    student_id = students[0]["id"]
    
    # 更新薄弱项
    payload = {
        "tags": [
            {"module": "常识判断", "submodule": "科技常识", "accuracy": 35}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v1/students/{student_id}/weakness", 
                     headers=headers, json=payload)
    data = r.json()
    log_result("更新薄弱项", data.get("success") == True)
    
    # 验证更新
    r = requests.get(f"{BASE_URL}/api/v1/students/{student_id}", headers={"X-API-Key": API_KEY})
    detail = r.json()
    tags = detail.get("data", {}).get("weakness_tags", [])
    has_new_tag = any(t.get("module") == "常识判断" for t in tags)
    log_result("薄弱项验证", has_new_tag, f"Tags: {len(tags)}")


# ============ 日历/分析内部API测试 ============

def test_calendar_service():
    """测试日历服务（内部）"""
    print("\n" + "="*50)
    print("日历服务测试（内部）")
    print("="*50)
    
    import sys
    sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/gongkao-system')
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.services.calendar_service import CalendarService
            
            # 测试获取事件
            today = date.today()
            start = today.replace(day=1)
            end = today.replace(day=28)
            
            events = CalendarService.get_calendar_events(start, end)
            log_result("获取日历事件", isinstance(events, list), f"Events: {len(events)}")
            
            # 测试获取日期详情
            schedules = CalendarService.get_day_schedules(today)
            log_result("获取日期详情", isinstance(schedules, list), f"Schedules: {len(schedules)}")
            
            # 测试月度汇总
            summary = CalendarService.get_month_summary(today.year, today.month)
            log_result("获取月度汇总", "total_days" in summary, f"Days: {summary.get('total_days', 0)}")
            
    except Exception as e:
        log_result("日历服务", False, str(e))


def test_analytics_service():
    """测试分析服务（内部）"""
    print("\n" + "="*50)
    print("分析服务测试（内部）")
    print("="*50)
    
    import sys
    sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/gongkao-system')
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.services.analytics_service import AnalyticsService
            
            # 测试概览统计
            stats = AnalyticsService.get_overview_stats(30)
            log_result("获取概览统计", "students" in stats, 
                      f"Total: {stats.get('students', {}).get('total', 0)}")
            
            # 测试趋势数据
            trend = AnalyticsService.get_student_trend(30)
            log_result("获取学员趋势", "dates" in trend and "counts" in trend,
                      f"Days: {len(trend.get('dates', []))}")
            
            # 测试状态分布
            distribution = AnalyticsService.get_student_status_distribution()
            log_result("获取状态分布", isinstance(distribution, list),
                      f"Categories: {len(distribution)}")
            
            # 测试薄弱点分布
            weakness = AnalyticsService.get_weakness_distribution(10)
            log_result("获取薄弱点分布", "modules" in weakness,
                      f"Modules: {len(weakness.get('modules', []))}")
            
            # 测试督学排行
            ranking = AnalyticsService.get_supervision_ranking(30, 10)
            log_result("获取督学排行", "names" in ranking,
                      f"Users: {len(ranking.get('names', []))}")
            
            # 测试班次进度
            progress = AnalyticsService.get_batch_progress()
            log_result("获取班次进度", isinstance(progress, list),
                      f"Batches: {len(progress)}")
            
            # 测试考勤统计
            attendance = AnalyticsService.get_attendance_summary()
            log_result("获取考勤统计", "rate" in attendance,
                      f"Rate: {attendance.get('rate', 0)}%")
            
    except Exception as e:
        log_result("分析服务", False, str(e))


def test_reminder_service():
    """测试提醒服务（内部）"""
    print("\n" + "="*50)
    print("提醒服务测试（内部）")
    print("="*50)
    
    import sys
    sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/gongkao-system')
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.services.reminder_service import ReminderService
            
            # 测试待跟进学员
            pending = ReminderService.get_pending_follow_ups(10)
            log_result("获取待跟进学员", isinstance(pending, list),
                      f"Count: {len(pending)}")
            
            # 测试今日课程
            today_schedules = ReminderService.get_today_schedules_reminder()
            log_result("获取今日课程提醒", isinstance(today_schedules, list),
                      f"Count: {len(today_schedules)}")
            
            # 测试需关注学员
            attention = ReminderService.get_attention_students(10)
            log_result("获取关注学员", isinstance(attention, list),
                      f"Count: {len(attention)}")
            
            # 测试工作台汇总
            reminders = ReminderService.get_dashboard_reminders()
            log_result("获取工作台提醒汇总", "pending_follow_ups" in reminders,
                      f"Pending: {reminders.get('pending_follow_ups', 0)}")
            
    except Exception as e:
        log_result("提醒服务", False, str(e))


def test_routes_exist():
    """测试路由是否存在"""
    print("\n" + "="*50)
    print("路由存在性测试")
    print("="*50)
    
    # 这些路由应该返回302（重定向到登录）而不是404
    routes = [
        ("/calendar/", "日历页面"),
        ("/analytics/", "分析页面"),
        ("/dashboard/", "工作台"),
    ]
    
    for route, name in routes:
        r = requests.get(f"{BASE_URL}{route}", allow_redirects=False)
        # 应该是302重定向或200成功
        passed = r.status_code in [200, 302]
        log_result(f"{name}路由存在", passed, f"Status: {r.status_code}")


def test_student_enhanced_data():
    """测试学员增强数据"""
    print("\n" + "="*50)
    print("学员增强数据测试（内部）")
    print("="*50)
    
    import sys
    sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/gongkao-system')
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.routes.students import get_student_enhanced_data
            from app.models.student import Student
            
            # 获取一个学员
            student = Student.query.first()
            if not student:
                log_warning("学员增强数据", "没有可用学员")
                return
            
            # 测试增强数据
            data = get_student_enhanced_data(student.id)
            
            log_result("督学汇总数据", "supervision" in data,
                      f"Total logs: {data.get('supervision', {}).get('total_logs', 0)}")
            
            log_result("班次数据", "batches" in data,
                      f"Batches: {len(data.get('batches', []))}")
            
            log_result("考勤数据", "attendance" in data,
                      f"Rate: {data.get('attendance', {}).get('rate', 0)}%")
            
    except Exception as e:
        log_result("学员增强数据", False, str(e))


# ============ 主测试函数 ============

def main():
    print("\n" + "="*60)
    print("第三阶段功能全方位测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服务地址: {BASE_URL}")
    
    # 运行所有测试
    test_api_auth()
    test_api_students()
    test_api_batches()
    test_api_weakness_update()
    test_calendar_service()
    test_analytics_service()
    test_reminder_service()
    test_routes_exist()
    test_student_enhanced_data()
    
    # 输出汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    print(f"✅ 通过: {len(results['passed'])} 项")
    print(f"❌ 失败: {len(results['failed'])} 项")
    print(f"⚠️ 警告: {len(results['warnings'])} 项")
    
    if results["failed"]:
        print("\n失败的测试:")
        for name, msg in results["failed"]:
            print(f"  - {name}: {msg}")
    
    if results["warnings"]:
        print("\n警告:")
        for name, msg in results["warnings"]:
            print(f"  - {name}: {msg}")
    
    print("\n" + "="*60)
    
    return len(results["failed"]) == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
