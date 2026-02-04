#!/usr/bin/env python3
"""
安徽省事业单位岗位数据导入工具

功能：
1. 扫描71个Excel文件
2. 解析和标准化数据
3. 生成整合总表
4. 导入到Position数据库

使用方法：
    python import_shiye_positions.py
"""
import os
import sys
from datetime import datetime
from typing import List, Dict

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_scanner import FileScanner
from excel_parser import ExcelParser
from field_mapper import FieldMapper
from data_normalizer import DataNormalizer
from data_validator import DataValidator
from summary_generator import SummaryGenerator
from database_importer import DatabaseImporter


class ImportLogger:
    """导入日志记录器"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.entries = []
        
        # 清空旧日志
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"安徽省事业单位岗位导入日志\n")
            f.write(f"开始时间: {datetime.now().isoformat()}\n")
            f.write("="*60 + "\n\n")
    
    def log(self, level: str, message: str, details: str = None):
        """记录日志"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'details': details
        }
        self.entries.append(entry)
        
        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{entry['timestamp']}] {level}: {message}\n")
            if details:
                f.write(f"  详情: {details}\n")
        
        # 同时打印到控制台（ERROR级别）
        if level == 'ERROR':
            print(f"  ✗ {message}")


def process_single_file(file_info: Dict, config_path: str, logger: ImportLogger) -> Dict:
    """
    处理单个Excel文件
    
    Args:
        file_info: 文件信息字典
        config_path: 映射配置文件路径
        logger: 日志记录器
        
    Returns:
        处理结果字典
    """
    file_path = file_info['path']
    filename = file_info['filename']
    city = file_info['city']
    is_provincial = file_info['is_provincial']
    
    result = {
        'filename': filename,
        'city': city,
        'success': False,
        'data': None,
        'rows': 0,
        'error': None
    }
    
    try:
        # 1. 解析Excel
        parser = ExcelParser()
        df, parse_result = parser.parse_excel(file_path)
        
        if not parse_result.success:
            result['error'] = f"解析失败: {parse_result.error}"
            logger.log('ERROR', f"{filename} - 解析失败", parse_result.error)
            return result
        
        # 2. 字段映射
        mapper = FieldMapper(config_path)
        mapped_df, mapping_log = mapper.map_fields(df)
        
        # 3. 数据标准化
        normalizer = DataNormalizer()
        normalized_df = normalizer.normalize(mapped_df, city, is_provincial)
        
        # 4. 数据验证
        validator = DataValidator()
        validation_results = validator.validate_dataframe(normalized_df)
        
        # 只保留有效数据
        valid_df = validator.get_valid_rows(normalized_df)
        
        if len(valid_df) == 0:
            result['error'] = "没有有效数据"
            logger.log('WARNING', f"{filename} - 没有有效数据")
            return result
        
        # 成功
        result['success'] = True
        result['data'] = valid_df
        result['rows'] = len(valid_df)
        result['validation'] = validation_results
        
        logger.log('INFO', f"{filename} - 处理成功，有效数据 {len(valid_df)} 行")
        
        return result
    
    except Exception as e:
        result['error'] = str(e)
        logger.log('ERROR', f"{filename} - 处理异常", str(e))
        return result


