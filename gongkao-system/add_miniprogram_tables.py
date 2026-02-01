# -*- coding: utf-8 -*-
"""
小程序相关数据库迁移脚本

扩展students表，添加微信相关字段和打卡统计字段
创建checkin_records表记录打卡历史
创建student_messages表存储学员消息

执行方式：
cd gongkao-system
source venv/bin/activate
python add_miniprogram_tables.py
"""
import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dev.db')


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def check_column_exists(cursor, table, column):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def check_table_exists(cursor, table):
    """检查表是否存在"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


def migrate():
    """执行迁移"""
    print("=" * 50)
    print("小程序数据库迁移")
    print("=" * 50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # ========================================
        # 1. 扩展 students 表
        # ========================================
        print("\n[1/4] 扩展 students 表...")
        
        # 添加微信openid字段
        if not check_column_exists(cursor, 'students', 'wx_openid'):
            cursor.execute('''
                ALTER TABLE students ADD COLUMN wx_openid VARCHAR(64)
            ''')
            print("  ✓ 添加 wx_openid 字段")
        else:
            print("  - wx_openid 字段已存在，跳过")
        
        # 添加微信unionid字段
        if not check_column_exists(cursor, 'students', 'wx_unionid'):
            cursor.execute('''
                ALTER TABLE students ADD COLUMN wx_unionid VARCHAR(64)
            ''')
            print("  ✓ 添加 wx_unionid 字段")
        else:
            print("  - wx_unionid 字段已存在，跳过")
        
        # 添加微信头像字段
        if not check_column_exists(cursor, 'students', 'wx_avatar_url'):
            cursor.execute('''
                ALTER TABLE students ADD COLUMN wx_avatar_url VARCHAR(500)
            ''')
            print("  ✓ 添加 wx_avatar_url 字段")
        else:
            print("  - wx_avatar_url 字段已存在，跳过")
        
        # 添加微信昵称字段
        if not check_column_exists(cursor, 'students', 'wx_nickname'):
            cursor.execute('''
                ALTER TABLE students ADD COLUMN wx_nickname VARCHAR(100)
            ''')
            print("  ✓ 添加 wx_nickname 字段")
        else:
            print("  - wx_nickname 字段已存在，跳过")
        
        # 添加最后打卡日期字段
        if not check_column_exists(cursor, 'students', 'last_checkin_date'):
            cursor.execute('''
                ALTER TABLE students ADD COLUMN last_checkin_date DATE
            ''')
            print("  ✓ 添加 last_checkin_date 字段")
        else:
            print("  - last_checkin_date 字段已存在，跳过")
        
        # 添加累计打卡天数字段
        if not check_column_exists(cursor, 'students', 'total_checkin_days'):
            cursor.execute('''
                ALTER TABLE students ADD COLUMN total_checkin_days INTEGER DEFAULT 0
            ''')
            print("  ✓ 添加 total_checkin_days 字段")
        else:
            print("  - total_checkin_days 字段已存在，跳过")
        
        # 添加连续打卡天数字段
        if not check_column_exists(cursor, 'students', 'consecutive_checkin_days'):
            cursor.execute('''
                ALTER TABLE students ADD COLUMN consecutive_checkin_days INTEGER DEFAULT 0
            ''')
            print("  ✓ 添加 consecutive_checkin_days 字段")
        else:
            print("  - consecutive_checkin_days 字段已存在，跳过")
        
        # ========================================
        # 2. 创建 checkin_records 表
        # ========================================
        print("\n[2/4] 创建 checkin_records 表...")
        
        if not check_table_exists(cursor, 'checkin_records'):
            cursor.execute('''
                CREATE TABLE checkin_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    checkin_date DATE NOT NULL,
                    checkin_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    study_minutes INTEGER DEFAULT 0,
                    note TEXT,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    UNIQUE(student_id, checkin_date)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX idx_checkin_student ON checkin_records(student_id)
            ''')
            cursor.execute('''
                CREATE INDEX idx_checkin_date ON checkin_records(checkin_date)
            ''')
            
            print("  ✓ 创建 checkin_records 表")
            print("  ✓ 创建索引 idx_checkin_student")
            print("  ✓ 创建索引 idx_checkin_date")
        else:
            print("  - checkin_records 表已存在，跳过")
        
        # ========================================
        # 3. 创建 student_messages 表
        # ========================================
        print("\n[3/4] 创建 student_messages 表...")
        
        if not check_table_exists(cursor, 'student_messages'):
            cursor.execute('''
                CREATE TABLE student_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    message_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT,
                    source_type VARCHAR(50),
                    source_id INTEGER,
                    is_read BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    read_at DATETIME,
                    FOREIGN KEY (student_id) REFERENCES students(id)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX idx_message_student ON student_messages(student_id)
            ''')
            cursor.execute('''
                CREATE INDEX idx_message_read ON student_messages(is_read)
            ''')
            cursor.execute('''
                CREATE INDEX idx_message_created ON student_messages(created_at)
            ''')
            
            print("  ✓ 创建 student_messages 表")
            print("  ✓ 创建索引 idx_message_student")
            print("  ✓ 创建索引 idx_message_read")
            print("  ✓ 创建索引 idx_message_created")
        else:
            print("  - student_messages 表已存在，跳过")
        
        # ========================================
        # 4. 创建 wx_subscribe_templates 表
        # ========================================
        print("\n[4/4] 创建 wx_subscribe_templates 表...")
        
        if not check_table_exists(cursor, 'wx_subscribe_templates'):
            cursor.execute('''
                CREATE TABLE wx_subscribe_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id VARCHAR(100) NOT NULL,
                    template_type VARCHAR(50) NOT NULL,
                    title VARCHAR(100),
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            print("  ✓ 创建 wx_subscribe_templates 表")
        else:
            print("  - wx_subscribe_templates 表已存在，跳过")
        
        # 提交事务
        conn.commit()
        
        print("\n" + "=" * 50)
        print("迁移完成！")
        print("=" * 50)
        
        # 验证结果
        print("\n验证迁移结果:")
        
        # 验证students表字段
        cursor.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in cursor.fetchall()]
        wx_fields = ['wx_openid', 'wx_unionid', 'wx_avatar_url', 'wx_nickname', 
                     'last_checkin_date', 'total_checkin_days', 'consecutive_checkin_days']
        for field in wx_fields:
            status = "✓" if field in columns else "✗"
            print(f"  {status} students.{field}")
        
        # 验证新表
        for table in ['checkin_records', 'student_messages', 'wx_subscribe_templates']:
            status = "✓" if check_table_exists(cursor, table) else "✗"
            print(f"  {status} {table} 表")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ 迁移失败: {e}")
        raise
    finally:
        conn.close()


def rollback():
    """回滚迁移（仅删除新建的表，不删除扩展的字段）"""
    print("=" * 50)
    print("回滚小程序数据库迁移")
    print("=" * 50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 删除新建的表
        tables = ['checkin_records', 'student_messages', 'wx_subscribe_templates']
        
        for table in tables:
            if check_table_exists(cursor, table):
                cursor.execute(f"DROP TABLE {table}")
                print(f"  ✓ 删除 {table} 表")
            else:
                print(f"  - {table} 表不存在，跳过")
        
        conn.commit()
        
        print("\n注意: students表的扩展字段未删除（SQLite不支持DROP COLUMN）")
        print("回滚完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ 回滚失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
