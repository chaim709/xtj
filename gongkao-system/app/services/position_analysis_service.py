"""
岗位分析服务 - 数据分析集成
提供岗位竞争度、性价比等分析功能
"""
from typing import Dict, Any, Optional
from app.models.position import Position


class PositionAnalysisService:
    """
    岗位分析服务
    
    提供岗位的多维度数据分析，包括：
    - 竞争度预测
    - 性价比评估
    - 地市发展评级
    - 综合分析报告
    """
    
    # 地市发展评级（1-10分）
    CITY_RATING = {
        '省直': 10,
        '合肥市': 10,
        '芜湖市': 8,
        '马鞍山市': 8,
        '滁州市': 8,
        '六安市': 6,
        '阜阳市': 6,
        '淮南市': 6,
        '安庆市': 6,
        '蚌埠市': 6,
        '铜陵市': 6,
        '宿州市': 4,
        '淮北市': 4,
        '黄山市': 4,
        '池州市': 4,
        '宣城市': 4
    }
    
    @staticmethod
    def calculate_competition_score(position: Position) -> Dict[str, Any]:
        """
        计算岗位竞争度分数（0-100）
        
        分数越高表示竞争越激烈
        
        权重分配：
        - 招录人数（40%）：人数越少竞争越大
        - 学历要求（30%）：要求越高竞争越小
        - 专业限制（20%）：限制越多竞争越小
        - 其他条件（10%）：有特殊要求竞争越小
        
        Args:
            position: 岗位对象
            
        Returns:
            {
                'score': float,      # 竞争度分数 0-100
                'level': str,        # 竞争度等级 low/medium/high
                'level_text': str,   # 中文等级
                'details': Dict      # 详细评分
            }
        """
        score = 0
        details = {}
        
        # 1. 招录人数（40%）- 人数越少竞争越大
        recruit_count = position.recruit_count or 1
        if recruit_count == 1:
            recruit_score = 100
            recruit_text = "仅招1人，竞争激烈"
        elif recruit_count <= 3:
            recruit_score = 80
            recruit_text = f"招录{recruit_count}人，竞争较大"
        elif recruit_count <= 5:
            recruit_score = 60
            recruit_text = f"招录{recruit_count}人，竞争中等"
        elif recruit_count <= 10:
            recruit_score = 40
            recruit_text = f"招录{recruit_count}人，竞争较小"
        else:
            recruit_score = 20
            recruit_text = f"招录{recruit_count}人，竞争很小"
        
        score += recruit_score * 0.4
        details['recruit'] = {
            'score': recruit_score,
            'count': recruit_count,
            'text': recruit_text
        }
        
        # 2. 学历要求（30%）- 要求越高竞争越小
        education = position.education or ''
        if '博士' in education:
            edu_score = 20
            edu_text = "要求博士，竞争很小"
        elif '研究生' in education and ('仅限' in education or '硕士' in education):
            edu_score = 30
            edu_text = "仅限研究生，竞争较小"
        elif '研究生' in education or '硕士' in education:
            edu_score = 40
            edu_text = "研究生及以上，竞争较小"
        elif '本科' in education and '仅限' in education:
            edu_score = 60
            edu_text = "仅限本科，竞争中等"
        elif '本科' in education:
            edu_score = 70
            edu_text = "本科及以上，竞争较大"
        elif '大专' in education:
            edu_score = 80
            edu_text = "大专及以上，竞争大"
        else:
            edu_score = 90
            edu_text = "学历不限，竞争激烈"
        
        score += edu_score * 0.3
        details['education'] = {
            'score': edu_score,
            'requirement': education or '未明确',
            'text': edu_text
        }
        
        # 3. 专业限制（20%）- 限制越多竞争越小
        major = position.major_requirement or ''
        if '不限' in major:
            major_score = 100
            major_text = "专业不限，竞争激烈"
        elif len(major) > 50:
            major_score = 40
            major_text = "专业限制较多，竞争较小"
        elif len(major) > 20:
            major_score = 60
            major_text = "专业限制中等，竞争中等"
        elif len(major) > 0:
            major_score = 80
            major_text = "专业有限制，竞争较大"
        else:
            major_score = 90
            major_text = "专业未明确，竞争大"
        
        score += major_score * 0.2
        details['major'] = {
            'score': major_score,
            'requirement': major[:50] + ('...' if len(major) > 50 else ''),
            'text': major_text
        }
        
        # 4. 其他条件（10%）- 有特殊要求竞争小
        other = position.other_requirements or ''
        other_score = 100  # 默认无特殊要求
        conditions = []
        
        if '党员' in other or '中共党员' in other:
            other_score -= 20
            conditions.append("要求党员")
        if '基层' in other and '年' in other:
            other_score -= 20
            conditions.append("要求基层经历")
        if '应届' in other:
            other_score -= 10
            conditions.append("限应届生")
        
        other_score = max(other_score, 20)
        
        if conditions:
            other_text = f"有特殊要求（{','.join(conditions)}），竞争较小"
        else:
            other_text = "无特殊要求，竞争较大"
        
        score += other_score * 0.1
        details['other'] = {
            'score': other_score,
            'requirements': other[:50] + ('...' if len(other) > 50 else ''),
            'text': other_text,
            'conditions': conditions
        }
        
        # 确定竞争度等级
        final_score = round(score, 1)
        if final_score < 40:
            level = 'low'
            level_text = '低竞争'
        elif final_score < 70:
            level = 'medium'
            level_text = '中等竞争'
        else:
            level = 'high'
            level_text = '高竞争'
        
        return {
            'score': final_score,
            'level': level,
            'level_text': level_text,
            'details': details
        }
    
    @staticmethod
    def calculate_value_score(position: Position) -> Dict[str, Any]:
        """
        计算岗位性价比分数（0-100）
        
        分数越高表示性价比越好
        
        权重分配：
        - 竞争度（40%）：竞争越低性价比越高
        - 地域发展（30%）：发达地区性价比高
        - 单位等级（20%）：级别越高性价比越高
        - 岗位稳定性（10%）：编制岗位稳定性高
        
        Args:
            position: 岗位对象
            
        Returns:
            {
                'score': float,      # 性价比分数 0-100
                'level': str,        # 性价比等级 high/medium/low
                'level_text': str,   # 中文等级
                'details': Dict      # 详细评分
            }
        """
        score = 0
        details = {}
        
        # 1. 竞争度（40%）- 竞争越低性价比越高（反转分数）
        competition = PositionAnalysisService.calculate_competition_score(position)
        comp_value = 100 - competition['score']  # 反转：竞争低=分数高
        score += comp_value * 0.4
        details['competition'] = {
            'value': round(comp_value, 1),
            'original_score': competition['score'],
            'level': competition['level'],
            'text': f"竞争度{competition['level_text']}，性价比{'高' if comp_value > 60 else '中等' if comp_value > 30 else '低'}"
        }
        
        # 2. 地域发展（30%）
        city = position.city or ''
        city_rating = PositionAnalysisService.CITY_RATING.get(city, 4)
        city_score = city_rating * 10  # 转换为0-100分
        score += city_score * 0.3
        
        if city_rating >= 9:
            city_text = f"{city}为发达地区，发展前景好"
        elif city_rating >= 7:
            city_text = f"{city}为较发达地区，发展前景较好"
        elif city_rating >= 5:
            city_text = f"{city}为一般地区，发展前景一般"
        else:
            city_text = f"{city}为欠发达地区，发展前景有限"
        
        details['city'] = {
            'name': city,
            'rating': city_rating,
            'score': city_score,
            'text': city_text
        }
        
        # 3. 单位等级（20%）
        dept = position.department_name or ''
        
        # 从单位名称推断等级
        if '省' in dept[:2]:  # 省开头
            if any(k in dept for k in ['厅', '局', '委', '办']):
                unit_score = 95
                unit_text = "省级厅局单位，级别高"
            else:
                unit_score = 90
                unit_text = "省级单位，级别高"
        elif '市' in dept[:3]:  # 市开头
            if any(k in dept for k in ['局', '委', '办']):
                unit_score = 75
                unit_text = "市级局委单位，级别较高"
            else:
                unit_score = 70
                unit_text = "市级单位，级别较高"
        elif '县' in dept or '区' in dept:
            unit_score = 50
            unit_text = "县区级单位，级别一般"
        elif '乡' in dept or '镇' in dept:
            unit_score = 30
            unit_text = "乡镇级单位，级别较低"
        else:
            # 其他单位（学校、医院等）
            if any(k in dept for k in ['大学', '学院']):
                unit_score = 85
                unit_text = "高校单位，待遇较好"
            elif '医院' in dept:
                unit_score = 80
                unit_text = "医院单位，待遇较好"
            else:
                unit_score = 60
                unit_text = "事业单位，待遇一般"
        
        score += unit_score * 0.2
        details['unit'] = {
            'name': dept[:30] + ('...' if len(dept) > 30 else ''),
            'score': unit_score,
            'text': unit_text
        }
        
        # 4. 岗位稳定性（10%）
        # 事业单位都是编制，稳定性较高
        stability_score = 80  # 基础分
        
        # 如果是公益一类，更稳定
        if '公益一类' in (position.other_requirements or ''):
            stability_score = 95
            stability_text = "公益一类，全额拨款，稳定性很高"
        elif '公益二类' in (position.other_requirements or ''):
            stability_score = 85
            stability_text = "公益二类，差额拨款，稳定性高"
        else:
            stability_text = "事业编制，稳定性较高"
        
        score += stability_score * 0.1
        details['stability'] = {
            'score': stability_score,
            'text': stability_text
        }
        
        # 确定性价比等级
        final_score = round(score, 1)
        if final_score >= 70:
            level = 'high'
            level_text = '高性价比'
        elif final_score >= 40:
            level = 'medium'
            level_text = '中等性价比'
        else:
            level = 'low'
            level_text = '低性价比'
        
        return {
            'score': final_score,
            'level': level,
            'level_text': level_text,
            'details': details
        }
    
    @staticmethod
    def analyze_position(position: Position) -> Dict[str, Any]:
        """
        综合分析岗位
        
        对岗位进行全方位分析，包括竞争度、性价比、地市评级等
        
        Args:
            position: 岗位对象
            
        Returns:
            {
                'position_id': int,
                'position_name': str,
                'department_name': str,
                'city': str,
                'competition': Dict,      # 竞争度分析
                'value': Dict,            # 性价比分析
                'city_rating': int,       # 地市评级 1-10
                'recommendation': str     # 推荐建议
            }
        """
        # 计算各项指标
        competition = PositionAnalysisService.calculate_competition_score(position)
        value = PositionAnalysisService.calculate_value_score(position)
        
        # 地市评级
        city = position.city or ''
        city_rating = PositionAnalysisService.CITY_RATING.get(city, 4)
        
        # 生成推荐建议
        recommendation = PositionAnalysisService._generate_recommendation(
            position, competition, value, city_rating
        )
        
        return {
            'position_id': position.id,
            'position_name': position.position_name,
            'department_name': position.department_name,
            'city': city,
            'recruit_count': position.recruit_count,
            'education': position.education,
            'major_requirement': position.major_requirement,
            'competition': competition,
            'value': value,
            'city_rating': city_rating,
            'recommendation': recommendation
        }
    
    @staticmethod
    def _generate_recommendation(
        position: Position,
        competition: Dict,
        value: Dict,
        city_rating: int
    ) -> str:
        """
        生成推荐建议
        
        根据分析结果生成针对性的建议
        """
        suggestions = []
        
        # 基于性价比
        if value['level'] == 'high':
            suggestions.append("该岗位性价比高")
        elif value['level'] == 'low':
            suggestions.append("该岗位性价比一般")
        
        # 基于竞争度
        if competition['level'] == 'low':
            suggestions.append("竞争压力小，上岸机会大")
        elif competition['level'] == 'medium':
            suggestions.append("竞争度适中")
        elif competition['level'] == 'high':
            suggestions.append("竞争激烈，需充分准备")
        
        # 基于地域
        if city_rating >= 9:
            suggestions.append("地处发达地区，发展前景好")
        elif city_rating <= 4:
            suggestions.append("地处偏远地区，生活成本较低")
        
        # 基于招录人数
        if position.recruit_count and position.recruit_count >= 5:
            suggestions.append("招录人数较多，机会较大")
        
        # 综合建议
        if value['score'] >= 70 and competition['score'] < 60:
            conclusion = "强烈推荐报考"
        elif value['score'] >= 60:
            conclusion = "推荐报考"
        elif competition['score'] >= 70:
            conclusion = "谨慎报考，需评估自身实力"
        else:
            conclusion = "可作为备选"
        
        return f"{conclusion}。{'，'.join(suggestions)}。"
    
    @staticmethod
    def get_city_rating(city: str) -> int:
        """
        获取城市发展评级
        
        Args:
            city: 城市名称
            
        Returns:
            评级分数 1-10
        """
        return PositionAnalysisService.CITY_RATING.get(city, 4)
    
    @staticmethod
    def get_all_city_ratings() -> Dict[str, int]:
        """
        获取所有城市评级
        
        Returns:
            城市评级字典
        """
        return PositionAnalysisService.CITY_RATING.copy()