def main():
    """主函数"""
    print("="*60)
    print("安徽省事业单位岗位数据导入工具")
    print("="*60)
    
    # 配置路径
    root_path = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位"
    config_path = "/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_field_mapping.json"
    log_file = "/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_import_log.txt"
    error_file = "/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_import_errors.txt"
    
    # 初始化日志
    logger = ImportLogger(log_file)
    
    # ========== 第1步：扫描文件 ==========
    print("\n[1/7] 扫描Excel文件...")
    scanner = FileScanner()
    files = scanner.scan_files(root_path)
    print(f"   找到 {len(files)} 个文件")
    logger.log('INFO', f"扫描完成，找到 {len(files)} 个文件")
    
    # ========== 第2步：解析和处理文件 ==========
    print("\n[2/7] 解析和处理Excel文件...")
    all_data = []
    success_count = 0
    failed_count = 0
    failed_files = []
    
    for idx, file_info in enumerate(files, 1):
        print(f"   处理 {idx}/{len(files)}: {file_info['filename']}")
        
        result = process_single_file(file_info, config_path, logger)
        
        if result['success']:
            all_data.append(result['data'])
            success_count += 1
        else:
            failed_count += 1
            failed_files.append({
                'filename': result['filename'],
                'error': result['error']
            })
    
    print(f"\n   处理完成:")
    print(f"     成功: {success_count} 个文件")
    print(f"     失败: {failed_count} 个文件")
    print(f"     成功率: {success_count/len(files)*100:.1f}%")
    
    if failed_count > 0:
        print(f"\n   失败的文件:")
        for failed in failed_files[:5]:  # 只显示前5个
            print(f"     - {failed['filename']}: {failed['error']}")
        
        # 写入错误报告
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write("导入失败的文件列表\n")
            f.write("="*60 + "\n\n")
            for failed in failed_files:
                f.write(f"文件: {failed['filename']}\n")
                f.write(f"错误: {failed['error']}\n\n")
        print(f"   详细错误已写入: {error_file}")
    
    if not all_data:
        print("\n✗ 没有数据可导入，程序退出")
        return
    
    # ========== 第3步：生成总表 ==========
    print("\n[3/7] 生成总表...")
    generator = SummaryGenerator()
    summary_result = generator.generate(all_data, root_path)
    
    if not summary_result['success']:
        print(f"   ✗ 生成总表失败: {summary_result['error']}")
        return
    
    print(f"   ✓ Excel总表: {summary_result['excel_path']}")
    print(f"   ✓ CSV总表: {summary_result['csv_path']}")
    print(f"   总记录数: {summary_result['total_rows']}")
    
    logger.log('INFO', f"总表生成成功，共 {summary_result['total_rows']} 条记录")
    
    # ========== 第4步：统计信息 ==========
    print("\n[4/7] 数据统计...")
    stats = summary_result['statistics']
    generator.print_statistics(stats)
    
    # ========== 第5步：清空旧数据 ==========
    print("\n[5/7] 清空数据库中的旧数据...")
    try:
        importer = DatabaseImporter()
        deleted = importer.clear_existing_data()
        logger.log('INFO', f"清空旧数据完成，删除 {deleted} 条记录")
    except Exception as e:
        print(f"   ✗ 清空数据失败: {str(e)}")
        logger.log('ERROR', "清空旧数据失败", str(e))
        return
    
    # ========== 第6步：导入新数据 ==========
    print("\n[6/7] 导入数据到数据库...")
    
    # 合并所有数据
    import pandas as pd
    final_df = pd.concat(all_data, ignore_index=True)
    
    try:
        import_result = importer.import_data(final_df)
        logger.log('INFO', f"数据导入完成，成功 {import_result['imported']} 条，失败 {import_result['failed']} 条")
        
        if import_result['errors']:
            print(f"\n   导入错误:")
            for error in import_result['errors']:
                print(f"     批次 {error['batch']}: {error['error']}")
    
    except Exception as e:
        print(f"   ✗ 导入失败: {str(e)}")
        logger.log('ERROR', "数据导入失败", str(e))
        return
    
    # ========== 第7步：验证数据 ==========
    print("\n[7/7] 验证导入的数据...")
    try:
        verify_result = importer.verify_data()
        
        if verify_result:
            print(f"   ✓ 数据库中共有 {verify_result['total_count']} 条事业单位岗位记录")
            print(f"\n   按城市分布:")
            for city, data in sorted(verify_result['by_city'].items()):
                print(f"     {city}: {data['positions']} 个岗位, {data['recruits']} 人")
            
            logger.log('INFO', f"数据验证完成，数据库共 {verify_result['total_count']} 条记录")
    
    except Exception as e:
        print(f"   ✗ 验证失败: {str(e)}")
    
    # ========== 完成 ==========
    print("\n" + "="*60)
    print("✓ 导入完成！")
    print("="*60)
    print(f"\n交付物:")
    print(f"  1. Excel总表: {summary_result['excel_path']}")
    print(f"  2. CSV总表: {summary_result['csv_path']}")
    print(f"  3. 导入日志: {log_file}")
    if failed_count > 0:
        print(f"  4. 错误报告: {error_file}")
    
    print(f"\n导入摘要:")
    print(f"  - 扫描文件: {len(files)} 个")
    print(f"  - 成功处理: {success_count} 个")
    print(f"  - 失败处理: {failed_count} 个")
    print(f"  - 总岗位数: {stats['total_positions']} 个")
    print(f"  - 总招聘人数: {stats['total_recruit']} 人")
    print(f"  - 数据库记录: {verify_result['total_count'] if verify_result else 'N/A'} 条")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断执行")
    except Exception as e:
        print(f"\n\n✗ 程序异常: {str(e)}")
        import traceback
        traceback.print_exc()
