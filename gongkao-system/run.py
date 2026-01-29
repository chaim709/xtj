"""
启动文件 - 公考培训机构管理系统
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app import create_app, db

# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.cli.command('init-db')
def init_db():
    """初始化数据库"""
    db.create_all()
    print('数据库初始化完成！')


@app.cli.command('create-admin')
def create_admin():
    """创建管理员账号"""
    from app.models.user import User
    from werkzeug.security import generate_password_hash
    
    # 检查是否已存在管理员
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('管理员账号已存在！')
        return
    
    # 创建管理员
    admin = User(
        username='admin',
        password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
        real_name='系统管理员',
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print('管理员账号创建成功！')
    print('用户名: admin')
    print('密码: admin123')


@app.cli.command('import-excel')
def import_excel():
    """从Excel导入历史数据"""
    import os
    from app.services.import_service import ImportService
    
    # Excel文件路径
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        '公考培训机构管理系统',
        '泗洪校区.xlsx'
    )
    
    if not os.path.exists(excel_path):
        print(f'文件不存在: {excel_path}')
        return
    
    print(f'开始导入: {excel_path}')
    
    # 导入教师
    print('\n1. 导入教师数据...')
    result = ImportService.import_teachers_from_excel(excel_path)
    if result['success']:
        print(f"   教师: 总计{result['total']}条，导入{result['imported']}条，跳过{result['skipped']}条")
    else:
        print(f"   导入失败: {result['message']}")
    
    # 获取第一个督学人员ID
    from app.models.user import User
    supervisor = User.query.filter_by(role='supervisor').first()
    supervisor_id = supervisor.id if supervisor else None
    
    # 导入学员
    print('\n2. 导入学员数据...')
    result = ImportService.import_students_from_excel(excel_path, supervisor_id)
    if result['success']:
        print(f"   学员: 总计{result['total']}条，导入{result['imported']}条，跳过{result['skipped']}条")
        if result.get('errors'):
            print(f"   错误: {result['errors'][:3]}")
    else:
        print(f"   导入失败: {result['message']}")
    
    # 导入题型分类
    print('\n3. 导入题型分类...')
    result = ImportService.import_module_categories_from_excel(excel_path)
    if result['success']:
        print(f"   题型: 总计{result['total']}条，导入{result['imported']}条")
    else:
        print(f"   导入失败: {result['message']}")
    
    print('\n导入完成！')


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
