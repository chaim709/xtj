"""JSON格式化器"""
import json
import os
from typing import Dict, Any
from app.migrate.utils import DateTimeEncoder


class JsonFormatter:
    """JSON格式处理器"""
    
    @staticmethod
    def serialize(data: Dict[str, Any]) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
    
    @staticmethod
    def deserialize(json_string: str) -> Dict[str, Any]:
        return json.loads(json_string)
    
    @staticmethod
    def save_to_file(data: Dict[str, Any], file_path: str) -> None:
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
    
    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def validate_file(file_path: str) -> tuple:
        if not os.path.exists(file_path):
            return False, f'文件不存在: {file_path}', None
        if not file_path.endswith('.json'):
            return False, '文件必须是.json格式', None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return True, None, data
        except json.JSONDecodeError as e:
            return False, f'JSON格式错误: {str(e)}', None
        except Exception as e:
            return False, f'读取文件失败: {str(e)}', None
