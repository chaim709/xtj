"""
迁移工具 - 版本适配器
"""
from typing import Dict, List

CURRENT_VERSION = '1.0'


class VersionAdapter:
    """版本兼容适配器"""
    
    MIGRATIONS = {}
    
    @staticmethod
    def detect_version(data: Dict) -> str:
        meta = data.get('meta', {})
        return meta.get('version', '1.0')
    
    @staticmethod
    def get_current_version() -> str:
        return CURRENT_VERSION
    
    @staticmethod
    def is_compatible(version: str) -> bool:
        if version.startswith('1.'):
            return True
        return False
    
    @staticmethod
    def get_migration_path(from_version: str, to_version: str) -> List[str]:
        if from_version == to_version:
            return []
        return []
    
    @classmethod
    def migrate_data(cls, data: Dict, from_version: str, to_version: str) -> Dict:
        if from_version == to_version:
            return data
        if 'meta' in data:
            data['meta']['version'] = to_version
        return data
    
    @staticmethod
    def validate_data_structure(data: Dict) -> tuple:
        if 'meta' not in data:
            return False, '缺少meta字段'
        if 'data' not in data:
            return False, '缺少data字段'
        meta = data['meta']
        required_meta_fields = ['version', 'system', 'export_time', 'export_type']
        for field in required_meta_fields:
            if field not in meta:
                return False, f'meta中缺少{field}字段'
        return True, None
