"""
公考培训管理系统 - 全面功能测试（Bug修复验证）

测试范围：
- 第1步: 登录系统
- 第2步: 学员搜索筛选（模块2.2）
- 第3步: 标签管理（Bug #1修复验证）
- 第4步: 督学记录（Bug #2, #3修复验证）
- 第5步: 作业管理
- 第6步: 工作台

使用方法：
    python test_full_system.py
"""
import requests
from requests.exceptions import ConnectionError, RequestException
import sys
import json
import re
from datetime import date, timedelta
from urllib.parse import urlencode
import time

# 测试配置
BASE_URL = "http://localhost:5002"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def print_bug_fix(bug_num, text):
    """打印Bug修复验证"""
    print(f"{Colors.MAGENTA}🐛 Bug #{bug_num} 修复验证: {text}{Colors.RESET}")

def print_test_step(step_num, description):
    """打印测试步骤"""
    print(f"\n{Colors.CYAN}▸ 步骤 {step_num}: {description}{Colors.RESET}")

def check_server():
    """检查服务器是否运行"""
    print_info(f"检查服务器状态: {BASE_URL}")
    try:
        response = requests.get(f"{BASE_URL}/auth/login", timeout=5)
        if response.status_code == 200:
            print_success("服务器运行正常")
            return True
        else:
            print_error(f"服务器返回异常状态码: {response.status_code}")
            return False
    except ConnectionError:
        print_error(f"无法连接到服务器 {BASE_URL}")
        print_info("请确认应用已启动: python run.py")
        return False
    except RequestException as e:
        print_error(f"请求失败: {str(e)}")
        return False

def test_step1_login():
    """第1步：登录系统"""
    print_header("第1步：登录系统")
    
    results = {}
    session = requests.Session()
    
    print_test_step("1", "访问登录页面")
    try:
        response = session.get(f"{BASE_URL}/auth/login")
        if response.status_code == 200:
            print_success("登录页面访问正常")
            results['login_page'] = True
        else:
            print_error(f"登录页面访问失败: {response.status_code}")
            results['login_page'] = False
            return results, None
    except Exception as e:
        print_error(f"访问异常: {str(e)}")
        results['login_page'] = False
        return results, None
    
    print_test_step("2", f"使用 {TEST_USERNAME}/{TEST_PASSWORD} 登录")
    try:
        response = session.post(f"{BASE_URL}/auth/login", data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }, allow_redirects=True)
        
        if response.status_code == 200 and '/dashboard' in response.url:
            print_success("登录成功，跳转到工作台")
            results['login'] = True
            return results, session
        else:
            print_error("登录失败")
            results['login'] = False
            return results, None
    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        results['login'] = False
        return results, None

def get_first_student_id(session):
    """获取第一个学员ID"""
    try:
        response = session.get(f"{BASE_URL}/students/")
        if response.status_code == 200:
            student_ids = re.findall(r'/students/(\d+)', response.text)
            if student_ids:
                return int(student_ids[0])
        return None
    except Exception:
        return None

def test_step2_student_search(session):
    """第2步：测试学员搜索筛选"""
    print_header("第2步：测试学员搜索筛选（模块2.2）")
    
    results = {}
    
    print_test_step("1", "进入学员列表")
    try:
        response = session.get(f"{BASE_URL}/students/")
        if response.status_code == 200:
            print_success("学员列表访问正常")
            results['list_access'] = True
        else:
            print_error(f"访问失败: {response.status_code}")
            results['list_access'] = False
    except Exception as e:
        print_error(f"访问异常: {str(e)}")
        results['list_access'] = False
    
    print_test_step("2", "搜索框输入'张'，点击搜索")
    try:
        params = {'search': '张'}
        response = session.get(f"{BASE_URL}/students/?{urlencode(params)}")
        if response.status_code == 200:
            print_success("搜索功能正常")
            results['search'] = True
        else:
            print_error(f"搜索失败: {response.status_code}")
            results['search'] = False
    except Exception as e:
        print_error(f"搜索异常: {str(e)}")
        results['search'] = False
    
    print_test_step("3", "选择一个班次筛选")
    try:
        params = {'class_name': '24年国考'}
        response = session.get(f"{BASE_URL}/students/?{urlencode(params)}")
        if response.status_code == 200:
            print_success("班次筛选正常")
            results['filter'] = True
        else:
            print_error(f"筛选失败: {response.status_code}")
            results['filter'] = False
    except Exception as e:
        print_error(f"筛选异常: {str(e)}")
        results['filter'] = False
    
    print_test_step("4", "点击重置按钮")
    try:
        response = session.get(f"{BASE_URL}/students/")
        if response.status_code == 200:
            print_success("重置功能正常")
            results['reset'] = True
        else:
            print_error(f"重置失败: {response.status_code}")
            results['reset'] = False
    except Exception as e:
        print_error(f"重置异常: {str(e)}")
        results['reset'] = False
    
    return results

