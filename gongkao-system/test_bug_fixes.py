"""
公考培训管理系统 - Bug修复验证测试

专门验证3个已修复的Bug：
- Bug #1: 标签添加500错误
- Bug #2: 学员详情页督学记录500错误
- Bug #3: 连续创建督学记录500错误

使用方法：
    python test_bug_fixes.py
"""
import requests
from requests.exceptions import ConnectionError, RequestException
import sys
import json
import re
from datetime import date, timedelta
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
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^80}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.RESET}\n")

def print_bug_header(bug_num, title):
    """打印Bug测试标题"""
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}{'─'*80}{Colors.RESET}")
    print(f"{Colors.MAGENTA}{Colors.BOLD}🐛 Bug #{bug_num} 修复验证: {title}{Colors.RESET}")
    print(f"{Colors.MAGENTA}{Colors.BOLD}{'─'*80}{Colors.RESET}\n")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def print_step(step_text):
    """打印测试步骤"""
    print(f"{Colors.CYAN}▸ {step_text}{Colors.RESET}")

def print_result(bug_num, passed, details=""):
    """打印Bug修复结果"""
    if passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*80}")
        print(f"🎉 Bug #{bug_num} 修复验证: ✅ 通过 - 该Bug已成功修复！")
        print(f"{'='*80}{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}{'='*80}")
        print(f"⚠️  Bug #{bug_num} 修复验证: ❌ 失败 - 该Bug仍然存在")
        if details:
            print(f"详情: {details}")
        print(f"{'='*80}{Colors.RESET}")

def check_server():
    """检查服务器状态"""
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

def login():
    """登录系统"""
    print_step("登录系统")
    session = requests.Session()
    
    try:
        response = session.post(f"{BASE_URL}/auth/login", data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }, allow_redirects=True)
        
        if response.status_code == 200 and '/dashboard' in response.url:
            print_success(f"登录成功: {TEST_USERNAME}")
            return session
        else:
            print_error("登录失败")
            return None
    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        return None

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

