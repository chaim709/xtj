#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动脚本"""
import os
from app import create_app, db

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 确保目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    app.run(host='0.0.0.0', port=5005, debug=True)
