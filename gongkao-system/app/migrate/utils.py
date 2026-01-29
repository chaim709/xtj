"""
迁移工具 - 通用工具函数
"""
import os
import json
import hashlib
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List


class DateTimeEncoder(json.JSONEncoder):
    """JSON编码器，支持datetime和date类型"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def model_to_dict(model_instance, exclude_fields: List[str] = None) -> Dict:
    """将SQLAlchemy模型实例转换为字典"""
    if exclude_fields is None:
        exclude_fields = []
    
    result = {}
    for column in model_instance.__table__.columns:
        if column.name not in exclude_fields:
            value = getattr(model_instance, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, date):
                value = value.isoformat()
            result[column.name] = value
    
    return result


def calculate_checksum(data: Dict) -> str:
    """计算数据的校验和"""
    json_str = json.dumps(data, sort_keys=True, cls=DateTimeEncoder)
    return hashlib.md5(json_str.encode()).hexdigest()


def ensure_dir(path: str) -> None:
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path)


def get_backup_dir() -> str:
    """获取备份目录路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backup_dir = os.path.join(base_dir, 'backups')
    ensure_dir(backup_dir)
    return backup_dir


def generate_backup_filename(format_type: str, export_type: str = 'full') -> str:
    """生成备份文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    extension = 'json' if format_type == 'json' else 'xlsx'
    return f'duxue_backup_{export_type}_{timestamp}.{extension}'


def parse_datetime(value: str) -> datetime:
    """解析ISO格式的日期时间字符串"""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return None


# 模块依赖顺序
IMPORT_ORDER = [
    'users',
    'teachers',
    'subjects',
    'projects',
    'packages',
    'class_types',
    'class_batches',
    'schedules',
    'schedule_change_logs',
    'course_recordings',
    'weakness_tags',
    'module_categories',
    'students',
    'student_batches',
    'supervision_logs',
    'homework_tasks',
    'homework_submissions',
    'attendances',
    'study_plans',
    'plan_goals',
    'plan_tasks',
    'plan_progresses',
]

# 模块名称映射
MODULE_NAMES = {
    'users': '用户',
    'teachers': '教师',
    'subjects': '科目',
    'projects': '项目',
    'packages': '套餐',
    'class_types': '班型',
    'class_batches': '班次',
    'schedules': '课表',
    'schedule_change_logs': '调课记录',
    'course_recordings': '课程录播',
    'weakness_tags': '薄弱标签',
    'module_categories': '题型分类',
    'students': '学员',
    'student_batches': '学员班次',
    'supervision_logs': '督学日志',
    'homework_tasks': '作业任务',
    'homework_submissions': '作业提交',
    'attendances': '考勤记录',
    'study_plans': '学习计划',
    'plan_goals': '计划目标',
    'plan_tasks': '计划任务',
    'plan_progresses': '计划进度',
}