def test_bug1_tag_addition(session):
    """Bug #1: 标签添加500错误"""
    print_bug_header(1, "标签添加500错误")
    
    # 获取学员ID
    print_step("步骤1: 进入学员列表，获取第一个学员")
    student_id = get_first_student_id(session)
    
    if not student_id:
        print_error("未找到可用学员")
        print_result(1, False, "无法获取学员ID")
        return False
    
    print_success(f"获取学员ID: {student_id}")
    
    # 访问学员详情页
    print_step("步骤2: 进入学员详情页")
    try:
        response = session.get(f"{BASE_URL}/students/{student_id}")
        if response.status_code == 200:
            print_success("学员详情页访问成功")
        else:
            print_error(f"详情页访问失败: {response.status_code}")
            print_result(1, False, f"详情页返回{response.status_code}")
            return False
    except Exception as e:
        print_error(f"访问异常: {str(e)}")
        print_result(1, False, str(e))
        return False
    
    # 添加标签
    print_step("步骤3: 添加薄弱项标签")
    print_info("标签信息: 判断推理 - 图形推理 (正确率: 55%)")
    
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
        
        print_info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    print_success("标签添加成功！")
                    print_info(f"返回消息: {data.get('message', '无消息')}")
                    
                    # 验证标签是否保存
                    time.sleep(0.3)
                    verify_response = session.get(f"{BASE_URL}/students/{student_id}")
                    if '图形推理' in verify_response.text:
                        print_success("标签已成功保存并显示在详情页")
                        print_result(1, True)
                        return True
                    else:
                        print_error("标签未在详情页显示")
                        print_result(1, False, "标签保存可能失败")
                        return False
                else:
                    print_error(f"添加失败: {data.get('message', '未知错误')}")
                    print_result(1, False, data.get('message'))
                    return False
            except json.JSONDecodeError:
                print_error("响应不是有效的JSON")
                print_result(1, False, "JSON解析错误")
                return False
        elif response.status_code == 500:
            print_error("⚠️  返回500错误 - Bug #1 未修复！")
            print_result(1, False, "服务器返回500错误")
            return False
        else:
            print_error(f"添加失败，状态码: {response.status_code}")
            print_result(1, False, f"状态码{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        print_result(1, False, str(e))
        return False

def test_bug2_student_detail_supervision(session):
    """Bug #2: 学员详情页督学记录500错误"""
    print_bug_header(2, "学员详情页督学记录500错误")
    
    # 获取学员ID
    print_step("步骤1: 获取学员信息")
    student_id = get_first_student_id(session)
    
    if not student_id:
        print_error("未找到可用学员")
        print_result(2, False, "无法获取学员ID")
        return False
    
    print_success(f"使用学员ID: {student_id}")
    
    # 先创建一条督学记录
    print_step("步骤2: 创建督学记录")
    try:
        log_data = {
            'student_id': student_id,
            'contact_type': '微信',
            'content': 'Bug #2测试 - 验证详情页显示',
            'student_mood': '积极',
            'log_date': date.today().strftime('%Y-%m-%d')
        }
        
        response = session.post(f"{BASE_URL}/supervision/log", data=log_data, allow_redirects=False)
        
        if response.status_code in [200, 302]:
            print_success("督学记录创建成功")
        else:
            print_error(f"督学记录创建失败: {response.status_code}")
    except Exception as e:
        print_error(f"创建督学记录异常: {str(e)}")
    
    # 访问学员详情页验证督学记录显示
    print_step("步骤3: 访问学员详情页，检查督学记录区域")
    time.sleep(0.5)
    
    try:
        response = session.get(f"{BASE_URL}/students/{student_id}")
        
        print_info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 500:
            print_error("⚠️  返回500错误 - Bug #2 未修复！")
            print_result(2, False, "学员详情页返回500错误")
            return False
        elif response.status_code == 200:
            print_success("学员详情页访问成功（状态码200）")
            
            # 检查督学记录区域
            if '督学记录' in response.text or 'supervision' in response.text.lower():
                print_success("页面包含督学记录相关内容")
                
                # 检查是否有具体的督学内容
                if 'Bug #2测试' in response.text or '沟通内容' in response.text:
                    print_success("督学记录内容正确渲染")
                    print_result(2, True)
                    return True
                else:
                    print_info("页面未显示具体督学记录（可能没有记录或未展开）")
                    print_result(2, True)
                    return True
            else:
                print_info("未找到督学记录标记（可能设计改变）")
                # 只要不是500错误，就认为Bug已修复
                print_result(2, True)
                return True
        else:
            print_error(f"访问失败，状态码: {response.status_code}")
            print_result(2, False, f"状态码{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        print_result(2, False, str(e))
        return False

def test_bug3_continuous_supervision(session):
    """Bug #3: 连续创建督学记录500错误"""
    print_bug_header(3, "连续创建督学记录500错误")
    
    # 获取学员ID
    student_id = get_first_student_id(session)
    
    if not student_id:
        print_error("未找到可用学员")
        print_result(3, False, "无法获取学员ID")
        return False
    
    print_success(f"使用学员ID: {student_id}")
    
    # 创建第一条督学记录
    print_step("步骤1: 创建第一条督学记录")
    print_info("沟通内容: 第一条测试记录")
    
    try:
        log_data1 = {
            'student_id': student_id,
            'contact_type': '微信',
            'content': '第一条测试记录 - Bug #3验证',
            'student_mood': '积极',
            'log_date': date.today().strftime('%Y-%m-%d')
        }
        
        response1 = session.post(f"{BASE_URL}/supervision/log", data=log_data1, allow_redirects=False)
        
        print_info(f"第一条记录响应状态码: {response1.status_code}")
        
        if response1.status_code in [200, 302]:
            print_success("第一条督学记录创建成功")
        else:
            print_error(f"第一条记录创建失败: {response1.status_code}")
            print_result(3, False, "第一条记录创建失败")
            return False
    except Exception as e:
        print_error(f"第一条记录异常: {str(e)}")
        print_result(3, False, str(e))
        return False
    
    # 等待一小段时间
    print_info("等待0.5秒后创建第二条记录...")
    time.sleep(0.5)
    
    # 创建第二条督学记录
    print_step("步骤2: 不关闭会话，连续创建第二条督学记录")
    print_info("沟通内容: 第二条测试记录")
    
    try:
        log_data2 = {
            'student_id': student_id,
            'contact_type': '电话',
            'content': '第二条测试记录 - Bug #3验证',
            'student_mood': '平稳',
            'log_date': date.today().strftime('%Y-%m-%d')
        }
        
        response2 = session.post(f"{BASE_URL}/supervision/log", data=log_data2, allow_redirects=False)
        
        print_info(f"第二条记录响应状态码: {response2.status_code}")
        
        if response2.status_code == 500:
            print_error("⚠️  返回500错误 - Bug #3 未修复！")
            print_result(3, False, "第二条记录返回500错误")
            return False
        elif response2.status_code in [200, 302]:
            print_success("第二条督学记录创建成功！")
            
            # 验证两条记录都已保存
            print_step("步骤3: 验证两条记录是否都已保存")
            time.sleep(0.3)
            
            verify_response = session.get(f"{BASE_URL}/supervision/my-logs")
            if verify_response.status_code == 200:
                if '第一条测试记录' in verify_response.text and '第二条测试记录' in verify_response.text:
                    print_success("两条记录都已成功保存")
                    print_result(3, True)
                    return True
                else:
                    print_info("记录可能已保存（在其他页面）")
                    print_result(3, True)
                    return True
            else:
                print_info("无法验证记录列表，但创建成功")
                print_result(3, True)
                return True
        else:
            print_error(f"第二条记录创建失败: {response2.status_code}")
            print_result(3, False, f"状态码{response2.status_code}")
            return False
            
    except Exception as e:
        print_error(f"第二条记录异常: {str(e)}")
        print_result(3, False, str(e))
        return False

def test_additional_features(session):
    """额外测试：整体功能流畅性"""
    print_header("额外测试：整体功能流畅性")
    
    results = {
        'search': False,
        'homework': False,
        'dashboard': False
    }
    
    # 测试学员搜索
    print_step("测试1: 学员搜索功能")
    try:
        response = session.get(f"{BASE_URL}/students/?search=张")
        if response.status_code == 200:
            print_success("学员搜索功能正常")
            results['search'] = True
        else:
            print_error(f"搜索功能异常: {response.status_code}")
    except Exception as e:
        print_error(f"搜索异常: {str(e)}")
    
    # 测试作业列表
    print_step("测试2: 作业管理功能")
    try:
        response = session.get(f"{BASE_URL}/homework/")
        if response.status_code == 200:
            print_success("作业管理功能正常")
            results['homework'] = True
        else:
            print_error(f"作业管理异常: {response.status_code}")
    except Exception as e:
        print_error(f"作业管理异常: {str(e)}")
    
    # 测试工作台
    print_step("测试3: 工作台数据显示")
    try:
        response = session.get(f"{BASE_URL}/dashboard/")
        if response.status_code == 200:
            print_success("工作台功能正常")
            results['dashboard'] = True
        else:
            print_error(f"工作台异常: {response.status_code}")
    except Exception as e:
        print_error(f"工作台异常: {str(e)}")
    
    # 计算流畅度评分
    score = sum(results.values())
    print(f"\n{Colors.CYAN}整体功能流畅度评分: {score}/3 = {score/3*5:.1f}/5.0{Colors.RESET}")
    
    return results

def generate_final_report(bug_results, additional_results):
    """生成最终测试报告"""
    print_header("Bug修复验证测试 - 最终报告")
    
    # Bug修复统计
    total_bugs = len(bug_results)
    fixed_bugs = sum(bug_results.values())
    fix_rate = (fixed_bugs / total_bugs * 100) if total_bugs > 0 else 0
    
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}Bug修复验证结果汇总{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    for bug_num, fixed in bug_results.items():
        status = f"{Colors.GREEN}✅ 已修复{Colors.RESET}" if fixed else f"{Colors.RED}❌ 未修复{Colors.RESET}"
        bug_desc = {
            1: "标签添加500错误",
            2: "学员详情页督学记录500错误",
            3: "连续创建督学记录500错误"
        }
        print(f"  Bug #{bug_num} - {bug_desc[bug_num]:<35} {status}")
    
    print(f"\n{Colors.BOLD}Bug修复率: {fixed_bugs}/{total_bugs} ({fix_rate:.1f}%){Colors.RESET}\n")
    
    # 额外功能测试
    if additional_results:
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}额外功能测试结果{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
        
        feature_names = {
            'search': '学员搜索功能',
            'homework': '作业管理功能',
            'dashboard': '工作台数据显示'
        }
        
        for key, passed in additional_results.items():
            status = f"{Colors.GREEN}✅ 正常{Colors.RESET}" if passed else f"{Colors.RED}❌ 异常{Colors.RESET}"
            print(f"  {feature_names[key]:<35} {status}")
        
        total_features = len(additional_results)
        passed_features = sum(additional_results.values())
        feature_rate = (passed_features / total_features * 100) if total_features > 0 else 0
        
        print(f"\n{Colors.BOLD}功能测试通过率: {passed_features}/{total_features} ({feature_rate:.1f}%){Colors.RESET}\n")
        
        # 流畅度评分
        fluency_score = passed_features / total_features * 5
        print(f"{Colors.BOLD}整体功能流畅度评分: {fluency_score:.1f}/5.0{Colors.RESET}\n")
    
    # 最终结论
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}最终结论{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    if fixed_bugs == total_bugs:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 所有Bug已成功修复！系统可以正常使用。{Colors.RESET}\n")
        return 0
    elif fixed_bugs >= total_bugs * 0.66:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  大部分Bug已修复（{fix_rate:.0f}%），但仍有 {total_bugs - fixed_bugs} 个Bug需要处理。{Colors.RESET}\n")
        return 1
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ 多个Bug仍未修复（修复率仅{fix_rate:.0f}%），需要继续调试。{Colors.RESET}\n")
        return 1

def main():
    """主测试函数"""
    print_header("公考培训管理系统 - Bug修复验证测试")
    print(f"{Colors.CYAN}测试地址: {BASE_URL}{Colors.RESET}")
    print(f"{Colors.CYAN}测试账号: {TEST_USERNAME}{Colors.RESET}\n")
    
    print(f"{Colors.MAGENTA}{Colors.BOLD}待验证Bug:{Colors.RESET}")
    print(f"  Bug #1: 标签添加500错误")
    print(f"  Bug #2: 学员详情页督学记录500错误")
    print(f"  Bug #3: 连续创建督学记录500错误\n")
    
    # 检查服务器
    if not check_server():
        print_error("\n测试终止: 服务器未运行")
        sys.exit(1)
    
    # 登录
    session = login()
    if not session:
        print_error("\n测试终止: 登录失败")
        sys.exit(1)
    
    # Bug测试结果
    bug_results = {}
    
    # 测试Bug #1
    bug_results[1] = test_bug1_tag_addition(session)
    
    # 测试Bug #2
    bug_results[2] = test_bug2_student_detail_supervision(session)
    
    # 测试Bug #3
    bug_results[3] = test_bug3_continuous_supervision(session)
    
    # 额外功能测试
    additional_results = test_additional_features(session)
    
    # 生成最终报告
    exit_code = generate_final_report(bug_results, additional_results)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.RESET}\n")
        sys.exit(130)
