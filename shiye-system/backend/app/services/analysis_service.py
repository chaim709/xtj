"""
数据分析服务
"""
from typing import Dict, List
from sqlalchemy import func
from app.models.position import Position
from app import db


class AnalysisService:
    """数据分析服务类"""
    
    # 城市薪资映射（万元/年）
    CITY_SALARY_MAP = {
        '省直': 12,
        '合肥市': 11,
        '芜湖市': 10,
        '马鞍山市': 10,
        '铜陵市': 9,
        '淮南市': 8,
        '黄山市': 9,
        '宣城市': 8,
        '安庆市': 8,
        '池州市': 8,
        '滁州市': 8,
        '阜阳市': 7,
        '六安市': 7,
        '淮北市': 7,
        '宿州市': 7,
        '蚌埠市': 8
    }
    
    # 预估竞争比映射（基于报告分析）
    CITY_COMPETITION_MAP = {
        '省直': 45.0,
        '合肥市': 50.0,
        '芜湖市': 70.0,
        '马鞍山市': 80.0,
        '铜陵市': 50.0,
        '淮南市': 45.0,
        '黄山市': 60.0,
        '宣城市': 65.0,
        '安庆市': 55.0,
        '池州市': 40.0,
        '滁州市': 65.0,
        '阜阳市': 28.0,
        '六安市': 55.0,
        '淮北市': 35.0,
        '宿州市': 40.0,
        '蚌埠市': 50.0
    }
    
    @staticmethod
    def estimate_position_data():
        """
        为所有岗位预估数据（薪资、竞争比、难度）
        
        这个函数会更新数据库中的预估字段
        """
        positions = Position.query.all()
        
        for pos in positions:
            # 预估薪资
            if not pos.estimated_salary:
                pos.estimated_salary = AnalysisService._estimate_salary(pos)
            
            # 预估竞争比
            if not pos.estimated_competition_ratio:
                pos.estimated_competition_ratio = AnalysisService._estimate_competition_ratio(pos)
            
            # 难度等级
            if not pos.difficulty_level:
                pos.difficulty_level = AnalysisService._calculate_difficulty(pos)
        
        db.session.commit()
        return len(positions)
    
    @staticmethod
    def _estimate_salary(position: Position) -> int:
        """
        预估岗位年薪（万元）
        
        基于：地市、单位层级、系统类型
        """
        # 基础薪资（按城市）
        base_salary = AnalysisService.CITY_SALARY_MAP.get(position.city, 8)
        
        # 省直加成
        if position.affiliation == '省':
            base_salary += 2
        
        # 学历要求加成
        if position.education:
            if '博士' in position.education:
                base_salary += 10
            elif '研究生' in position.education or '硕士' in position.education:
                base_salary += 3
        
        # 系统类型调整
        if position.system_type:
            if '医疗' in position.system_type or '医院' in (position.department_name or ''):
                base_salary += 2
            elif '高校' in (position.department_name or '') or '学院' in (position.department_name or ''):
                base_salary += 1
        
        return base_salary
    
    @staticmethod
    def _estimate_competition_ratio(position: Position) -> float:
        """
        预估竞争比
        
        基于：地市、学历要求、专业限制、招聘人数
        """
        # 基础竞争比（按城市）
        base_ratio = AnalysisService.CITY_COMPETITION_MAP.get(position.city, 45.0)
        
        # 学历调整
        if position.education:
            if '博士' in position.education:
                base_ratio *= 0.05  # 博士竞争极小
            elif '研究生' in position.education and '仅限' in position.education:
                base_ratio *= 0.35  # 仅限研究生
            elif '本科' in position.education and '仅限' in position.education:
                base_ratio *= 0.7  # 仅限本科
            elif '专科' in position.education:
                base_ratio *= 1.2  # 专科竞争反而大（本科可报）
        
        # 专业限制调整
        if position.major_requirement:
            if '不限' in position.major_requirement:
                base_ratio *= 1.8  # 专业不限竞争大
            elif len(position.major_requirement) > 100:
                base_ratio *= 0.7  # 专业限制严格
        
        # 招聘人数调整
        if position.recruit_count:
            if position.recruit_count >= 5:
                base_ratio *= 0.9  # 招聘人数多，竞争略小
            elif position.recruit_count == 1:
                base_ratio *= 1.1  # 只招1人，竞争略大
        
        # 隶属关系调整
        if position.affiliation == '省':
            base_ratio *= 1.3  # 省直竞争大
        elif position.affiliation == '乡镇':
            base_ratio *= 0.5  # 基层竞争小
        
        return round(base_ratio, 1)
    
    @staticmethod
    def _calculate_difficulty(position: Position) -> str:
        """
        计算难度等级
        
        Returns:
            easy/medium/hard
        """
        ratio = position.estimated_competition_ratio or 50.0
        
        if ratio >= 60:
            return 'hard'
        elif ratio >= 35:
            return 'medium'
        else:
            return 'easy'
    
    @staticmethod
    def get_city_comparison_data() -> List[dict]:
        """
        获取城市对比数据
        
        Returns:
            城市对比数据列表
        """
        # 城市数据（基于报告）
        city_data = [
            {'city': '省直', 'positions': 674, 'recruits': 949, 'ratio': 45, 'salary': 12, 'rank': 1},
            {'city': '六安市', 'positions': 346, 'recruits': 392, 'ratio': 55, 'salary': 7, 'rank': 4},
            {'city': '阜阳市', 'positions': 278, 'recruits': 358, 'ratio': 28, 'salary': 7, 'rank': 5},
            {'city': '芜湖市', 'positions': 303, 'recruits': 338, 'ratio': 70, 'salary': 10, 'rank': 3},
            {'city': '马鞍山市', 'positions': 304, 'recruits': 327, 'ratio': 80, 'salary': 10, 'rank': 4},
            {'city': '合肥市', 'positions': 181, 'recruits': 288, 'ratio': 50, 'salary': 11, 'rank': 2},
            {'city': '淮南市', 'positions': 234, 'recruits': 271, 'ratio': 45, 'salary': 8, 'rank': 7},
            {'city': '黄山市', 'positions': 187, 'recruits': 205, 'ratio': 60, 'salary': 9, 'rank': 8},
            {'city': '铜陵市', 'positions': 161, 'recruits': 190, 'ratio': 50, 'salary': 9, 'rank': 9},
            {'city': '淮北市', 'positions': 120, 'recruits': 170, 'ratio': 35, 'salary': 7, 'rank': 10},
            {'city': '蚌埠市', 'positions': 145, 'recruits': 161, 'ratio': 50, 'salary': 8, 'rank': 11},
            {'city': '宣城市', 'positions': 138, 'recruits': 154, 'ratio': 65, 'salary': 8, 'rank': 12},
            {'city': '安庆市', 'positions': 118, 'recruits': 135, 'ratio': 55, 'salary': 8, 'rank': 13},
            {'city': '宿州市', 'positions': 96, 'recruits': 122, 'ratio': 40, 'salary': 7, 'rank': 14},
            {'city': '滁州市', 'positions': 103, 'recruits': 106, 'ratio': 65, 'salary': 8, 'rank': 15},
            {'city': '池州市', 'positions': 55, 'recruits': 55, 'ratio': 40, 'salary': 8, 'rank': 16}
        ]
        
        return city_data
    
    @staticmethod
    def analyze_position_for_user(position: Position, user_profile: dict) -> dict:
        """
        为特定用户分析岗位
        
        Returns:
            {
                'matches': {...},  # 匹配度分析
                'suggestions': [...],  # 建议列表
                'warnings': [...],  # 警告列表
                'advantages': [...],  # 优势列表
                'disadvantages': [...]  # 劣势列表
            }
        """
        from app.services.recommend_service import RecommendService
        
        # 计算匹配度
        landing_prob = RecommendService.calculate_landing_probability(position, user_profile)
        rec_score = RecommendService.calculate_recommendation_score(position, user_profile)
        
        # 学历匹配
        education_match = AnalysisService._check_education_match(position, user_profile.get('education'))
        
        # 专业匹配
        major_match = RecommendService._match_major(
            position.major_requirement,
            user_profile.get('major', ''),
            user_profile.get('major_category', '')
        )
        
        # 地域匹配
        preferred_cities = user_profile.get('preferred_cities', [])
        if isinstance(preferred_cities, str):
            import json
            try:
                preferred_cities = json.loads(preferred_cities)
            except:
                preferred_cities = []
        location_match = '优先地区' if position.city in preferred_cities else '非优先地区'
        
        # 生成建议
        suggestions = []
        warnings = []
        advantages = []
        disadvantages = []
        
        # 分析竞争度
        comp_ratio = position.estimated_competition_ratio or 50
        if comp_ratio > 70:
            warnings.append(f'竞争激烈，预估报录比{comp_ratio}:1')
            disadvantages.append('竞争压力大')
        elif comp_ratio < 30:
            advantages.append('竞争相对较小')
            suggestions.append('这是一个性价比较高的岗位')
        
        # 分析上岸概率
        if landing_prob >= 80:
            suggestions.append(f'上岸概率{landing_prob}%，建议重点考虑')
            advantages.append('上岸概率高')
        elif landing_prob < 50:
            warnings.append(f'上岸概率仅{landing_prob}%，建议谨慎报考')
        
        # 分析专业匹配
        if major_match == '精确匹配':
            advantages.append('专业完全对口，竞争优势明显')
        elif major_match == '不匹配':
            warnings.append('专业不匹配，建议核实是否可以报考')
            disadvantages.append('专业匹配度低')
        
        # 分析待遇
        if position.estimated_salary and position.estimated_salary >= 12:
            advantages.append(f'待遇较好，预估年薪{position.estimated_salary}万')
        
        return {
            'matches': {
                'education': education_match,
                'major': major_match,
                'location': location_match,
                'overall': '高度匹配' if landing_prob >= 75 else '中等匹配' if landing_prob >= 50 else '匹配度低'
            },
            'scores': {
                'landing_probability': round(landing_prob, 1),
                'recommendation_score': round(rec_score, 1)
            },
            'suggestions': suggestions,
            'warnings': warnings,
            'advantages': advantages,
            'disadvantages': disadvantages
        }
    
    @staticmethod
    def _check_education_match(position: Position, user_education: str) -> str:
        """
        检查学历匹配度
        
        Returns:
            符合/不符合/超过要求
        """
        if not position.education:
            return '符合'
        
        pos_edu = position.education
        
        # 建立学历层级
        edu_levels = {
            '专科': 1, '大专': 1,
            '本科': 2,
            '硕士': 3, '研究生': 3, '硕士研究生': 3,
            '博士': 4, '博士研究生': 4
        }
        
        user_level = edu_levels.get(user_education, 2)
        
        # 判断
        if '博士' in pos_edu and user_level >= 4:
            return '符合'
        elif '研究生' in pos_edu and user_level >= 3:
            return '符合'
        elif '本科' in pos_edu and user_level >= 2:
            return '符合'
        elif '专科' in pos_edu or '大专' in pos_edu:
            return '符合'
        elif '不限' in pos_edu:
            return '符合'
        
        # 判断是否超过要求
        if '仅限本科' in pos_edu and user_level > 2:
            return '超过要求'
        elif '仅限专科' in pos_edu and user_level > 1:
            return '超过要求'
        
        return '不符合'
