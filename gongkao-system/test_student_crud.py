"""
公考培训管理系统 - 学员CRUD自动化测试脚本

测试用例：
2.1.1 新增学员
2.1.2 必填验证
2.1.3 查看详情
2.1.4 编辑学员

使用方法：
    python test_student_crud.py
"""
import requests
from requests.exceptions import ConnectionError, RequestException
import sys
from urllib.parse import urlparse
import re

# 测试配置
BASE_URL = "http://localhost:5002"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# 测试数据
TEST_STUDENT_NAME = "测试学员01"
TEST_STUDENT_PHONE = "13800000001"
TEST_STUDENT_PHONE_UPDATED = "13800000099"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
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

def login_and_get_session():
    """登录并返回session"""
    print_info("正在登录系统...")
    
    session = requests.Session()
    
    # 访问登录页
    session.get(f"{BASE_URL}/auth/login")
    
    # 提交登录表单
    response = session.post(f"{BASE_URL}/auth/login", data={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }, allow_redirects=True)
    
    if response.status_code == 200 and '/dashboard' in response.url:
        print_success(f"登录成功 (用户: {TEST_USERNAME})")
        return session
    else:
        print_error("登录失败")
        return None

def extract_student_id_from_url(url):
    """从URL中提取学员ID"""
    # URL格式: /students/123 或 /students/123/edit
    match = re.search(r'/students/(\d+)', url)
    if match:
        return int(match.group(1))
    return None

