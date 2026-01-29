"""
数据导入服务 - 岗位和专业目录导入
"""
import os
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd
from app import db
from app.models.position import Position
from app.models.major import MajorCategory, Major


class ImportService:
    """数据导入服务类"""
    
    # 岗位表列名映射（支持多种格式）
    POSITION_COLUMN_MAPPING = {
        '隶属  关系': 'affiliation',
        '隶属关系': 'affiliation',
        '地区  代码': 'region_code',
        '地区代码': 'region_code',
        '地区  名称': 'region_name',
        '地区名称': 'region_name',
        '地市': 'city',
        '单位代码': 'department_code',
        '单位名称': 'department_name',
        '职位代码': 'position_code',
        '职位名称': 'position_name',
        '职位简介': 'position_desc',
        '考试类别': 'exam_category',
        '开考比例': 'open_ratio',
        '招考人数': 'recruit_count',
        '学　历': 'education',
        '学历': 'education',
        '专　业': 'major_requirement',
        '专业': 'major_requirement',
        '其　它': 'other_requirements',
        '其它': 'other_requirements',
        '其他': 'other_requirements',
        '报名人数': 'apply_count',
        '竞争比': 'competition_ratio',
        '最低进面分': 'min_entry_score',
        '最高进面分': 'max_entry_score',
        '最高行测': 'max_xingce_score',
        '最高申论': 'max_shenlun_score',
        '公安专业知识最高分': 'max_police_score',
        '公安专业知识最低分': 'min_police_score',
        '职位所属地区': 'region_name',
        '地': 'city',
    }
    
    @staticmethod
    def import_positions_from_excel(file_path: str, year: int, exam_type: str = '省考',
                                     city: str = None, sheet_name: Any = 0,
                                     header_row: int = 2, system_type: str = None) -> Dict[str, Any]:
        """
        从Excel导入岗位数据
        
        Args:
            file_path: Excel文件路径
            year: 年份
            exam_type: 考试类型（省考/国考）
            city: 城市名称（可选，如果文件中没有城市列）
            sheet_name: Sheet名称或索引
            header_row: 表头所在行（从0开始）
            
        Returns:
            导入结果字典
        """
        result = {
            'success': False,
            'total': 0,
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # 读取Excel
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
            result['total'] = len(df)
            
            # 标准化列名
            df = ImportService._normalize_columns(df)
            
            # 逐行处理
            for idx, row in df.iterrows():
                try:
                    position_data = ImportService._parse_position_row(row, year, exam_type, city, system_type)
                    if not position_data:
                        result['skipped'] += 1
                        continue
                    
                    # 检查是否已存在
                    existing = Position.query.filter_by(
                        year=year,
                        exam_type=exam_type,
                        region_code=position_data.get('region_code'),
                        department_code=position_data.get('department_code'),
                        position_code=position_data.get('position_code')
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        for key, value in position_data.items():
                            if value is not None:
                                setattr(existing, key, value)
                        result['updated'] += 1
                    else:
                        # 创建新记录
                        position = Position(**position_data)
                        db.session.add(position)
                        result['imported'] += 1
                        
                except Exception as e:
                    result['errors'].append(f"行 {idx + header_row + 2}: {str(e)}")
                    result['skipped'] += 1
            
            db.session.commit()
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"文件读取错误: {str(e)}")
            db.session.rollback()
        
        return result
    
    @staticmethod
    def import_positions_from_folder(folder_path: str, year: int, 
                                      exam_type: str = '省考') -> Dict[str, Any]:
        """
        从文件夹批量导入岗位数据（支持多个城市文件）
        
        Args:
            folder_path: 文件夹路径
            year: 年份
            exam_type: 考试类型
            
        Returns:
            导入结果字典
        """
        total_result = {
            'success': True,
            'files_processed': 0,
            'total': 0,
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'file_results': {}
        }
        
        # 城市名称映射
        city_mapping = {
            '01': '南京市', '02': '无锡市', '03': '徐州市', '04': '常州市',
            '05': '苏州市', '06': '南通市', '07': '连云港市', '08': '淮安市',
            '09': '盐城市', '10': '扬州市', '11': '镇江市', '12': '泰州市',
            '13': '宿迁市'
        }
        
        # 遍历文件夹
        for filename in os.listdir(folder_path):
            if not (filename.endswith('.xls') or filename.endswith('.xlsx')):
                continue
            
            file_path = os.path.join(folder_path, filename)
            
            # 从文件名提取城市和系统类型
            city = None
            system_type = None
            
            # 先检查是否为特殊系统
            if '省级机关' in filename:
                system_type = '省级机关'
                city = '省级'
            elif '监狱' in filename or '戒毒' in filename:
                system_type = '监狱戒毒系统'
                city = '省级'
            elif '统计' in filename:
                system_type = '统计系统'
                city = '省级'
            else:
                # 检查是否为城市文件
                for code, city_name in city_mapping.items():
                    if filename.startswith(code) or city_name.replace('市', '') in filename:
                        city = city_name
                        system_type = '地市机关'
                        break
            
            # 如果都没匹配到
            if not system_type:
                system_type = '其他'
                city = city or '未知'
            
            # 导入单个文件
            result = ImportService.import_positions_from_excel(
                file_path, year, exam_type, city, system_type=system_type
            )
            
            total_result['files_processed'] += 1
            total_result['total'] += result['total']
            total_result['imported'] += result['imported']
            total_result['updated'] += result['updated']
            total_result['skipped'] += result['skipped']
            total_result['errors'].extend(result['errors'])
            total_result['file_results'][filename] = result
            
            if not result['success']:
                total_result['success'] = False
        
        return total_result
    
    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        # 清理列名中的空格
        df.columns = [str(col).strip() for col in df.columns]
        
        # 映射列名 - 精确匹配优先
        rename_dict = {}
        used_new_names = set()  # 避免重复映射
        
        for col in df.columns:
            # 跳过已映射的列
            if col in rename_dict:
                continue
            
            # 精确匹配
            if col in ImportService.POSITION_COLUMN_MAPPING:
                new_name = ImportService.POSITION_COLUMN_MAPPING[col]
                if new_name not in used_new_names:
                    rename_dict[col] = new_name
                    used_new_names.add(new_name)
        
        if rename_dict:
            df = df.rename(columns=rename_dict)
        
        # 删除无法映射的列（避免干扰）
        keep_cols = list(rename_dict.values()) + [c for c in df.columns if c not in rename_dict]
        
        return df
    
    @staticmethod
    def _parse_position_row(row: pd.Series, year: int, exam_type: str,
                            default_city: str = None, system_type: str = None) -> Dict[str, Any]:
        """解析岗位数据行"""
        # 必要字段检查
        position_code = row.get('position_code')
        department_name = row.get('department_name')
        
        # 检查值是否为空或为NaN
        def is_empty(val):
            if val is None:
                return True
            if isinstance(val, float) and pd.isna(val):
                return True
            if isinstance(val, str) and not val.strip():
                return True
            return False
        
        if is_empty(position_code) or is_empty(department_name):
            return None
        
        data = {
            'year': year,
            'exam_type': exam_type,
            'affiliation': ImportService._clean_value(row.get('affiliation')),
            'region_code': ImportService._clean_value(row.get('region_code')),
            'region_name': ImportService._clean_value(row.get('region_name')),
            'city': ImportService._clean_value(row.get('city')) or default_city,
            'system_type': system_type,
            'department_code': ImportService._clean_value(row.get('department_code')),
            'department_name': ImportService._clean_value(department_name),
            'position_code': str(int(position_code)) if isinstance(position_code, float) else str(position_code),
            'position_name': ImportService._clean_value(row.get('position_name')),
            'position_desc': ImportService._clean_value(row.get('position_desc')),
            'exam_category': ImportService._clean_value(row.get('exam_category')),
            'education': ImportService._clean_value(row.get('education')),
            'major_requirement': ImportService._clean_value(row.get('major_requirement')),
            'other_requirements': ImportService._clean_value(row.get('other_requirements')),
        }
        
        # 数值字段
        data['open_ratio'] = ImportService._parse_int(row.get('open_ratio'))
        data['recruit_count'] = ImportService._parse_int(row.get('recruit_count')) or 1
        data['apply_count'] = ImportService._parse_int(row.get('apply_count'))
        data['competition_ratio'] = ImportService._parse_float(row.get('competition_ratio'))
        data['min_entry_score'] = ImportService._parse_float(row.get('min_entry_score'))
        data['max_entry_score'] = ImportService._parse_float(row.get('max_entry_score'))
        data['max_xingce_score'] = ImportService._parse_float(row.get('max_xingce_score'))
        data['max_shenlun_score'] = ImportService._parse_float(row.get('max_shenlun_score'))
        data['max_police_score'] = ImportService._parse_float(row.get('max_police_score'))
        data['min_police_score'] = ImportService._parse_float(row.get('min_police_score'))
        
        return data
    
    @staticmethod
    def _clean_value(value) -> str:
        """清理值"""
        if pd.isna(value):
            return None
        return str(value).strip()
    
    @staticmethod
    def _parse_int(value) -> int:
        """解析整数"""
        if pd.isna(value):
            return None
        try:
            return int(float(value))
        except:
            return None
    
    @staticmethod
    def _parse_float(value) -> float:
        """解析浮点数"""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except:
            return None
    
    @staticmethod
    def import_majors_from_parsed_data(data: List[Dict]) -> Dict[str, Any]:
        """
        从解析后的数据导入专业
        
        Args:
            data: 专业数据列表，格式：
                [{'category_code': 1, 'education_level': '本科', 'majors': ['法学', '知识产权']}]
                
        Returns:
            导入结果
        """
        result = {
            'success': True,
            'categories_processed': 0,
            'majors_imported': 0,
            'errors': []
        }
        
        for item in data:
            try:
                category_code = item.get('category_code')
                education_level = item.get('education_level')
                majors = item.get('majors', [])
                
                # 查找专业大类
                category = MajorCategory.query.filter_by(code=category_code).first()
                if not category:
                    result['errors'].append(f"专业大类不存在: {category_code}")
                    continue
                
                result['categories_processed'] += 1
                
                # 导入专业
                for major_name in majors:
                    major_name = major_name.strip()
                    if not major_name or len(major_name) < 2:
                        continue
                    
                    # 检查是否已存在
                    existing = Major.query.filter_by(
                        category_id=category.id,
                        name=major_name,
                        education_level=education_level
                    ).first()
                    
                    if not existing:
                        major = Major(
                            category_id=category.id,
                            name=major_name,
                            education_level=education_level
                        )
                        db.session.add(major)
                        result['majors_imported'] += 1
                
            except Exception as e:
                result['errors'].append(f"处理数据错误: {str(e)}")
                result['success'] = False
        
        try:
            db.session.commit()
        except Exception as e:
            result['errors'].append(f"数据库提交错误: {str(e)}")
            result['success'] = False
            db.session.rollback()
        
        return result
    
    @staticmethod
    def get_import_stats() -> Dict[str, int]:
        """获取导入统计"""
        return {
            'positions': Position.query.count(),
            'categories': MajorCategory.query.count(),
            'majors': Major.query.count(),
            'positions_by_year': dict(
                db.session.query(Position.year, db.func.count(Position.id))
                .group_by(Position.year)
                .all()
            )
        }
    
    # ==================== 国考数据导入器 ====================
    
    # 国考列名映射
    GUOKAO_COLUMN_MAPPING = {
        '部门代码': 'department_code',
        '部门名称': 'department_name',
        '用人司局': 'bureau_name',
        '机构性质': 'institution_type',
        '招考职位': 'position_name',
        '职位属性': 'position_attr',
        '职位分布': 'position_dist',
        '职位简介': 'position_desc',
        '职位代码': 'position_code',
        '机构层级': 'institution_level',
        '考试类别': 'exam_category',
        '招考人数': 'recruit_count',
        '专业': 'major_requirement',
        '学历': 'education',
        '学位': 'degree',
        '政治面貌': 'political_status',
        '基层工作最低年限': 'min_work_years',
        '服务基层项目工作经历': 'grassroots_experience',
        '备注': 'other_requirements',
        '是否在面试阶段组织专业能力测试': 'has_ability_test',
        '面试人员比例': 'interview_ratio',
        '工作地点': 'work_location',
        '落户地点': 'settle_location',
        '咨询电话': 'contact_phone',
    }
    
    @staticmethod
    def import_guokao_positions(file_path: str, year: int) -> Dict[str, Any]:
        """
        从国考职位表导入数据
        
        Args:
            file_path: Excel文件路径
            year: 年份
            
        Returns:
            导入结果字典
        """
        result = {
            'success': False,
            'total': 0,
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'sheets_processed': []
        }
        
        try:
            xl = pd.ExcelFile(file_path)
            sheets = xl.sheet_names
            
            for sheet_name in sheets:
                try:
                    # 读取数据，跳过第一行说明
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
                    
                    # 检查是否为有效的职位表（通过检查关键列）
                    if '职位代码' not in df.columns and '部门代码' not in df.columns:
                        continue
                    
                    result['sheets_processed'].append(sheet_name)
                    result['total'] += len(df)
                    
                    # 逐行处理
                    for idx, row in df.iterrows():
                        try:
                            position_data = ImportService._parse_guokao_row(row, year, sheet_name)
                            if not position_data:
                                result['skipped'] += 1
                                continue
                            
                            # 检查是否已存在（国考用职位代码作为唯一标识）
                            existing = Position.query.filter_by(
                                year=year,
                                exam_type='国考',
                                position_code=position_data.get('position_code')
                            ).first()
                            
                            if existing:
                                # 更新现有记录
                                for key, value in position_data.items():
                                    if value is not None:
                                        setattr(existing, key, value)
                                result['updated'] += 1
                            else:
                                # 创建新记录
                                position = Position(**position_data)
                                db.session.add(position)
                                result['imported'] += 1
                            
                            # 每1000条提交一次
                            if (result['imported'] + result['updated']) % 1000 == 0:
                                db.session.commit()
                                
                        except Exception as e:
                            result['errors'].append(f"Sheet[{sheet_name}] 行{idx}: {str(e)}")
                            result['skipped'] += 1
                
                except Exception as e:
                    result['errors'].append(f"Sheet[{sheet_name}] 读取失败: {str(e)}")
            
            db.session.commit()
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"文件读取错误: {str(e)}")
            db.session.rollback()
        
        return result
    
    @staticmethod
    def _parse_guokao_row(row: pd.Series, year: int, sheet_name: str) -> Dict[str, Any]:
        """解析国考数据行"""
        position_code = row.get('职位代码')
        department_name = row.get('部门名称')
        
        # 检查必要字段
        if pd.isna(position_code) or pd.isna(department_name):
            return None
        
        # 根据sheet名称确定系统类型
        system_type_mapping = {
            '中央党群机关': '中央党群机关',
            '中央国家行政机关（本级）': '中央国家行政机关',
            '中央国家行政机关省级以下直属机构': '省级以下直属机构',
            '中央国家行政机关参照公务员法管理事业单位': '参公事业单位',
        }
        system_type = system_type_mapping.get(sheet_name, '其他')
        
        data = {
            'year': year,
            'exam_type': '国考',
            'system_type': system_type,
            'department_code': ImportService._clean_value(row.get('部门代码')),
            'department_name': ImportService._clean_value(department_name),
            'position_code': str(position_code).strip(),
            'position_name': ImportService._clean_value(row.get('招考职位')),
            'position_desc': ImportService._clean_value(row.get('职位简介')),
            'exam_category': ImportService._clean_value(row.get('考试类别')),
            'education': ImportService._clean_value(row.get('学历')),
            'major_requirement': ImportService._clean_value(row.get('专业')),
            'other_requirements': ImportService._clean_value(row.get('备注')),
            'city': ImportService._clean_value(row.get('工作地点')),
            'region_name': ImportService._clean_value(row.get('工作地点')),
        }
        
        # 数值字段
        data['recruit_count'] = ImportService._parse_int(row.get('招考人数')) or 1
        
        return data
    
    # ==================== 进面分数导入器 ====================
    
    @staticmethod
    def import_entry_scores(file_path: str, year: int = None, 
                            exam_type: str = '省考') -> Dict[str, Any]:
        """
        从进面分数表导入数据
        
        Args:
            file_path: Excel文件路径
            year: 年份（如果文件中没有年份列）
            exam_type: 考试类型
            
        Returns:
            导入结果字典
        """
        result = {
            'success': False,
            'total': 0,
            'matched': 0,
            'created': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            df = pd.read_excel(file_path, header=0)
            result['total'] = len(df)
            
            # 检测列名
            columns = list(df.columns)
            
            # 尝试识别年份列
            year_col = None
            if '年份' in columns:
                year_col = '年份'
            
            # 识别其他列
            city_col = '地市' if '地市' in columns else None
            dept_col = '部门名称' if '部门名称' in columns else None
            
            # 职位代码列可能有不同名称
            code_col = None
            for col in columns:
                if '职位' in col and '代码' in col:
                    code_col = col
                    break
            
            min_score_col = '进面最低分' if '进面最低分' in columns else None
            max_score_col = '进面最高分' if '进面最高分' in columns else None
            
            if not code_col or not min_score_col:
                result['errors'].append(f"无法识别关键列：{columns}")
                return result
            
            # 逐行处理
            for idx, row in df.iterrows():
                try:
                    # 获取年份
                    row_year = year
                    if year_col:
                        row_year = ImportService._parse_int(row.get(year_col))
                    if not row_year:
                        result['skipped'] += 1
                        continue
                    
                    position_code = row.get(code_col)
                    if pd.isna(position_code):
                        result['skipped'] += 1
                        continue
                    
                    position_code = str(int(position_code) if isinstance(position_code, float) else position_code)
                    
                    min_score = ImportService._parse_float(row.get(min_score_col))
                    max_score = ImportService._parse_float(row.get(max_score_col)) if max_score_col else None
                    
                    city = ImportService._clean_value(row.get(city_col)) if city_col else None
                    dept_name = ImportService._clean_value(row.get(dept_col)) if dept_col else None
                    
                    # 尝试匹配已有岗位
                    query = Position.query.filter(
                        Position.year == row_year,
                        Position.exam_type == exam_type,
                        Position.position_code == position_code
                    )
                    
                    # 如果有城市信息，进一步筛选
                    if city:
                        # 城市可能是简称，需要模糊匹配
                        query = query.filter(Position.city.contains(city.replace('市', '')))
                    
                    existing = query.first()
                    
                    if existing:
                        # 更新分数
                        existing.min_entry_score = min_score
                        if max_score:
                            existing.max_entry_score = max_score
                        result['matched'] += 1
                    else:
                        # 创建简化记录
                        position = Position(
                            year=row_year,
                            exam_type=exam_type,
                            position_code=position_code,
                            department_name=dept_name or f"未知部门-{position_code}",
                            city=city,
                            min_entry_score=min_score,
                            max_entry_score=max_score,
                            system_type='进面分数导入'
                        )
                        db.session.add(position)
                        result['created'] += 1
                    
                    # 每1000条提交一次
                    if (result['matched'] + result['created']) % 1000 == 0:
                        db.session.commit()
                        
                except Exception as e:
                    result['errors'].append(f"行{idx}: {str(e)}")
                    result['skipped'] += 1
            
            db.session.commit()
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"文件读取错误: {str(e)}")
            db.session.rollback()
        
        return result
    
    # ==================== 批量导入控制器 ====================
    
    @staticmethod
    def identify_file_type(file_path: str) -> Tuple[str, int]:
        """
        智能识别文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            (文件类型, 年份)
            文件类型: 'guokao' | 'jiangsu' | 'score_only' | 'unknown'
        """
        filename = os.path.basename(file_path)
        parent_dir = os.path.basename(os.path.dirname(file_path))
        year = None
        
        # 从文件名提取年份
        year_match = re.search(r'(20\d{2})', filename)
        if year_match:
            year = int(year_match.group(1))
        
        # 如果文件名没有年份，尝试从父文件夹提取
        if not year:
            year_match = re.search(r'(20\d{2})', parent_dir)
            if year_match:
                year = int(year_match.group(1))
        
        # 特殊处理：23/24/25/26开头的年份
        short_year_match = re.search(r'^(2[0-9])江苏', filename)
        if short_year_match and not year:
            year = 2000 + int(short_year_match.group(1))
        
        # 通过文件名快速判断
        if '国考' in filename or '中央机关' in filename:
            return 'guokao', year
        
        # 进面分数文件判断（但排除包含"职位表"的完整数据文件）
        if '进面' in filename and '分' in filename and '职位表' not in filename:
            return 'score_only', year
        
        # 读取文件检查列名
        try:
            xl = pd.ExcelFile(file_path)
            sheets = xl.sheet_names
            
            # 优先检查的sheet名称
            priority_sheets = ['职位汇总版', '汇总', '中央国家行政机关省级以下直属机构']
            check_sheets = [s for s in priority_sheets if s in sheets] + sheets[:5]
            
            for sheet in check_sheets:
                if sheet not in sheets:
                    continue
                for header_row in [0, 1, 2]:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet, header=header_row, nrows=1)
                        columns_str = ' '.join(str(c) for c in df.columns)
                        
                        # 国考特征：部门代码 + 用人司局
                        if '部门代码' in columns_str and '用人司局' in columns_str:
                            return 'guokao', year
                        
                        # 江苏省考特征：地区代码 或 单位代码 + 职位代码（优先于进面分数）
                        if ('地区' in columns_str and '代码' in columns_str) or \
                           ('单位代码' in columns_str and '职位代码' in columns_str) or \
                           ('隶属' in columns_str and '关系' in columns_str):
                            return 'jiangsu', year
                        
                        # 进面分数特征：只有进面最低分，没有完整岗位信息
                        if '进面最低分' in columns_str and '单位代码' not in columns_str:
                            return 'score_only', year
                        
                    except:
                        continue
        except:
            pass
        
        return 'unknown', year
    
    @staticmethod
    def batch_import_all_files(folder_path: str) -> Dict[str, Any]:
        """
        批量导入文件夹中的所有数据
        
        Args:
            folder_path: 根文件夹路径
            
        Returns:
            导入结果汇总
        """
        result = {
            'success': True,
            'files_processed': 0,
            'total_imported': 0,
            'total_updated': 0,
            'total_skipped': 0,
            'errors': [],
            'file_results': {},
            'summary': {
                'guokao': {'files': 0, 'records': 0},
                'jiangsu': {'files': 0, 'records': 0},
                'score_only': {'files': 0, 'records': 0},
                'unknown': {'files': 0},
            }
        }
        
        # 递归查找所有Excel文件
        excel_files = []
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f.endswith('.xls') or f.endswith('.xlsx'):
                    # 跳过临时文件
                    if f.startswith('~$'):
                        continue
                    excel_files.append(os.path.join(root, f))
        
        print(f"找到 {len(excel_files)} 个Excel文件")
        
        for file_path in excel_files:
            filename = os.path.basename(file_path)
            print(f"\n处理: {filename}")
            
            try:
                # 识别文件类型
                file_type, year = ImportService.identify_file_type(file_path)
                print(f"  类型: {file_type}, 年份: {year}")
                
                if file_type == 'unknown':
                    result['summary']['unknown']['files'] += 1
                    result['file_results'][filename] = {'type': 'unknown', 'skipped': True}
                    print(f"  跳过: 无法识别的文件类型")
                    continue
                
                if not year:
                    result['errors'].append(f"{filename}: 无法识别年份")
                    print(f"  跳过: 无法识别年份")
                    continue
                
                # 根据类型调用不同的导入器
                if file_type == 'guokao':
                    file_result = ImportService.import_guokao_positions(file_path, year)
                    result['summary']['guokao']['files'] += 1
                    result['summary']['guokao']['records'] += file_result.get('imported', 0) + file_result.get('updated', 0)
                    
                elif file_type == 'jiangsu':
                    # 检查是否为文件夹内的城市文件
                    if '各地职位表' in file_path:
                        # 单独处理城市文件
                        file_result = ImportService._import_jiangsu_city_file(file_path, year)
                    else:
                        file_result = ImportService.import_positions_from_excel(
                            file_path, year, '省考', header_row=1
                        )
                    result['summary']['jiangsu']['files'] += 1
                    result['summary']['jiangsu']['records'] += file_result.get('imported', 0) + file_result.get('updated', 0)
                    
                elif file_type == 'score_only':
                    file_result = ImportService.import_entry_scores(file_path, year)
                    result['summary']['score_only']['files'] += 1
                    result['summary']['score_only']['records'] += file_result.get('matched', 0) + file_result.get('created', 0)
                
                result['files_processed'] += 1
                result['total_imported'] += file_result.get('imported', 0) + file_result.get('created', 0)
                result['total_updated'] += file_result.get('updated', 0) + file_result.get('matched', 0)
                result['total_skipped'] += file_result.get('skipped', 0)
                result['errors'].extend(file_result.get('errors', [])[:5])  # 只保留前5个错误
                result['file_results'][filename] = file_result
                
                print(f"  结果: 导入{file_result.get('imported', 0)}, 更新{file_result.get('updated', 0)}, 跳过{file_result.get('skipped', 0)}")
                
            except Exception as e:
                result['errors'].append(f"{filename}: {str(e)}")
                print(f"  错误: {str(e)}")
        
        return result
    
    @staticmethod
    def _import_jiangsu_city_file(file_path: str, year: int) -> Dict[str, Any]:
        """导入江苏省考城市文件"""
        filename = os.path.basename(file_path)
        
        # 城市名称映射
        city_mapping = {
            '01': '南京市', '02': '无锡市', '03': '徐州市', '04': '常州市',
            '05': '苏州市', '06': '南通市', '07': '连云港市', '08': '淮安市',
            '09': '盐城市', '10': '扬州市', '11': '镇江市', '12': '泰州市',
            '13': '宿迁市'
        }
        
        # 识别城市和系统类型
        city = None
        system_type = None
        
        if '省级机关' in filename:
            system_type = '省级机关'
            city = '省级'
        elif '监狱' in filename or '戒毒' in filename:
            system_type = '监狱戒毒系统'
            city = '省级'
        elif '统计' in filename:
            system_type = '统计系统'
            city = '省级'
        else:
            for code, city_name in city_mapping.items():
                if filename.startswith(code) or city_name.replace('市', '') in filename:
                    city = city_name
                    system_type = '地市机关'
                    break
        
        if not system_type:
            system_type = '其他'
            city = city or '未知'
        
        return ImportService.import_positions_from_excel(
            file_path, year, '省考', city, system_type=system_type
        )
