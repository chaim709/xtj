"""
岗位筛选服务 - 核心匹配逻辑
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from sqlalchemy import or_, and_
from app import db
from app.models.position import Position, StudentPosition
from app.models.student import Student
from app.models.major import MajorCategory, Major
from app.services.major_service import MajorService


class PositionService:
    """岗位筛选服务类"""
    
    # 学历匹配规则
    EDUCATION_RULES = {
        '专科': ['大专及以上', '大专或本科', '不限'],
        '本科': ['本科及以上', '仅限本科', '大专及以上', '大专或本科', '不限'],
        '研究生': ['研究生及以上', '仅限研究生', '本科及以上', '硕士研究生及以上', '大专及以上', '不限'],
        '博士': ['博士及以上', '仅限博士', '研究生及以上', '硕士研究生及以上', '本科及以上', '大专及以上', '不限'],
    }
    
    # 政治面貌匹配规则
    POLITICAL_RULES = {
        '党员': ['中共党员', '中共党员（含预备）', '不限', None, ''],
        '预备党员': ['中共党员', '中共党员（含预备）', '不限', None, ''],
        '团员': ['共青团员', '不限', None, ''],
        '群众': ['不限', None, ''],
    }
    
    @staticmethod
    def search_positions(filters: Dict[str, Any], page: int = 1, 
                         per_page: int = 20) -> Tuple[List[Position], int]:
        """
        搜索岗位
        
        Args:
            filters: 筛选条件
                - year: 年份
                - exam_type: 考试类型
                - city: 城市
                - department_name: 单位名称（模糊）
                - position_name: 职位名称（模糊）
                - education: 学历
                - major: 专业搜索（模糊匹配专业要求）
                - keyword: 关键词搜索
            page: 页码
            per_page: 每页数量
            
        Returns:
            (岗位列表, 总数)
        """
        query = Position.query
        
        # 年份筛选
        if filters.get('year'):
            query = query.filter(Position.year == filters['year'])
        
        # 考试类型
        if filters.get('exam_type'):
            query = query.filter(Position.exam_type == filters['exam_type'])
        
        # 城市
        if filters.get('city'):
            query = query.filter(Position.city == filters['city'])
        
        # 系统类型
        if filters.get('system_type'):
            query = query.filter(Position.system_type == filters['system_type'])
        
        # 单位名称模糊搜索
        if filters.get('department_name'):
            query = query.filter(Position.department_name.contains(filters['department_name']))
        
        # 职位名称模糊搜索
        if filters.get('position_name'):
            query = query.filter(Position.position_name.contains(filters['position_name']))
        
        # 学历筛选（支持模糊匹配）
        if filters.get('education'):
            query = query.filter(Position.education.contains(filters['education']))
        
        # 专业搜索（模糊匹配专业要求字段）
        if filters.get('major'):
            major = filters['major']
            query = query.filter(Position.major_requirement.contains(major))
        
        # 关键词搜索（全文搜索）
        if filters.get('keyword'):
            keyword = filters['keyword']
            query = query.filter(or_(
                Position.department_name.contains(keyword),
                Position.position_name.contains(keyword),
                Position.position_desc.contains(keyword),
                Position.major_requirement.contains(keyword),
                Position.other_requirements.contains(keyword)
            ))
        
        # 排序
        sort_by = filters.get('sort_by', 'competition_ratio')
        sort_order = filters.get('sort_order', 'asc')
        
        if sort_by == 'competition_ratio':
            if sort_order == 'asc':
                query = query.order_by(Position.competition_ratio.asc().nullslast())
            else:
                query = query.order_by(Position.competition_ratio.desc().nullsfirst())
        elif sort_by == 'min_entry_score':
            if sort_order == 'asc':
                query = query.order_by(Position.min_entry_score.asc().nullslast())
            else:
                query = query.order_by(Position.min_entry_score.desc().nullsfirst())
        elif sort_by == 'recruit_count':
            # 招录人数默认降序（人多的在前）
            query = query.order_by(Position.recruit_count.desc())
        else:
            # 默认按职位代码排序
            query = query.order_by(Position.position_code.asc())
        
        # 分页
        total = query.count()
        positions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return positions, total
    
    @staticmethod
    def match_positions_for_student(student_id: int, year: int = 2026,
                                     exam_type: str = '省考',
                                     filters: Dict[str, Any] = None) -> List[Dict]:
        """
        根据学员条件匹配岗位
        
        Args:
            student_id: 学员ID
            year: 年份
            exam_type: 考试类型
            filters: 额外筛选条件（城市、单位类型等）
            
        Returns:
            匹配的岗位列表（带匹配信息）
        """
        student = Student.query.get(student_id)
        if not student:
            return []
        
        # 检查学员信息完整性
        if not student.is_position_eligible():
            return []
        
        # 获取所有岗位
        query = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type
        )
        
        # 应用额外筛选
        if filters:
            if filters.get('city'):
                query = query.filter(Position.city == filters['city'])
            if filters.get('department_name'):
                query = query.filter(Position.department_name.contains(filters['department_name']))
        
        positions = query.all()
        
        # 逐个匹配
        matched = []
        for position in positions:
            match_result = PositionService._match_single_position(student, position)
            if match_result['is_match']:
                matched.append({
                    'position': position.to_dict(),
                    'match_score': match_result['score'],
                    'match_details': match_result['details'],
                    'difficulty_level': position.difficulty_level,
                    'difficulty_score': position.difficulty_score,
                })
        
        # 按匹配分数排序
        matched.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matched
    
    @staticmethod
    def _match_single_position(student: Student, position: Position) -> Dict:
        """
        匹配单个岗位
        
        Returns:
            {
                'is_match': bool,
                'score': float,  # 匹配分数 0-100
                'details': {
                    'education': {'match': bool, 'reason': str},
                    'major': {'match': bool, 'reason': str},
                    'political': {'match': bool, 'reason': str},
                    'work_years': {'match': bool, 'reason': str},
                    'age': {'match': bool, 'reason': str},
                    'other': {'match': bool, 'reason': str},
                }
            }
        """
        details = {}
        all_match = True
        total_score = 0
        
        # 1. 学历匹配 (20分)
        edu_match, edu_reason = PositionService._match_education(
            student.education, position.education
        )
        details['education'] = {'match': edu_match, 'reason': edu_reason}
        if not edu_match:
            all_match = False
        else:
            total_score += 20
        
        # 2. 专业匹配 (30分)
        major_match, major_reason = MajorService.match_major_requirement(
            position.major_requirement,
            student.major,
            student.major_category_id
        )
        details['major'] = {'match': major_match, 'reason': major_reason}
        if not major_match:
            all_match = False
        else:
            total_score += 30
        
        # 3. 政治面貌匹配 (15分)
        political_match, political_reason = PositionService._match_political_status(
            student.political_status, position.other_requirements
        )
        details['political'] = {'match': political_match, 'reason': political_reason}
        if not political_match:
            all_match = False
        else:
            total_score += 15
        
        # 4. 基层工作年限匹配 (15分)
        work_match, work_reason = PositionService._match_work_years(
            student.work_years, position.other_requirements
        )
        details['work_years'] = {'match': work_match, 'reason': work_reason}
        if not work_match:
            all_match = False
        else:
            total_score += 15
        
        # 5. 年龄匹配 (10分)
        age_match, age_reason = PositionService._match_age(
            student.age, position.other_requirements, student.education
        )
        details['age'] = {'match': age_match, 'reason': age_reason}
        if not age_match:
            all_match = False
        else:
            total_score += 10
        
        # 6. 其他条件匹配 (10分) - 性别等
        other_match, other_reason = PositionService._match_other_requirements(
            student, position.other_requirements
        )
        details['other'] = {'match': other_match, 'reason': other_reason}
        if not other_match:
            all_match = False
        else:
            total_score += 10
        
        return {
            'is_match': all_match,
            'score': total_score,
            'details': details
        }
    
    @staticmethod
    def _match_education(student_edu: str, position_edu: str) -> Tuple[bool, str]:
        """匹配学历"""
        if not position_edu or position_edu == '不限':
            return True, "岗位不限学历"
        
        if not student_edu:
            return False, "学员学历信息缺失"
        
        # 标准化学历名称
        student_edu = student_edu.replace('硕士', '研究生').replace('本科生', '本科').replace('专科生', '专科')
        
        # 获取学员可报考的学历要求
        allowed_requirements = PositionService.EDUCATION_RULES.get(student_edu, [])
        
        # 检查岗位要求是否在可报考范围内
        for allowed in allowed_requirements:
            if allowed in position_edu:
                return True, f"学历匹配：{student_edu} 可报考 {position_edu}"
        
        return False, f"学历不匹配：{student_edu} 不能报考 {position_edu}"
    
    @staticmethod
    def _match_political_status(student_political: str, 
                                 other_requirements: str) -> Tuple[bool, str]:
        """匹配政治面貌"""
        if not other_requirements:
            return True, "岗位无政治面貌要求"
        
        # 检查是否有党员要求
        has_party_requirement = any(kw in other_requirements for kw in 
                                    ['中共党员', '党员'])
        
        if not has_party_requirement:
            return True, "岗位不要求党员"
        
        if not student_political:
            return False, "学员政治面貌信息缺失"
        
        # 党员和预备党员都可以报考要求党员的岗位
        if student_political in ['党员', '预备党员']:
            return True, f"政治面貌匹配：{student_political} 符合党员要求"
        
        return False, f"政治面貌不匹配：{student_political} 不符合党员要求"
    
    @staticmethod
    def _match_work_years(student_years: int, 
                          other_requirements: str) -> Tuple[bool, str]:
        """匹配基层工作年限"""
        if not other_requirements:
            return True, "岗位无工作年限要求"
        
        student_years = student_years or 0
        
        # 解析工作年限要求
        import re
        
        # 常见格式："两年以上基层工作经历"、"具有2年以上"
        patterns = [
            r'(\d+)年以上.*(?:基层)?.*(?:工作|经历)',
            r'(?:两|二)年以上.*(?:基层)?.*(?:工作|经历)',
            r'(?:三)年以上.*(?:基层)?.*(?:工作|经历)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, other_requirements)
            if match:
                if '两' in pattern or '二' in pattern:
                    required_years = 2
                elif '三' in pattern:
                    required_years = 3
                else:
                    required_years = int(match.group(1))
                
                if student_years >= required_years:
                    return True, f"工作年限匹配：{student_years}年 >= 要求{required_years}年"
                else:
                    return False, f"工作年限不足：{student_years}年 < 要求{required_years}年"
        
        return True, "岗位无明确工作年限要求"
    
    @staticmethod
    def _match_age(student_age: int, other_requirements: str,
                   education: str = None) -> Tuple[bool, str]:
        """匹配年龄"""
        if not student_age:
            return True, "学员年龄信息缺失，跳过年龄检查"
        
        # 默认年龄限制
        max_age = 35
        
        # 研究生可放宽到40岁
        if education and '研究生' in education:
            max_age = 40
        
        # 检查其他条件中是否有特殊年龄要求
        if other_requirements:
            import re
            age_match = re.search(r'(\d+)周?岁以下', other_requirements)
            if age_match:
                max_age = int(age_match.group(1))
        
        if student_age <= max_age:
            return True, f"年龄匹配：{student_age}岁 <= {max_age}岁"
        
        return False, f"年龄超限：{student_age}岁 > {max_age}岁"
    
    @staticmethod
    def _match_other_requirements(student: Student, 
                                   other_requirements: str) -> Tuple[bool, str]:
        """匹配其他条件（性别等）"""
        if not other_requirements:
            return True, "岗位无其他特殊要求"
        
        reasons = []
        
        # 性别匹配
        if '男性' in other_requirements or '限男' in other_requirements:
            if student.gender != '男':
                return False, "岗位限男性"
            reasons.append("性别匹配")
        elif '女性' in other_requirements or '限女' in other_requirements:
            if student.gender != '女':
                return False, "岗位限女性"
            reasons.append("性别匹配")
        
        # 可以扩展更多条件检查...
        # 如：证书要求、户籍要求等
        
        if reasons:
            return True, '；'.join(reasons)
        return True, "其他条件匹配"
    
    @staticmethod
    def get_position_detail(position_id: int) -> Optional[Dict]:
        """获取岗位详情"""
        position = Position.query.get(position_id)
        if not position:
            return None
        
        data = position.to_dict()
        data['difficulty_level'] = position.difficulty_level
        data['difficulty_score'] = position.difficulty_score
        
        return data
    
    @staticmethod
    def get_cities(year: int = 2026, exam_type: str = '省考') -> List[str]:
        """获取城市列表"""
        cities = db.session.query(Position.city).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.city.isnot(None)
        ).distinct().all()
        
        return sorted([c[0] for c in cities if c[0]])
    
    @staticmethod
    def get_system_types(year: int = 2026, exam_type: str = '省考') -> List[str]:
        """获取系统类型列表"""
        types = db.session.query(Position.system_type).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.system_type.isnot(None)
        ).distinct().all()
        
        return [t[0] for t in types if t[0]]
    
    @staticmethod
    def get_statistics(year: int = 2026, exam_type: str = '省考') -> Dict:
        """获取统计信息"""
        query = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type
        )
        
        total = query.count()
        
        # 按城市统计
        by_city = dict(
            db.session.query(Position.city, db.func.count(Position.id))
            .filter(Position.year == year, Position.exam_type == exam_type)
            .group_by(Position.city)
            .all()
        )
        
        # 按考试类别统计
        by_category = dict(
            db.session.query(Position.exam_category, db.func.count(Position.id))
            .filter(Position.year == year, Position.exam_type == exam_type)
            .group_by(Position.exam_category)
            .all()
        )
        
        # 招录人数总计
        total_recruit = db.session.query(db.func.sum(Position.recruit_count)).filter(
            Position.year == year, Position.exam_type == exam_type
        ).scalar() or 0
        
        return {
            'total_positions': total,
            'total_recruit': int(total_recruit),
            'by_city': by_city,
            'by_category': by_category,
        }