def test_create_student(session):
    """测试2.1.1: 新增学员"""
    print_header("测试用例 2.1.1: 新增学员")
    
    try:
        print_info("步骤1: 访问学员创建页面")
        response = session.get(f"{BASE_URL}/students/create")
        
        if response.status_code != 200:
            print_error(f"访问创建页面失败，状态码: {response.status_code}")
            return None
        
        print_success("成功访问创建页面")
        
        print_info(f"步骤2: 填写学员信息")
        print_info(f"  - 姓名: {TEST_STUDENT_NAME}")
        print_info(f"  - 电话: {TEST_STUDENT_PHONE}")
        print_info(f"  - 班次: 国考笔试班")
        print_info(f"  - 报考类型: 国考")
        
        # 提交表单
        form_data = {
            'name': TEST_STUDENT_NAME,
            'phone': TEST_STUDENT_PHONE,
            'class_name': '国考笔试班',
            'exam_type': '国考',
            'wechat': '',
            'target_position': '',
            'education': '',
            'remarks': '自动化测试创建的学员'
        }
        
        response = session.post(
            f"{BASE_URL}/students/create",
            data=form_data,
            allow_redirects=True
        )
        
        print_info(f"响应状态码: {response.status_code}")
        print_info(f"当前URL: {response.url}")
        
        # 检查是否跳转到详情页
        if response.status_code == 200:
            # 检查是否包含成功消息
            if '创建成功' in response.text or TEST_STUDENT_NAME in response.text:
                print_success("测试通过: 学员创建成功")
                
                # 从URL中提取学员ID
                student_id = extract_student_id_from_url(response.url)
                if student_id:
                    print_info(f"创建的学员ID: {student_id}")
                    return student_id
                else:
                    print_info("无法从URL提取学员ID，尝试其他方式")
                    return True
            else:
                print_error("测试失败: 未找到成功标识")
                if 'danger' in response.text or '错误' in response.text:
                    print_info("页面包含错误信息")
                return None
        else:
            print_error(f"测试失败: 预期状态码200，实际{response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_required_validation(session):
    """测试2.1.2: 必填验证"""
    print_header("测试用例 2.1.2: 必填验证")
    
    try:
        print_info("步骤1: 访问学员创建页面")
        response = session.get(f"{BASE_URL}/students/create")
        
        if response.status_code != 200:
            print_error(f"访问创建页面失败，状态码: {response.status_code}")
            return False
        
        print_info("步骤2: 不填姓名，直接提交表单")
        
        # 提交空姓名的表单
        form_data = {
            'name': '',  # 姓名为空
            'phone': TEST_STUDENT_PHONE,
            'class_name': '国考笔试班',
            'exam_type': '国考'
        }
        
        response = session.post(
            f"{BASE_URL}/students/create",
            data=form_data,
            allow_redirects=False
        )
        
        print_info(f"响应状态码: {response.status_code}")
        
        # 检查是否留在创建页面并显示错误
        if response.status_code == 200:
            # 检查是否包含错误提示
            if '姓名不能为空' in response.text or 'danger' in response.text:
                print_success("测试通过: 必填验证生效，显示错误提示")
                return True
            else:
                print_error("测试失败: 未显示预期的错误提示")
                return False
        elif response.status_code == 302:
            print_error("测试失败: 空姓名却通过了验证（不应该重定向）")
            return False
        else:
            print_error(f"测试失败: 预期状态码200，实际{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        return False

def test_view_detail(session, student_id=None):
    """测试2.1.3: 查看详情"""
    print_header("测试用例 2.1.3: 查看详情")
    
    try:
        # 如果没有传入student_id，从列表页查找
        if student_id is None:
            print_info("步骤1: 从学员列表查找刚创建的学员")
            response = session.get(f"{BASE_URL}/students/")
            
            if response.status_code != 200:
                print_error(f"访问列表页失败，状态码: {response.status_code}")
                return None
            
            # 在页面中查找学员链接
            # 格式: <a href="/students/123">测试学员01</a>
            pattern = rf'<a[^>]*href="/students/(\d+)"[^>]*>{TEST_STUDENT_NAME}</a>'
            match = re.search(pattern, response.text)
            
            if match:
                student_id = int(match.group(1))
                print_success(f"找到学员: {TEST_STUDENT_NAME}, ID: {student_id}")
            else:
                print_error(f"在列表中未找到学员: {TEST_STUDENT_NAME}")
                return None
        else:
            print_info(f"使用已知的学员ID: {student_id}")
        
        print_info(f"步骤2: 访问学员详情页")
        response = session.get(f"{BASE_URL}/students/{student_id}")
        
        print_info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查详情页是否包含学员信息
            if TEST_STUDENT_NAME in response.text and TEST_STUDENT_PHONE in response.text:
                print_success("测试通过: 详情页正常显示学员信息")
                print_info(f"  - 学员姓名: {TEST_STUDENT_NAME} ✓")
                print_info(f"  - 联系电话: {TEST_STUDENT_PHONE} ✓")
                return student_id
            else:
                print_error("测试失败: 详情页未正确显示学员信息")
                if TEST_STUDENT_NAME not in response.text:
                    print_info("  - 姓名未显示")
                if TEST_STUDENT_PHONE not in response.text:
                    print_info("  - 电话未显示")
                return None
        else:
            print_error(f"测试失败: 预期状态码200，实际{response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        return None

def test_edit_student(session, student_id):
    """测试2.1.4: 编辑学员"""
    print_header("测试用例 2.1.4: 编辑学员")
    
    try:
        print_info(f"步骤1: 访问学员编辑页面 (ID: {student_id})")
        response = session.get(f"{BASE_URL}/students/{student_id}/edit")
        
        if response.status_code != 200:
            print_error(f"访问编辑页面失败，状态码: {response.status_code}")
            return False
        
        print_success("成功访问编辑页面")
        
        print_info(f"步骤2: 修改学员电话")
        print_info(f"  - 原电话: {TEST_STUDENT_PHONE}")
        print_info(f"  - 新电话: {TEST_STUDENT_PHONE_UPDATED}")
        
        # 提交更新表单
        form_data = {
            'name': TEST_STUDENT_NAME,
            'phone': TEST_STUDENT_PHONE_UPDATED,  # 修改电话
            'class_name': '国考笔试班',
            'exam_type': '国考',
            'wechat': '',
            'target_position': '',
            'education': '',
            'remarks': '自动化测试更新的学员'
        }
        
        response = session.post(
            f"{BASE_URL}/students/{student_id}/edit",
            data=form_data,
            allow_redirects=True
        )
        
        print_info(f"响应状态码: {response.status_code}")
        print_info(f"当前URL: {response.url}")
        
        if response.status_code == 200:
            # 检查是否更新成功
            if '更新成功' in response.text or TEST_STUDENT_PHONE_UPDATED in response.text:
                print_success("测试通过: 学员信息更新成功")
                
                # 验证更新后的数据
                print_info("步骤3: 验证更新后的数据")
                if TEST_STUDENT_PHONE_UPDATED in response.text:
                    print_success(f"  - 新电话 {TEST_STUDENT_PHONE_UPDATED} 已显示 ✓")
                else:
                    print_error(f"  - 新电话 {TEST_STUDENT_PHONE_UPDATED} 未显示")
                    return False
                
                return True
            else:
                print_error("测试失败: 未找到更新成功标识")
                if 'danger' in response.text or '错误' in response.text:
                    print_info("页面包含错误信息")
                return False
        else:
            print_error(f"测试失败: 预期状态码200，实际{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data(session, student_id):
    """清理测试数据（可选）"""
    print_header("清理测试数据")
    
    try:
        print_info(f"删除测试学员 (ID: {student_id})")
        
        # 注意：删除需要管理员权限
        response = session.post(
            f"{BASE_URL}/students/{student_id}/delete",
            allow_redirects=True
        )
        
        if response.status_code == 200:
            if '已删除' in response.text or 'students' in response.url:
                print_success("测试数据已清理")
                return True
            else:
                print_info("无法删除测试数据（可能需要管理员权限）")
                return False
        else:
            print_info("无法删除测试数据")
            return False
            
    except Exception as e:
        print_info(f"清理失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print_header("公考培训管理系统 - 学员CRUD自动化测试")
    print(f"测试地址: {BASE_URL}")
    print(f"测试账号: {TEST_USERNAME} / {'*' * len(TEST_PASSWORD)}")
    
    # 检查服务器
    if not check_server():
        print_error("\n测试终止: 服务器未运行")
        sys.exit(1)
    
    # 登录系统
    session = login_and_get_session()
    if not session:
        print_error("\n测试终止: 登录失败")
        sys.exit(1)
    
    # 执行测试
    results = {}
    student_id = None
    
    # 测试2.1.2: 必填验证（先测试，避免干扰）
    results['2.1.2_required_validation'] = test_required_validation(session)
    
    # 测试2.1.1: 新增学员
    student_id = test_create_student(session)
    results['2.1.1_create_student'] = (student_id is not None)
    
    # 如果创建成功，继续后续测试
    if student_id:
        # 测试2.1.3: 查看详情
        verified_id = test_view_detail(session, student_id)
        results['2.1.3_view_detail'] = (verified_id is not None)
        
        # 测试2.1.4: 编辑学员
        results['2.1.4_edit_student'] = test_edit_student(session, student_id)
        
        # 询问是否清理测试数据
        print_info(f"\n测试学员ID: {student_id}")
        print_info("测试完成后，测试数据将保留在系统中")
        print_info("如需清理，可以手动删除或运行清理函数")
        
        # 可选：自动清理（取消注释以启用）
        # cleanup_test_data(session, student_id)
    else:
        print_error("创建学员失败，跳过后续测试")
        results['2.1.3_view_detail'] = False
        results['2.1.4_edit_student'] = False
    
    # 汇总结果
    print_header("测试结果汇总")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\n{'测试用例':<35} {'结果':<10}")
    print("-" * 45)
    print(f"{'2.1.1 新增学员':<35} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['2.1.1_create_student'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print(f"{'2.1.2 必填验证':<35} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['2.1.2_required_validation'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print(f"{'2.1.3 查看详情':<35} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['2.1.3_view_detail'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print(f"{'2.1.4 编辑学员':<35} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['2.1.4_edit_student'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print("-" * 45)
    print(f"\n总计: {total} 个测试")
    print(f"{Colors.GREEN}通过: {passed}{Colors.RESET}")
    print(f"{Colors.RED}失败: {failed}{Colors.RESET}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  有 {failed} 个测试失败{Colors.RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.RESET}\n")
        sys.exit(130)
