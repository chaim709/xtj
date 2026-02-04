"""
Excel解析器 - 智能识别表头并解析Excel文件
"""
import pandas as pd
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    rows: int = 0
    error: str = None
    header_row: int = None


class ExcelParser:
    """Excel文件解析器 - 支持多行表头智能识别"""
    
    # 用于识别表头的关键词（按优先级排序）
    HEADER_KEYWORDS = ['序号', '岗位代码', '岗位名称', '招聘单位', '用人单位', '拟聘人数', '招聘人数', '专业']
    
    # 标题行关键词（用于识别标题而非表头）
    TITLE_KEYWORDS = ['岗位表', '汇总表', '计划表', '附件']
    
    @staticmethod
    def parse_excel(file_path: str) -> Tuple[Optional[pd.DataFrame], ParseResult]:
        """
        解析Excel文件（支持多行表头自动识别）
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            (DataFrame, ParseResult)
        """
        try:
            # 1. 读取前15行，查找表头（增加扫描范围）
            df_preview = pd.read_excel(file_path, header=None, nrows=15)
            header_row = ExcelParser.find_header_row_enhanced(df_preview)
            
            if header_row is None:
                return None, ParseResult(
                    success=False,
                    error="无法识别表头行"
                )
            
            # 2. 使用找到的表头行重新读取
            df = pd.read_excel(file_path, header=header_row)
            
            # 3. 清理列名
            df.columns = [ExcelParser.clean_column_name(col) for col in df.columns]
            
            # 4. 移除完全空的行和标题行残留
            df = df.dropna(how='all')
            
            # 5. 移除可能的标题行残留（第一列为空或为标题文本）
            if len(df) > 0:
                first_col = df.columns[0]
                df = df[df[first_col].notna()]  # 移除第一列为空的行
                
                # 如果第一列包含标题关键词，移除该行
                if len(df) > 0:
                    first_val = str(df.iloc[0][first_col])
                    if any(kw in first_val for kw in ExcelParser.TITLE_KEYWORDS):
                        df = df.iloc[1:]
            
            # 6. 重置索引
            df = df.reset_index(drop=True)
            
            return df, ParseResult(
                success=True,
                rows=len(df),
                header_row=header_row
            )
        
        except Exception as e:
            return None, ParseResult(
                success=False,
                error=str(e)
            )
    
    @staticmethod
    def find_header_row(df: pd.DataFrame) -> Optional[int]:
        """
        查找表头行（原版，保留兼容性）
        
        Args:
            df: DataFrame（前几行）
            
        Returns:
            表头行索引，如果未找到返回None
        """
        for idx, row in df.iterrows():
            # 将行转换为字符串
            row_str = ' '.join([str(v) for v in row if pd.notna(v)])
            
            # 检查是否包含多个关键词
            keyword_count = sum(1 for kw in ExcelParser.HEADER_KEYWORDS if kw in row_str)
            
            # 如果包含至少3个关键词，认为是表头行
            if keyword_count >= 3:
                return idx
        
        # 默认返回第0行或第1行
        # 检查第0行是否像标题
        first_row_str = ' '.join([str(v) for v in df.iloc[0] if pd.notna(v)])
        if '岗位表' in first_row_str or '汇总表' in first_row_str:
            return 1  # 第一行是标题，第二行可能是表头
        
        return 0  # 默认第一行
    
    @staticmethod
    def find_header_row_enhanced(df: pd.DataFrame) -> Optional[int]:
        """
        增强版表头行查找（支持多行表头和复杂格式）
        
        Args:
            df: DataFrame（前几行）
            
        Returns:
            表头行索引，如果未找到返回None
        """
        best_row = None
        best_score = 0
        
        for idx, row in df.iterrows():
            score = 0
            non_empty_count = 0
            
            # 统计非空单元格
            for val in row:
                if pd.notna(val):
                    non_empty_count += 1
                    val_str = str(val).strip()
                    
                    # 1. 检查是否包含关键词（高权重）
                    for kw in ExcelParser.HEADER_KEYWORDS:
                        if kw in val_str:
                            score += 10
                    
                    # 2. 短文本（可能是列名）
                    if len(val_str) <= 20:
                        score += 1
                    
                    # 3. 包含换行符（可能是合并单元格的列名）
                    if '\n' in val_str or '\r' in val_str:
                        score += 2
                    
                    # 4. 负面评分：如果是标题关键词
                    if any(kw in val_str for kw in ExcelParser.TITLE_KEYWORDS):
                        score -= 20
                    
                    # 5. 负面评分：纯数字（可能是数据行）
                    if val_str.isdigit():
                        score -= 3
            
            # 6. 非空单元格数量加分（表头通常有多个列）
            if non_empty_count >= 5:
                score += non_empty_count
            
            # 更新最佳行
            if score > best_score:
                best_score = score
                best_row = idx
        
        # 如果找到了合适的表头（得分>10）
        if best_score > 10:
            return best_row
        
        # 降级策略：使用原版方法
        return ExcelParser.find_header_row(df)
    
    @staticmethod
    def clean_column_name(col_name) -> str:
        """
        清理列名
        
        Args:
            col_name: 原始列名
            
        Returns:
            清理后的列名
        """
        if pd.isna(col_name):
            return 'Unnamed'
        
        col_name = str(col_name)
        
        # 移除换行符和多余空格
        col_name = col_name.replace('\n', '').replace('\r', '')
        col_name = ' '.join(col_name.split())  # 多个空格变为一个
        col_name = col_name.strip()
        
        return col_name if col_name else 'Unnamed'


if __name__ == '__main__':
    # 测试代码
    import sys
    
    test_files = [
        "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/安徽省2026年度省直事业单位统一公开招聘岗位汇总表.xlsx",
        "/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/蚌埠市岗位表/蚌埠市事业单位2026年度公开招聘工作人员岗位计划表.xlsx"
    ]
    
    parser = ExcelParser()
    
    for file_path in test_files:
        print(f"\n{'='*60}")
        print(f"测试文件: {file_path.split('/')[-1]}")
        print('='*60)
        
        df, result = parser.parse_excel(file_path)
        
        if result.success:
            print(f"✓ 解析成功")
            print(f"  表头行: {result.header_row}")
            print(f"  数据行数: {result.rows}")
            print(f"  列名: {list(df.columns[:10])}")  # 显示前10个列名
            print(f"\n前3行数据:")
            print(df.head(3).to_string())
        else:
            print(f"✗ 解析失败: {result.error}")
