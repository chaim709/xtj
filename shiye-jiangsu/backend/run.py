"""
启动文件 - 安徽事业单位智能选岗系统
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app import create_app

# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'development'))


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5002))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
