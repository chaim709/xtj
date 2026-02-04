#!/usr/bin/env python3
"""
原始数据核查脚本 - 重新扫描所有源文件，验证真实的岗位数和招聘人数
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from typing import Dict, List
from file_scanner import FileScanner
from excel_parser import ExcelParser


class DataVerifier:
    """数据验证器"""
    
    # 招聘人数字段的可能列名
    RECRUIT_COUNT_COLUMNS = [
        '拟聘人数', '招聘人数', '计划数', '人数', '聘用人数',
        '招录人数', '拟招聘人数', '拟录用人数'
    ]
    
    # 岗位代码字段的可能列名
    POSITION_CODE_COLUMNS = [
        '岗位代码', '职位代码', '代码', '岗位 代码'
    ]
    
    @staticmethod
    def verify_all_files(root_path: str) -> Dict:
        """
        验证所有文件，统计真实数据
        
        Args:
            root_path: 根目录路径
            
        Returns:
            验证结果字典
        """
        print("=" * 80)
        print("原始数据核查工具")
        print("=" * 80)
        
        # 1. 扫描文件（启用去重）
        print("\n[1/4] 扫描Excel文件...")
        scanner = FileScanner()
        files, scan_info = scanner.scan_files(root_path, deduplicate=True)
        
        print(f"   ✓ 找到有效文件: {len(files)} 个")
        print(f"   ✓ 排除文件: {len(scan_info['excluded'])} 个")
        print(f"   ✓ 重复文件: {len(scan_info['duplicates'])} 个")
        
        if scan_info['duplicates']:
            print("\n   重复文件详情:")
            for dup in scan_info['duplicates']:
                print(f"     - {dup['filename']} ({dup['city']})")
        
        # 2. 解析每个文件并统计
        print(f"\n[2/4] 解析和统计数据...")
        parser = ExcelParser()
        
        city_stats = {}  # 按城市统计
        file_details = []  # 文件详情
        
        success_count = 0
        fail_count = 0
        total_positions = 0
        total_recruits = 0
        
        for idx, file_info in enumerate(files, 1):
            file_path = file_info['path']
            filename = file_info['filename']
            city = file_info['city']
            
            print(f"   处理 {idx}/{len(files)}: {filename[:50]}...", end='')
            
            # 解析文件
            df, result = parser.parse_excel(file_path)
            
            if not result.success or df is None or len(df) == 0:
                print(f" ❌ 失败")
                fail_count += 1
                file_details.append({
                    'filename': filename,
                    'city': city,
                    'status': 'failed',
                    'error': result.error,
                    'positions': 0,
                    'recruits': 0
                })
                continue
            
            # 统计数据
            try:
                positions_count, recruits_count = DataVerifier.count_positions_and_recruits(df)
                
                # 更新城市统计
                if city not in city_stats:
                    city_stats[city] = {'files': 0, 'positions': 0, 'recruits': 0}
                
                city_stats[city]['files'] += 1
                city_stats[city]['positions'] += positions_count
                city_stats[city]['recruits'] += recruits_count
                
                total_positions += positions_count
                total_recruits += recruits_count
                
                success_count += 1
                print(f" ✓ {positions_count}岗/{recruits_count}人")
                
                file_details.append({
                    'filename': filename,
                    'city': city,
                    'status': 'success',
                    'positions': positions_count,
                    'recruits': recruits_count,
                    'header_row': result.header_row
                })
                
            except Exception as e:
                print(f" ❌ 统计失败: {str(e)[:30]}")
                fail_count += 1
                file_details.append({
                    'filename': filename,
                    'city': city,
                    'status': 'count_failed',
                    'error': str(e),
                    'positions': 0,
                    'recruits': 0
                })
        
        # 3. 生成报告
        print(f"\n[3/4] 生成统计报告...")
        
        result = {
            'summary': {
                'total_files': len(files),
                'success_files': success_count,
                'failed_files': fail_count,
                'success_rate': f"{success_count/len(files)*100:.1f}%" if files else "0%",
                'total_positions': total_positions,
                'total_recruits': total_recruits,
                'excluded_files': len(scan_info['excluded']),
                'duplicate_files': len(scan_info['duplicates'])
            },
            'city_stats': city_stats,
            'file_details': file_details,
            'scan_info': scan_info
        }
        
        # 4. 显示结果
        print(f"\n[4/4] 核查完成!")
        print("=" * 80)
        print("\n汇总统计:")
        print(f"  总文件数: {len(files)} 个")
        print(f"  成功解析: {success_count} 个 ({success_count/len(files)*100:.1f}%)")
        print(f"  解析失败: {fail_count} 个")
        print(f"  总岗位数: {total_positions} 个")
        print(f"  总招聘人数: {total_recruits} 人")
        print(f"  平均每岗: {total_recruits/total_positions:.2f} 人" if total_positions > 0 else "")
        
        print("\n按城市统计:")
        print("-" * 80)
        print(f"{'城市':15s} | {'文件数':>6s} | {'岗位数':>8s} | {'招聘人数':>8s}")
        print("-" * 80)
        
        for city, stats in sorted(city_stats.items(), key=lambda x: x[1]['recruits'], reverse=True):
            print(f"{city:15s} | {stats['files']:6d} | {stats['positions']:8d} | {stats['recruits']:8d}")
        
        print("-" * 80)
        
        return result
    
    @staticmethod
    def count_positions_and_recruits(df: pd.DataFrame) -> tuple:
        """
        统计岗位数和招聘人数（改进版）
        
        Args:
            df: 数据DataFrame
            
        Returns:
            (岗位数, 招聘人数)
        """
        # 1. 清理数据：移除完全空的行
        df = df.dropna(how='all')
        
        if len(df) == 0:
            return 0, 0
        
        # 2. 尝试找到招聘人数列
        recruit_col = None
        for col_name in DataVerifier.RECRUIT_COUNT_COLUMNS:
            if col_name in df.columns:
                recruit_col = col_name
                break
        
        if recruit_col is None:
            # 如果没有找到标准列名，尝试模糊匹配
            for col in df.columns:
                col_str = str(col)
                if '人数' in col_str and ('招' in col_str or '拟' in col_str or '计划' in col_str):
                    recruit_col = col
                    break
        
        # 3. 尝试找到岗位代码列（用于判断有效行）
        code_col = None
        for col_name in DataVerifier.POSITION_CODE_COLUMNS:
            if col_name in df.columns:
                code_col = col_name
                break
        
        # 4. 确定有效行
        # 策略：优先使用岗位代码列，其次使用第一列（序号）
        if code_col and code_col in df.columns:
            # 使用岗位代码列判断有效行
            valid_rows = df[df[code_col].notna()]
            # 过滤掉包含"代码"等标题文字的行
            valid_rows = valid_rows[~valid_rows[code_col].astype(str).str.contains('代码|岗位', na=False)]
        else:
            # 使用第一列判断有效行
            first_col = df.columns[0]
            valid_rows = df[df[first_col].notna()]
            
            # 尝试过滤掉标题行：第一列如果是纯数字或序号格式，认为是有效行
            # 但如果没有找到任何纯数字行，则不过滤（可能是其他格式的序号）
            numeric_rows = valid_rows[valid_rows[first_col].astype(str).str.match(r'^\d+$', na=False)]
            if len(numeric_rows) > 0:
                valid_rows = numeric_rows
        
        positions_count = len(valid_rows)
        
        # 5. 统计招聘人数
        recruits_count = 0
        
        if recruit_col and recruit_col in df.columns and positions_count > 0:
            # 只统计有效行的招聘人数
            recruit_series = valid_rows[recruit_col]
            
            # 转换为数字并求和
            for val in recruit_series:
                try:
                    if pd.notna(val):
                        # 清理字符串
                        val_str = str(val).strip().replace(',', '').replace('，', '')
                        
                        # 尝试转换为数字
                        num = float(val_str)
                        
                        # 合理范围检查
                        if 0 < num < 1000:
                            recruits_count += int(num)
                        elif num >= 1000:
                            # 如果数字太大，可能是错误，假设为1
                            recruits_count += 1
                    else:
                        # 空值假设为1人
                        recruits_count += 1
                except:
                    # 如果无法转换，假设招聘1人
                    recruits_count += 1
        else:
            # 如果没有找到招聘人数列，假设每个岗位招聘1人
            recruits_count = positions_count
        
        return positions_count, recruits_count
    
    @staticmethod
    def save_report(result: Dict, output_file: str):
        """保存核查报告到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("安徽省事业单位原始数据核查报告\n")
            f.write("=" * 80 + "\n\n")
            
            # 1. 汇总信息
            f.write("一、汇总信息\n")
            f.write("-" * 80 + "\n")
            for key, value in result['summary'].items():
                f.write(f"{key}: {value}\n")
            
            # 2. 按城市统计
            f.write("\n二、按城市统计\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'城市':15s} | {'文件数':>6s} | {'岗位数':>8s} | {'招聘人数':>8s}\n")
            f.write("-" * 80 + "\n")
            
            for city, stats in sorted(result['city_stats'].items(), key=lambda x: x[1]['recruits'], reverse=True):
                f.write(f"{city:15s} | {stats['files']:6d} | {stats['positions']:8d} | {stats['recruits']:8d}\n")
            
            # 3. 文件详情
            f.write("\n三、文件详情\n")
            f.write("-" * 80 + "\n")
            
            for detail in result['file_details']:
                status_icon = "✓" if detail['status'] == 'success' else "✗"
                f.write(f"{status_icon} {detail['filename']}\n")
                f.write(f"   城市: {detail['city']}, 岗位: {detail['positions']}, 招聘: {detail['recruits']}\n")
                if detail.get('error'):
                    f.write(f"   错误: {detail['error']}\n")
            
            # 4. 重复文件
            if result['scan_info']['duplicates']:
                f.write("\n四、重复文件（已排除）\n")
                f.write("-" * 80 + "\n")
                for dup in result['scan_info']['duplicates']:
                    f.write(f"  - {dup['filename']} ({dup['city']})\n")
            
            # 5. 排除文件
            if result['scan_info']['excluded']:
                f.write("\n五、排除文件\n")
                f.write("-" * 80 + "\n")
                for excl in result['scan_info']['excluded']:
                    f.write(f"  - {os.path.basename(excl['path'])}\n")


def main():
    """主函数"""
    root_path = "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位"
    
    # 执行核查
    result = DataVerifier.verify_all_files(root_path)
    
    # 保存报告
    report_file = os.path.join(
        os.path.dirname(__file__),
        'original_data_verification_report.txt'
    )
    
    DataVerifier.save_report(result, report_file)
    
    print(f"\n✓ 详细报告已保存到: {report_file}")
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
