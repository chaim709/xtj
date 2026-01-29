"""
公考培训管理系统 - 认证模块自动化测试脚本

测试用例：
1.1 正常登录
1.2 错误密码
1.3 空用户名
1.4 登出功能

使用方法：
    python test_auth.py
"""
import requests
from requests.exceptions import ConnectionError, RequestException
import sys
from urllib.parse import urlparse

# 测试配置
BASE_URL = "http://localhost:5002"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"
WRONG_PASSWORD = "wrongpass"

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

def test_empty_username():
    """测试1.3: 空用户名"""
    print_header("测试用例 1.3: 空用户名验证")
    
    try:
        session = requests.Session()
        
        print_info("步骤1: 访问登录页面")
        session.get(f"{BASE_URL}/auth/login")
        
        print_info("步骤2: 提交空用户名")
        response = session.post(f"{BASE_URL}/auth/login", data={
            "username": "",
            "password": TEST_PASSWORD
        }, allow_redirects=False)
        
        print_info(f"响应状态码: {response.status_code}")
        
        # 检查是否留在登录页面（没有重定向）
        if response.status_code == 200:
            # 检查是否包含错误提示
            if '请输入用户名和密码' in response.text or 'danger' in response.text:
                print_success("测试通过: 空用户名被正确拦截，显示错误提示")
                return True
            else:
                print_error("测试失败: 未显示预期的错误提示")
                return False
        else:
            print_error(f"测试失败: 预期状态码200，实际{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        return False

def test_wrong_password():
    """测试1.2: 错误密码"""
    print_header("测试用例 1.2: 错误密码验证")
    
    try:
        session = requests.Session()
        
        print_info("步骤1: 访问登录页面")
        session.get(f"{BASE_URL}/auth/login")
        
        print_info(f"步骤2: 使用错误密码登录 (用户名: {TEST_USERNAME}, 密码: {WRONG_PASSWORD})")
        response = session.post(f"{BASE_URL}/auth/login", data={
            "username": TEST_USERNAME,
            "password": WRONG_PASSWORD
        }, allow_redirects=False)
        
        print_info(f"响应状态码: {response.status_code}")
        
        # 检查是否留在登录页面
        if response.status_code == 200:
            # 检查是否包含错误提示
            if '用户名或密码错误' in response.text or 'danger' in response.text:
                print_success("测试通过: 错误密码被正确拦截，显示错误提示")
                return True
            else:
                print_error("测试失败: 未显示预期的错误提示")
                print_info("响应内容片段:")
                print(response.text[:500])
                return False
        elif response.status_code == 302:
            print_error("测试失败: 错误密码却登录成功了（不应该重定向）")
            return False
        else:
            print_error(f"测试失败: 预期状态码200，实际{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        return False

def test_normal_login():
    """测试1.1: 正常登录"""
    print_header("测试用例 1.1: 正常登录")
    
    try:
        session = requests.Session()
        
        print_info("步骤1: 访问登录页面")
        session.get(f"{BASE_URL}/auth/login")
        
        print_info(f"步骤2: 使用正确凭据登录 (用户名: {TEST_USERNAME})")
        response = session.post(f"{BASE_URL}/auth/login", data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }, allow_redirects=False)
        
        print_info(f"响应状态码: {response.status_code}")
        
        # 检查是否重定向到工作台
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print_info(f"重定向目标: {location}")
            
            # 解析重定向URL
            if '/dashboard' in location or location.endswith('/dashboard/'):
                print_success("测试通过: 登录成功，正确跳转到工作台")
                
                # 验证session是否有效
                print_info("步骤3: 验证登录状态")
                dashboard_response = session.get(f"{BASE_URL}/dashboard/", allow_redirects=False)
                
                if dashboard_response.status_code == 200:
                    print_success("登录状态验证成功: 可以访问工作台")
                    return session  # 返回session供logout测试使用
                else:
                    print_error(f"登录状态验证失败: 工作台返回{dashboard_response.status_code}")
                    return None
            else:
                print_error(f"测试失败: 重定向到了错误的页面 {location}")
                return None
        elif response.status_code == 200:
            # 检查是否包含错误信息
            if 'danger' in response.text or '错误' in response.text:
                print_error("测试失败: 登录被拒绝")
                # 尝试提取错误信息
                if 'flash' in response.text or 'alert' in response.text:
                    print_info("页面包含错误提示，可能是账号不存在或密码错误")
            else:
                print_error("测试失败: 没有重定向，但也没有错误提示")
            return None
        else:
            print_error(f"测试失败: 预期状态码302，实际{response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_logout(session=None):
    """测试1.4: 登出功能"""
    print_header("测试用例 1.4: 登出功能")
    
    # 如果没有传入session，先登录
    if session is None:
        print_info("未提供已登录session，先执行登录")
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/auth/login", data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }, allow_redirects=True)
        
        if login_response.status_code != 200 or '/dashboard' not in login_response.url:
            print_error("登录失败，无法测试登出功能")
            return False
    
    try:
        print_info("步骤1: 点击登出按钮")
        response = session.get(f"{BASE_URL}/auth/logout", allow_redirects=False)
        
        print_info(f"响应状态码: {response.status_code}")
        
        # 检查是否重定向到登录页
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print_info(f"重定向目标: {location}")
            
            if '/login' in location or location.endswith('/auth/login'):
                print_success("测试通过: 登出成功，正确跳转到登录页")
                
                # 验证session是否已清除
                print_info("步骤2: 验证session已清除")
                dashboard_response = session.get(f"{BASE_URL}/dashboard/", allow_redirects=False)
                
                if dashboard_response.status_code == 302:
                    redirect_location = dashboard_response.headers.get('Location', '')
                    if '/login' in redirect_location:
                        print_success("Session验证成功: 已无法访问需要登录的页面")
                        return True
                    else:
                        print_error(f"Session验证失败: 重定向到了{redirect_location}")
                        return False
                else:
                    print_error(f"Session验证失败: 仍可访问工作台（状态码{dashboard_response.status_code}）")
                    return False
            else:
                print_error(f"测试失败: 重定向到了错误的页面 {location}")
                return False
        else:
            print_error(f"测试失败: 预期状态码302，实际{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print_header("公考培训管理系统 - 认证模块自动化测试")
    print(f"测试地址: {BASE_URL}")
    print(f"测试账号: {TEST_USERNAME} / {'*' * len(TEST_PASSWORD)}")
    
    # 检查服务器
    if not check_server():
        print_error("\n测试终止: 服务器未运行")
        sys.exit(1)
    
    # 执行测试
    results = {}
    
    # 测试1.3: 空用户名
    results['1.3_empty_username'] = test_empty_username()
    
    # 测试1.2: 错误密码
    results['1.2_wrong_password'] = test_wrong_password()
    
    # 测试1.1: 正常登录（返回session）
    login_session = test_normal_login()
    results['1.1_normal_login'] = (login_session is not None)
    
    # 测试1.4: 登出（使用登录session）
    results['1.4_logout'] = test_logout(login_session)
    
    # 汇总结果
    print_header("测试结果汇总")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\n{'测试用例':<30} {'结果':<10}")
    print("-" * 40)
    print(f"{'1.3 空用户名验证':<30} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['1.3_empty_username'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print(f"{'1.2 错误密码验证':<30} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['1.2_wrong_password'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print(f"{'1.1 正常登录':<30} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['1.1_normal_login'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print(f"{'1.4 登出功能':<30} {Colors.GREEN + '✅ 通过' + Colors.RESET if results['1.4_logout'] else Colors.RED + '❌ 失败' + Colors.RESET}")
    print("-" * 40)
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
