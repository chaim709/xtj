"""
文件扫描器 - 扫描所有Excel文件（支持去重）
"""
import os
import glob
import hashlib
from typing import List, Dict, Set


class FileScanner:
    """Excel文件扫描器（支持基于内容的去重）"""
    
    @staticmethod
    def scan_files(root_path: str, deduplicate: bool = True, exclude_patterns: List[str] = None) -> List[Dict]:
        """
        扫描所有Excel文件（支持去重和排除）
        
        Args:
            root_path: 根目录路径
            deduplicate: 是否启用基于内容的去重
            exclude_patterns: 要排除的文件名模式列表（如 ['整合后总表', '_converted']）
            
        Returns:
            文件信息列表
        """
        files = []
        seen_hashes: Set[str] = set()  # 用于存储已见过的文件hash
        excluded_files = []  # 被排除的文件列表
        duplicate_files = []  # 重复的文件列表
        
        if exclude_patterns is None:
            exclude_patterns = ['整合后总表', '_converted', 'backup']
        
        # 1. 扫描根目录（省级文件）
        provincial_files = glob.glob(os.path.join(root_path, '*.xls*'))
        for file_path in provincial_files:
            filename = os.path.basename(file_path)
            
            # 检查是否应该排除
            if any(pattern in filename for pattern in exclude_patterns):
                excluded_files.append({'path': file_path, 'reason': 'excluded_pattern'})
                continue
            
            file_info = {
                'path': file_path,
                'filename': filename,
                'city': '省直',
                'is_provincial': True,
                'size': os.path.getsize(file_path)
            }
            
            # 去重检查
            if deduplicate:
                file_hash = FileScanner.calculate_file_hash(file_path)
                file_info['hash'] = file_hash
                
                if file_hash in seen_hashes:
                    duplicate_files.append(file_info)
                    continue
                seen_hashes.add(file_hash)
            
            files.append(file_info)
        
        # 2. 扫描子目录（地市文件）
        city_dirs = glob.glob(os.path.join(root_path, '*岗位表'))
        for city_dir in city_dirs:
            if not os.path.isdir(city_dir):
                continue
            
            city_name = FileScanner.extract_city_name(os.path.basename(city_dir))
            
            # 扫描该地市目录下的所有Excel文件
            city_files = glob.glob(os.path.join(city_dir, '*.xls*'))
            for file_path in city_files:
                filename = os.path.basename(file_path)
                
                # 检查是否应该排除
                if any(pattern in filename for pattern in exclude_patterns):
                    excluded_files.append({'path': file_path, 'reason': 'excluded_pattern'})
                    continue
                
                file_info = {
                    'path': file_path,
                    'filename': filename,
                    'city': city_name,
                    'is_provincial': False,
                    'size': os.path.getsize(file_path)
                }
                
                # 去重检查
                if deduplicate:
                    file_hash = FileScanner.calculate_file_hash(file_path)
                    file_info['hash'] = file_hash
                    
                    if file_hash in seen_hashes:
                        duplicate_files.append(file_info)
                        continue
                    seen_hashes.add(file_hash)
                
                files.append(file_info)
        
        # 记录去重信息
        return files, {
            'excluded': excluded_files,
            'duplicates': duplicate_files
        }
    
    @staticmethod
    def calculate_file_hash(file_path: str, chunk_size: int = 8192) -> str:
        """
        计算文件的MD5 hash值（用于去重）
        
        Args:
            file_path: 文件路径
            chunk_size: 读取块大小
            
        Returns:
            文件的MD5 hash值
        """
        md5_hash = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            # 如果无法读取文件，返回文件路径的hash
            return hashlib.md5(file_path.encode()).hexdigest()
    
    @staticmethod
    def extract_city_name(folder_name: str) -> str:
        """
        从文件夹名提取城市名
        
        Args:
            folder_name: 文件夹名（如："合肥市岗位表"或"池州岗位表"）
            
        Returns:
            城市名（如："合肥市"）
        """
        # 移除"岗位表"后缀
        city_name = folder_name.replace('岗位表', '').strip()
        
        # 移除可能的"市"字（防止重复）
        city_name = city_name.replace('市', '').strip()
        
        # 添加"市"后缀（标准化）
        if city_name:
            city_name = city_name + '市'
        
        return city_name
    
    @staticmethod
    def print_summary(files: List[Dict]):
        """打印扫描摘要"""
        provincial = [f for f in files if f['is_provincial']]
        city_files = [f for f in files if not f['is_provincial']]
        
        print(f"扫描完成！")
        print(f"  省级文件: {len(provincial)} 个")
        print(f"  地市文件: {len(city_files)} 个")
        print(f"  总计: {len(files)} 个")
        
        # 按城市统计
        city_count = {}
        for file_info in files:
            city = file_info['city']
            city_count[city] = city_count.get(city, 0) + 1
        
        print(f"\n按城市分布:")
        for city, count in sorted(city_count.items()):
            print(f"  {city}: {count} 个文件")


if __name__ == '__main__':
    # 测试代码
    root_path = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位"
    
    scanner = FileScanner()
    files = scanner.scan_files(root_path)
    scanner.print_summary(files)
    
    # 显示前5个文件
    print(f"\n前5个文件示例:")
    for file_info in files[:5]:
        print(f"  - {file_info['filename']}")
        print(f"    城市: {file_info['city']}, 省级: {file_info['is_provincial']}")
