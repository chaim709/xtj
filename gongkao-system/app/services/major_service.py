"""
专业目录服务 - 专业匹配和查询
"""
import re
from typing import List, Optional, Tuple
from app import db
from app.models.major import MajorCategory, Major, MAJOR_CATEGORIES


class MajorService:
    """专业目录服务类"""
    
    @staticmethod
    def search_majors(keyword: str, education_level: str = None, limit: int = 20) -> List[Major]:
        """
        搜索专业
        
        Args:
            keyword: 搜索关键词
            education_level: 学历层次筛选（研究生/本科/专科）
            limit: 返回数量限制
            
        Returns:
            匹配的专业列表
        """
        query = Major.query.filter(Major.name.contains(keyword))
        
        if education_level:
            query = query.filter(Major.education_level == education_level)
        
        return query.limit(limit).all()
    
    @staticmethod
    def get_category_by_major(major_name: str, education_level: str = None) -> Optional[MajorCategory]:
        """
        根据专业名称获取所属专业大类
        
        Args:
            major_name: 专业名称
            education_level: 学历层次
            
        Returns:
            专业大类对象，未找到返回None
        """
        query = Major.query.filter(Major.name == major_name)
        
        if education_level:
            query = query.filter(Major.education_level == education_level)
        
        major = query.first()
        if major:
            return major.category
        
        # 尝试模糊匹配
        major = Major.query.filter(Major.name.contains(major_name)).first()
        if major:
            return major.category
        
        return None
    
    @staticmethod
    def get_all_categories() -> List[MajorCategory]:
        """获取所有专业大类"""
        return MajorCategory.query.order_by(MajorCategory.code).all()
    
    @staticmethod
    def get_majors_by_category(category_id: int, education_level: str = None) -> List[Major]:
        """
        获取某专业大类下的所有专业
        
        Args:
            category_id: 专业大类ID
            education_level: 学历层次筛选
            
        Returns:
            专业列表
        """
        query = Major.query.filter(Major.category_id == category_id)
        
        if education_level:
            query = query.filter(Major.education_level == education_level)
        
        return query.all()
    
    @staticmethod
    def parse_major_requirement(requirement_text: str) -> List[MajorCategory]:
        """
        解析岗位的专业要求，返回匹配的专业大类
        
        Args:
            requirement_text: 岗位的专业要求文本（如"法律类、经济类"）
            
        Returns:
            匹配的专业大类列表
        """
        if not requirement_text:
            return []
        
        # 如果是"不限"，返回空列表（表示所有专业都可以）
        if '不限' in requirement_text:
            return []
        
        matched_categories = []
        
        # 获取所有专业大类
        all_categories = MajorCategory.query.all()
        
        for category in all_categories:
            # 检查大类名称是否在要求中
            category_name = category.name.replace('类', '')
            if category_name in requirement_text or category.name in requirement_text:
                matched_categories.append(category)
        
        return matched_categories
    
    @staticmethod
    def match_major_requirement(requirement_text: str, student_major: str, 
                                 student_category_id: int = None) -> Tuple[bool, str]:
        """
        检查学员专业是否符合岗位要求
        
        Args:
            requirement_text: 岗位专业要求
            student_major: 学员专业名称
            student_category_id: 学员专业大类ID
            
        Returns:
            (是否匹配, 匹配说明)
        """
        if not requirement_text:
            return True, "专业要求为空，默认匹配"
        
        # 不限专业
        if '不限' in requirement_text:
            return True, "岗位不限专业"
        
        # 精确匹配专业名称
        if student_major and student_major in requirement_text:
            return True, f"专业名称精确匹配：{student_major}"
        
        # 大类匹配
        if student_category_id:
            category = MajorCategory.query.get(student_category_id)
            if category:
                category_name = category.name.replace('类', '')
                if category_name in requirement_text or category.name in requirement_text:
                    return True, f"专业大类匹配：{category.name}"
        
        # 尝试通过学员专业名称查找所属大类
        if student_major:
            category = MajorService.get_category_by_major(student_major)
            if category:
                category_name = category.name.replace('类', '')
                if category_name in requirement_text or category.name in requirement_text:
                    return True, f"专业大类匹配：{category.name}（通过专业名称推断）"
        
        return False, f"专业不匹配，要求：{requirement_text}"
    
    @staticmethod
    def import_majors_from_text(category_id: int, majors_text: str, 
                                 education_level: str) -> int:
        """
        从文本导入专业（用于PDF解析后的数据导入）
        
        Args:
            category_id: 专业大类ID
            majors_text: 专业名称文本（逗号或顿号分隔）
            education_level: 学历层次
            
        Returns:
            导入的专业数量
        """
        if not majors_text:
            return 0
        
        # 清理和分割文本
        # 支持的分隔符：逗号、顿号、换行
        majors_text = majors_text.replace('，', ',').replace('、', ',').replace('\n', ',')
        major_names = [m.strip() for m in majors_text.split(',') if m.strip()]
        
        count = 0
        for name in major_names:
            # 清理专业名称中的括号说明
            name = re.sub(r'（[^）]*）', '', name)
            name = re.sub(r'\([^)]*\)', '', name)
            name = name.strip()
            
            if not name or len(name) < 2:
                continue
            
            # 检查是否已存在
            existing = Major.query.filter_by(
                category_id=category_id,
                name=name,
                education_level=education_level
            ).first()
            
            if not existing:
                major = Major(
                    category_id=category_id,
                    name=name,
                    education_level=education_level
                )
                db.session.add(major)
                count += 1
        
        db.session.commit()
        return count
    
    @staticmethod
    def init_categories_if_needed():
        """如果专业大类为空，初始化50个专业大类"""
        if MajorCategory.query.count() == 0:
            for code, name in MAJOR_CATEGORIES:
                category = MajorCategory(code=code, name=name, year=2026)
                db.session.add(category)
            db.session.commit()
            return True
        return False