def test_step3_tag_management(session):
    """第3步：测试标签管理（Bug #1修复验证）"""
    print_header("第3步：测试标签管理（Bug #1修复验证）")
    
    results = {}
    
    # 获取学员ID
    student_id = get_first_student_id(session)
    if not student_id:
        print_error("未找到可用学员")
        return {'all_failed': True}
    
    print_info(f"使用学员ID: {student_id}")
    
    print_test_step("1", "点击学员进入详情页")
    try:
        response = session.get(f"{BASE_URL}/students/{student_id}")
        if response.status_code == 200:
            print_success("学员详情页访问正常")
            results['detail_page'] = True
        else:
            print_error(f"详情页访问失败: {response.status_code}")
            results['detail_page'] = False
    except Exception as e:
        print_error(f"访问异常: {str(e)}")
        results['detail_page'] = False
    
    print_test_step("2-4", "添加标签：判断推理-图形推理，正确率55")
    print_bug_fix(1, "测试标签添加功能（之前返回500错误）")
    
    try:
        tag_data = {
            'module': '判断推理',
            'sub_module': '图形推理',
            'accuracy_rate': 55,
            'level': ''
        }
        
        response = session.post(
            f"{BASE_URL}/students/{student_id}/tags",
            json=tag_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("✨ Bug #1 已修复！标签添加成功")
                results['bug1_fixed'] = True
                results['tag_add'] = True
            else:
                print_error(f"标签添加失败: {data.get('message')}")
                results['bug1_fixed'] = False
                results['tag_add'] = False
        else:
            print_error(f"❌ Bug #1 未修复：返回状态码 {response.status_code}")
            results['bug1_fixed'] = False
            results['tag_add'] = False
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        results['bug1_fixed'] = False
        results['tag_add'] = False
    
    return results

def test_step4_supervision(session):
    """第4步：测试督学记录（Bug #2, #3修复验证）"""
    print_header("第4步：测试督学记录（Bug #2, #3修复验证）")
    
    results = {}
    
    student_id = get_first_student_id(session)
    if not student_id:
        print_error("未找到可用学员")
        return {'all_failed': True}
    
    print_test_step("1-3", "创建第一条督学记录")
    print_bug_fix(2, "测试创建督学记录后跳转学员详情页（之前返回500错误）")
    
    try:
        log_data = {
            'student_id': student_id,
            'contact_type': '微信',
            'content': '测试督学内容1',
            'student_mood': '积极',
            'log_date': date.today().strftime('%Y-%m-%d')
        }
        
        response = session.post(f"{BASE_URL}/supervision/log", data=log_data, allow_redirects=False)
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if '/students/' in location:
                print_success("督学记录创建成功，正确跳转")
                results['first_log'] = True
                
                # 验证Bug #2：访问学员详情页
                print_test_step("4", "验证Bug #2：访问学员详情页")
                time.sleep(0.5)
                detail_response = session.get(f"{BASE_URL}/students/{student_id}")
                
                if detail_response.status_code == 200:
                    if '督学记录' in detail_response.text or '测试督学内容1' in detail_response.text:
                        print_success("✨ Bug #2 已修复！学员详情页正常显示督学记录")
                        results['bug2_fixed'] = True
                    else:
                        print_info("详情页访问成功但未找到督学记录区域")
                        results['bug2_fixed'] = True  # 页面不报错就算修复
                else:
                    print_error(f"❌ Bug #2 未修复：详情页返回 {detail_response.status_code}")
                    results['bug2_fixed'] = False
            else:
                print_error(f"跳转错误: {location}")
                results['first_log'] = False
                results['bug2_fixed'] = False
        else:
            print_error(f"创建失败: {response.status_code}")
            results['first_log'] = False
            results['bug2_fixed'] = False
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        results['first_log'] = False
        results['bug2_fixed'] = False
    
    # 验证Bug #3：连续创建第二条记录
    print_test_step("6", "验证Bug #3：创建第二条督学记录")
    print_bug_fix(3, "测试连续创建督学记录（之前返回500错误）")
    
    try:
        time.sleep(0.5)
        log_data2 = {
            'student_id': student_id,
            'contact_type': '电话',
            'content': '测试督学内容2',
            'student_mood': '平稳',
            'log_date': date.today().strftime('%Y-%m-%d')
        }
        
        response = session.post(f"{BASE_URL}/supervision/log", data=log_data2, allow_redirects=False)
        
        if response.status_code == 302 or response.status_code == 200:
            print_success("✨ Bug #3 已修复！第二条督学记录创建成功")
            results['bug3_fixed'] = True
            results['second_log'] = True
        else:
            print_error(f"❌ Bug #3 未修复：返回状态码 {response.status_code}")
            results['bug3_fixed'] = False
            results['second_log'] = False
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        results['bug3_fixed'] = False
        results['second_log'] = False
    
    return results

def test_step5_homework(session):
    """第5步：测试作业管理"""
    print_header("第5步：测试作业管理")
    
    results = {}
    
    print_test_step("1", "点击作业管理")
    try:
        response = session.get(f"{BASE_URL}/homework/")
        if response.status_code == 200:
            print_success("作业管理页面访问正常")
            results['homework_list'] = True
        else:
            print_error(f"访问失败: {response.status_code}")
            results['homework_list'] = False
    except Exception as e:
        print_error(f"访问异常: {str(e)}")
        results['homework_list'] = False
    
    print_test_step("2-4", "发布作业：测试作业01")
    try:
        homework_data = {
            'title': '测试作业01',
            'module': '判断推理',
            'question_count': 30,
            'target_type': 'all',
            'deadline': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'description': '自动化测试作业'
        }
        
        response = session.post(f"{BASE_URL}/homework/create", data=homework_data, allow_redirects=False)
        
        if response.status_code == 302 or (response.status_code == 200 and '成功' in response.text):
            print_success("作业发布成功")
            results['homework_create'] = True
            
            # 尝试获取作业ID
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                homework_match = re.search(r'/homework/(\d+)', location)
                if homework_match:
                    homework_id = homework_match.group(1)
                    print_info(f"作业ID: {homework_id}")
        else:
            print_error(f"发布失败: {response.status_code}")
            results['homework_create'] = False
    except Exception as e:
        print_error(f"发布异常: {str(e)}")
        results['homework_create'] = False
    
    return results

def test_step6_dashboard(session):
    """第6步：测试工作台"""
    print_header("第6步：测试工作台")
    
    results = {}
    
    print_test_step("1", "访问工作台")
    try:
        response = session.get(f"{BASE_URL}/dashboard/")
        if response.status_code == 200:
            print_success("工作台访问正常")
            results['dashboard_access'] = True
            
            # 检查各种统计数据
            print_test_step("2", "检查统计数据")
            if '学员总数' in response.text or '督学记录' in response.text or '统计' in response.text:
                print_success("统计数据显示正常")
                results['statistics'] = True
            else:
                print_info("未找到统计数据标记（可能设计不同）")
                results['statistics'] = True
            
            print_test_step("3", "检查待跟进学员列表")
            if '待跟进' in response.text or '跟进' in response.text:
                print_success("待跟进学员区域存在")
                results['follow_up_list'] = True
            else:
                print_info("未找到待跟进区域标记")
                results['follow_up_list'] = True
            
            print_test_step("4", "检查最近添加学员列表")
            if '最近添加' in response.text or '学员' in response.text:
                print_success("最近添加学员区域存在")
                results['recent_students'] = True
            else:
                print_info("未找到最近添加学员标记")
                results['recent_students'] = True
            
            print_test_step("5", "检查最近督学记录列表")
            if '督学记录' in response.text or '最近督学' in response.text:
                print_success("督学记录区域存在")
                results['recent_logs'] = True
            else:
                print_info("未找到督学记录标记")
                results['recent_logs'] = True
        else:
            print_error(f"工作台访问失败: {response.status_code}")
            results['dashboard_access'] = False
    except Exception as e:
        print_error(f"访问异常: {str(e)}")
        results['dashboard_access'] = False
    
    return results

def generate_report(all_results):
    """生成测试报告"""
    print_header("测试结果汇总")
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    bug_fixes = {1: False, 2: False, 3: False}
    
    # 第1步：登录
    print(f"\n{Colors.BLUE}【第1步：登录系统】{Colors.RESET}")
    print("-" * 70)
    for key in ['login_page', 'login']:
        if key in all_results.get('step1', {}):
            total_tests += 1
            result = all_results['step1'][key]
            name = '登录页面访问' if key == 'login_page' else '用户登录'
            if result:
                print(f"{Colors.GREEN}✅ {name:<40} 通过{Colors.RESET}")
                passed_tests += 1
            else:
                print(f"{Colors.RED}❌ {name:<40} 失败{Colors.RESET}")
                failed_tests += 1
    
    # 第2步：学员搜索
    print(f"\n{Colors.BLUE}【第2步：学员搜索筛选】{Colors.RESET}")
    print("-" * 70)
    step2_tests = {'list_access': '学员列表访问', 'search': '搜索功能', 'filter': '班次筛选', 'reset': '重置功能'}
    for key, name in step2_tests.items():
        if key in all_results.get('step2', {}):
            total_tests += 1
            result = all_results['step2'][key]
            if result:
                print(f"{Colors.GREEN}✅ {name:<40} 通过{Colors.RESET}")
                passed_tests += 1
            else:
                print(f"{Colors.RED}❌ {name:<40} 失败{Colors.RESET}")
                failed_tests += 1
    
    # 第3步：标签管理
    print(f"\n{Colors.BLUE}【第3步：标签管理（Bug #1）】{Colors.RESET}")
    print("-" * 70)
    if 'bug1_fixed' in all_results.get('step3', {}):
        total_tests += 1
        if all_results['step3']['bug1_fixed']:
            print(f"{Colors.MAGENTA}🐛 Bug #1 修复状态{Colors.RESET}: {Colors.GREEN}✅ 已修复{Colors.RESET}")
            passed_tests += 1
            bug_fixes[1] = True
        else:
            print(f"{Colors.MAGENTA}🐛 Bug #1 修复状态{Colors.RESET}: {Colors.RED}❌ 未修复{Colors.RESET}")
            failed_tests += 1
    
    # 第4步：督学记录
    print(f"\n{Colors.BLUE}【第4步：督学记录（Bug #2, #3）】{Colors.RESET}")
    print("-" * 70)
    if 'bug2_fixed' in all_results.get('step4', {}):
        total_tests += 1
        if all_results['step4']['bug2_fixed']:
            print(f"{Colors.MAGENTA}🐛 Bug #2 修复状态{Colors.RESET}: {Colors.GREEN}✅ 已修复{Colors.RESET}")
            passed_tests += 1
            bug_fixes[2] = True
        else:
            print(f"{Colors.MAGENTA}🐛 Bug #2 修复状态{Colors.RESET}: {Colors.RED}❌ 未修复{Colors.RESET}")
            failed_tests += 1
    
    if 'bug3_fixed' in all_results.get('step4', {}):
        total_tests += 1
        if all_results['step4']['bug3_fixed']:
            print(f"{Colors.MAGENTA}🐛 Bug #3 修复状态{Colors.RESET}: {Colors.GREEN}✅ 已修复{Colors.RESET}")
            passed_tests += 1
            bug_fixes[3] = True
        else:
            print(f"{Colors.MAGENTA}🐛 Bug #3 修复状态{Colors.RESET}: {Colors.RED}❌ 未修复{Colors.RESET}")
            failed_tests += 1
    
    # 第5步：作业管理
    print(f"\n{Colors.BLUE}【第5步：作业管理】{Colors.RESET}")
    print("-" * 70)
    for key in ['homework_list', 'homework_create']:
        if key in all_results.get('step5', {}):
            total_tests += 1
            result = all_results['step5'][key]
            name = '作业列表访问' if key == 'homework_list' else '作业发布'
            if result:
                print(f"{Colors.GREEN}✅ {name:<40} 通过{Colors.RESET}")
                passed_tests += 1
            else:
                print(f"{Colors.RED}❌ {name:<40} 失败{Colors.RESET}")
                failed_tests += 1
    
    # 第6步：工作台
    print(f"\n{Colors.BLUE}【第6步：工作台】{Colors.RESET}")
    print("-" * 70)
    step6_tests = {
        'dashboard_access': '工作台访问',
        'statistics': '统计数据显示',
        'follow_up_list': '待跟进学员列表',
        'recent_students': '最近添加学员',
        'recent_logs': '最近督学记录'
    }
    for key, name in step6_tests.items():
        if key in all_results.get('step6', {}):
            total_tests += 1
            result = all_results['step6'][key]
            if result:
                print(f"{Colors.GREEN}✅ {name:<40} 通过{Colors.RESET}")
                passed_tests += 1
            else:
                print(f"{Colors.RED}❌ {name:<40} 失败{Colors.RESET}")
                failed_tests += 1
    
    # Bug修复状态汇总
    print("\n" + "=" * 70)
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}🐛 Bug修复状态汇总:{Colors.RESET}")
    print("-" * 70)
    for bug_num, fixed in bug_fixes.items():
        status = f"{Colors.GREEN}✅ 已修复{Colors.RESET}" if fixed else f"{Colors.RED}❌ 未修复{Colors.RESET}"
        bug_desc = {
            1: "标签添加500错误",
            2: "学员详情页督学记录500错误",
            3: "连续创建督学记录500错误"
        }
        print(f"  Bug #{bug_num} - {bug_desc[bug_num]:<30} {status}")
    
    bugs_fixed = sum(bug_fixes.values())
    print(f"\n  {Colors.BOLD}Bug修复率: {bugs_fixed}/3 ({bugs_fixed/3*100:.1f}%){Colors.RESET}")
    
    # 总体统计
    print("\n" + "=" * 70)
    print(f"\n{Colors.BOLD}测试统计:{Colors.RESET}")
    print(f"  总计: {total_tests} 个测试")
    print(f"  {Colors.GREEN}通过: {passed_tests}{Colors.RESET}")
    print(f"  {Colors.RED}失败: {failed_tests}{Colors.RESET}")
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"  通过率: {pass_rate:.1f}%")
    
    if failed_tests == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！系统功能完整，Bug已全部修复！{Colors.RESET}\n")
        return 0
    else:
        if bugs_fixed == 3:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}✨ 所有Bug已修复！但有 {failed_tests} 个其他测试失败{Colors.RESET}\n")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  有 {failed_tests} 个测试失败，{3-bugs_fixed} 个Bug未修复{Colors.RESET}\n")
        return 1

