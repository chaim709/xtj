"""
推荐服务 - 核心推荐算法
"""
import json
from typing import List, Dict, Tuple
from app.models.position import Position
from app.models.recommendation import Recommendation
from app import db


class RecommendService:
    """推荐服务类"""
    
    # 学历系数映射
    EDUCATION_COEFFICIENT = {
        '博士': 3.0,
        '博士研究生': 3.0,
        '研究生': 1.8,
        '硕士': 1.8,
        '硕士研究生': 1.8,
        '本科': 1.0,
        '专科': 0.7,
        '大专': 0.7
    }
    
    # 专业匹配系数
    MAJOR_MATCH_COEFFICIENT = {
        '精确匹配': 1.5,
        '大类匹配': 1.2,
        '相关专业': 1.0,
        '不限专业': 0.8,
        '不匹配': 0.3
    }
    
    # 地域系数
    LOCAL_COEFFICIENT = 1.3  # 本地考生加成
    
    @staticmethod
    def calculate_landing_probability(position: Position, user_profile: dict) -> float:
        """
        计算上岸概率
        
        Args:
            position: 岗位对象
            user_profile: 用户画像字典
        
        Returns:
            上岸概率 (0-99)
        """
        # 基础概率（基于预估竞争比）
        competition_ratio = position.estimated_competition_ratio or 50.0
        base_prob = 1.0 / competition_ratio
        
        # 学历系数
        user_edu = user_profile.get('education', '本科')
        edu_coef = RecommendService.EDUCATION_COEFFICIENT.get(user_edu, 1.0)
        
        # 专业匹配系数
        major_match = RecommendService._match_major(
            position.major_requirement,
            user_profile.get('major', ''),
            user_profile.get('major_category', '')
        )
        major_coef = RecommendService.MAJOR_MATCH_COEFFICIENT.get(major_match, 1.0)
        
        # 分数系数
        user_score = user_profile.get('estimated_score', 130)
        score_coef = RecommendService._calculate_score_coefficient(user_score, position)
        
        # 地域系数
        user_cities = user_profile.get('preferred_cities', [])
        if isinstance(user_cities, str):
            try:
                user_cities = json.loads(user_cities)
            except:
                user_cities = []
        
        is_local = position.city in user_cities if position.city else False
        local_coef = RecommendService.LOCAL_COEFFICIENT if is_local else 1.0
        
        # 综合计算
        probability = base_prob * edu_coef * major_coef * score_coef * local_coef * 100
        
        # 限制在1-99之间
        return min(max(probability, 1), 99)
    
    @staticmethod
    def _match_major(position_major_req: str, user_major: str, user_major_category: str) -> str:
        """
        判断专业匹配度
        
        Returns:
            匹配类型：精确匹配/大类匹配/相关专业/不限专业/不匹配
        """
        if not position_major_req:
            return '不限专业'
        
        position_major_req = position_major_req.lower()
        
        # 检查专业不限
        if '不限' in position_major_req or '专业不限' in position_major_req:
            return '不限专业'
        
        if not user_major:
            return '不匹配'
        
        user_major = user_major.lower()
        
        # 精确匹配
        if user_major in position_major_req:
            return '精确匹配'
        
        # 大类匹配
        if user_major_category and user_major_category.lower() in position_major_req:
            return '大类匹配'
        
        # 检查常见相关词
        related_keywords = ['类', '相关', '或']
        if any(keyword in position_major_req for keyword in related_keywords):
            return '相关专业'
        
        return '不匹配'
    
    @staticmethod
    def _calculate_score_coefficient(user_score: int, position: Position) -> float:
        """
        计算分数系数
        
        基于用户分数与历年最低分的差距
        """
        min_score = position.min_entry_score or 125  # 默认最低分125
        
        diff = user_score - min_score
        
        if diff >= 20:
            return 1.8  # 远高于最低分
        elif diff >= 10:
            return 1.5  # 明显高于最低分
        elif diff >= 5:
            return 1.2  # 略高于最低分
        elif diff >= 0:
            return 1.0  # 达到最低分
        elif diff >= -5:
            return 0.8  # 略低于最低分
        else:
            return 0.5  # 明显低于最低分
    
    @staticmethod
    def calculate_recommendation_score(position: Position, user_profile: dict) -> float:
        """
        计算综合推荐评分
        
        综合评分 = Σ(维度分数 × 权重)
        """
        score = 0.0
        
        # 1. 上岸概率 (30%)
        landing_prob = RecommendService.calculate_landing_probability(position, user_profile)
        score += landing_prob * 0.30
        
        # 2. 待遇水平 (25%)
        salary_score = RecommendService._normalize_salary(position.estimated_salary or 8)
        score += salary_score * 0.25
        
        # 3. 发展空间 (20%)
        development_score = RecommendService._calculate_development_score(position)
        score += development_score * 0.20
        
        # 4. 生活质量 (15%)
        life_quality = RecommendService._calculate_life_quality(position.city)
        score += life_quality * 0.15
        
        # 5. 综合评价 (10%)
        overall_score = 75.0  # 默认中等评价
        score += overall_score * 0.10
        
        return min(score, 100.0)
    
    @staticmethod
    def _normalize_salary(salary: int) -> float:
        """
        薪资归一化到0-100分
        
        薪资范围：6-30万，映射到0-100分
        """
        min_salary = 6
        max_salary = 30
        
        normalized = ((salary - min_salary) / (max_salary - min_salary)) * 100
        return min(max(normalized, 0), 100)
    
    @staticmethod
    def _calculate_development_score(position: Position) -> float:
        """
        计算发展空间评分
        
        基于：单位层级、地域、系统类型
        """
        score = 50.0  # 基础分
        
        # 省直加分
        if position.affiliation == '省':
            score += 20
        elif position.affiliation == '市':
            score += 10
        
        # 系统类型加分
        high_development_systems = ['教育系统', '医疗卫生', '科研院所']
        if any(sys in (position.system_type or '') for sys in high_development_systems):
            score += 15
        
        # 城市加分
        tier1_cities = ['合肥市', '芜湖市', '马鞍山市']
        if position.city in tier1_cities:
            score += 15
        
        return min(score, 100)
    
    @staticmethod
    def _calculate_life_quality(city: str) -> float:
        """
        计算生活质量评分
        
        基于：经济发展、房价、配套设施
        """
        # 城市评分映射（基于报告数据）
        city_scores = {
            '省直': 85,
            '合肥市': 90,
            '芜湖市': 85,
            '马鞍山市': 80,
            '铜陵市': 75,
            '黄山市': 75,
            '淮南市': 70,
            '阜阳市': 65,
            '六安市': 70,
            '宣城市': 72,
            '安庆市': 70,
            '池州市': 65,
            '滁州市': 72,
            '淮北市': 65,
            '宿州市': 60,
            '蚌埠市': 68
        }
        
        return city_scores.get(city, 65)
    
    @staticmethod
    def classify_recommendation_type(landing_probability: float) -> str:
        """
        分类推荐类型
        
        Args:
            landing_probability: 上岸概率
        
        Returns:
            冲刺型/稳妥型/保底型
        """
        if landing_probability >= 85:
            return '保底型'
        elif landing_probability >= 70:
            return '稳妥型'
        else:
            return '冲刺型'
    
    @staticmethod
    def recommend_positions(user_profile: dict, limit: int = 20) -> Dict[str, List]:
        """
        为用户推荐岗位
        
        Args:
            user_profile: 用户画像
            limit: 推荐数量限制
        
        Returns:
            {
                'challenge': [冲刺型岗位],
                'stable': [稳妥型岗位],
                'safe': [保底型岗位]
            }
        """
        # 获取符合条件的岗位（江苏版默认 2025 年）
        target_year = user_profile.get('year', 2025)
        query = Position.query.filter(Position.year == target_year)
        
        # 学历筛选
        education = user_profile.get('education', '本科')
        query = RecommendService._filter_by_education(query, education)
        
        # 专业筛选
        major = user_profile.get('major', '')
        if major:
            query = RecommendService._filter_by_major(query, major)
        
        # 地域筛选
        preferred_cities = user_profile.get('preferred_cities', [])
        if isinstance(preferred_cities, str):
            try:
                preferred_cities = json.loads(preferred_cities)
            except:
                preferred_cities = []
        
        if preferred_cities:
            query = query.filter(Position.city.in_(preferred_cities))
        
        # 获取所有匹配岗位
        positions = query.all()
        
        # 计算每个岗位的推荐评分和上岸概率
        scored_positions = []
        for pos in positions:
            landing_prob = RecommendService.calculate_landing_probability(pos, user_profile)
            rec_score = RecommendService.calculate_recommendation_score(pos, user_profile)
            rec_type = RecommendService.classify_recommendation_type(landing_prob)
            
            scored_positions.append({
                'position': pos,
                'landing_probability': landing_prob,
                'recommendation_score': rec_score,
                'recommendation_type': rec_type
            })
        
        # 按推荐评分排序
        scored_positions.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        # 分类
        challenge = [p for p in scored_positions if p['recommendation_type'] == '冲刺型'][:5]
        stable = [p for p in scored_positions if p['recommendation_type'] == '稳妥型'][:8]
        safe = [p for p in scored_positions if p['recommendation_type'] == '保底型'][:5]
        
        return {
            'challenge': challenge,
            'stable': stable,
            'safe': safe,
            'total_matched': len(positions)
        }
    
    @staticmethod
    def _filter_by_education(query, user_education: str):
        """按学历筛选"""
        education_mapping = {
            '博士': ['博士', '博士及以上', '研究生及以上', '不限'],
            '博士研究生': ['博士', '博士及以上', '研究生及以上', '不限'],
            '研究生': ['研究生', '研究生及以上', '硕士及以上', '本科及以上', '不限'],
            '硕士': ['研究生', '研究生及以上', '硕士及以上', '本科及以上', '不限'],
            '硕士研究生': ['研究生', '研究生及以上', '硕士及以上', '本科及以上', '不限'],
            '本科': ['本科', '本科及以上', '大专及以上', '不限'],
            '专科': ['专科', '大专', '大专及以上', '不限'],
            '大专': ['专科', '大专', '大专及以上', '不限']
        }
        
        allowed_edu = education_mapping.get(user_education, ['不限'])
        
        # 构建OR条件
        from sqlalchemy import or_
        conditions = []
        for edu in allowed_edu:
            conditions.append(Position.education.contains(edu))
        conditions.append(Position.education.is_(None))  # 包含未明确的
        
        return query.filter(or_(*conditions))
    
    @staticmethod
    def _filter_by_major(query, user_major: str):
        """按专业筛选"""
        from sqlalchemy import or_
        
        conditions = [
            Position.major_requirement.contains(user_major),
            Position.major_requirement.contains('不限'),
            Position.major_requirement.is_(None)
        ]
        
        return query.filter(or_(*conditions))