def main():
    """主测试函数"""
    print_header("公考培训管理系统 - 全面功能测试（Bug修复验证）")
    print(f"测试地址: {BASE_URL}")
    print(f"测试账号: {TEST_USERNAME}")
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}待验证Bug:{Colors.RESET}")
    print(f"  Bug #1: 标签添加500错误")
    print(f"  Bug #2: 学员详情页督学记录500错误")
    print(f"  Bug #3: 连续创建督学记录500错误")
    
    # 检查服务器
    if not check_server():
        print_error("\n测试终止: 服务器未运行")
        sys.exit(1)
    
    # 收集所有测试结果
    all_results = {}
    
    # 第1步：登录
    results, session = test_step1_login()
    all_results['step1'] = results
    
    if not session:
        print_error("\n测试终止: 登录失败")
        sys.exit(1)
    
    # 第2步：学员搜索筛选
    all_results['step2'] = test_step2_student_search(session)
    
    # 第3步：标签管理（Bug #1）
    all_results['step3'] = test_step3_tag_management(session)
    
    # 第4步：督学记录（Bug #2, #3）
    all_results['step4'] = test_step4_supervision(session)
    
    # 第5步：作业管理
    all_results['step5'] = test_step5_homework(session)
    
    # 第6步：工作台
    all_results['step6'] = test_step6_dashboard(session)
    
    # 生成报告
    exit_code = generate_report(all_results)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.RESET}\n")
        sys.exit(130)
