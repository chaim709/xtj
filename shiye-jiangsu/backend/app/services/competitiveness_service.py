"""
竞争力评估服务
"""
from typing import Dict


class CompetitivenessService:
    """竞争力评估服务"""
    
    @staticmethod
    def evaluate(user_profile: dict) -> Dict:
        """
        评估用户竞争力
        
        Returns:
            {
                'total_score': 总分,
                'grade': 等级,
                'dimension_scores': 各维度得分,
                'strengths': 优势列表,
                'weaknesses': 弱项列表,
                'suggestions': 建议列表
            }
        """
        scores = {
            'education': 0,
            'major': 0,
            'exam_ability': 0,
            'comprehensive': 0,
            'location': 0
        }
        
        # 1. 学历背景（25分）
        education = user_profile.get('education', '本科')
        education_scores = {
            '博士': 25, '博士研究生': 25,
            '研究生': 20, '硕士': 20, '硕士研究生': 20,
            '本科': 15,
            '专科': 10, '大专': 10
        }
        scores['education'] = education_scores.get(education, 15)
        
        # 应届加分
        if user_profile.get('graduation_status') == '应届':
            scores['education'] += 2
        
        # 2. 专业匹配（20分）
        major = user_profile.get('major', '')
        
        # 热门专业评分（竞争大，分数低）
        hot_majors = ['会计', '汉语言', '法学', '工商管理', '行政管理']
        is_hot = any(hot in major for hot in hot_majors)
        
        if is_hot:
            scores['major'] = 8  # 热门专业竞争力低
        else:
            scores['major'] = 16  # 冷门专业竞争力高
        
        # 有相关证书加分
        if user_profile.get('has_certificate'):
            scores['major'] += 4
        
        # 3. 考试能力（30分）
        estimated_score = user_profile.get('estimated_score', 130)
        
        if estimated_score >= 150:
            scores['exam_ability'] = 30
        elif estimated_score >= 140:
            scores['exam_ability'] = 25
        elif estimated_score >= 130:
            scores['exam_ability'] = 20
        elif estimated_score >= 120:
            scores['exam_ability'] = 15
        else:
            scores['exam_ability'] = 10
        
        # 4. 综合素质（15分）
        # 政治面貌
        political = user_profile.get('political_status', '')
        if political == '党员':
            scores['comprehensive'] = 15
        elif political == '团员':
            scores['comprehensive'] = 10
        else:
            scores['comprehensive'] = 8
        
        # 工作经验加分
        if user_profile.get('has_work_experience'):
            scores['comprehensive'] += 3
        
        # 特殊身份加分
        if user_profile.get('special_status'):
            scores['comprehensive'] += 5
        
        scores['comprehensive'] = min(scores['comprehensive'], 15)
        
        # 5. 地域优势（10分）
        preferred_cities = user_profile.get('preferred_cities', [])
        if isinstance(preferred_cities, str):
            import json
            try:
                preferred_cities = json.loads(preferred_cities)
            except:
                preferred_cities = []
        
        if len(preferred_cities) <= 3:
            scores['location'] = 10  # 选择少，说明有明确目标
        elif len(preferred_cities) <= 6:
            scores['location'] = 7
        else:
            scores['location'] = 5
        
        # 愿意去基层加分
        if user_profile.get('base_layer_willing'):
            scores['location'] += 3
        
        scores['location'] = min(scores['location'], 10)
        
        # 总分
        total_score = sum(scores.values())
        
        # 等级评定
        if total_score >= 90:
            grade = 'S'
            grade_name = '竞争力极强'
        elif total_score >= 80:
            grade = 'A'
            grade_name = '竞争力强'
        elif total_score >= 70:
            grade = 'B'
            grade_name = '竞争力中等'
        elif total_score >= 60:
            grade = 'C'
            grade_name = '竞争力偏弱'
        else:
            grade = 'D'
            grade_name = '需要提升'
        
        # 分析优劣势
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 学历分析
        if scores['education'] >= 20:
            strengths.append('学历优势明显')
        elif scores['education'] < 15:
            weaknesses.append('学历竞争力不足')
            suggestions.append('建议提升学历（专升本或考研）')
        
        # 专业分析
        if scores['major'] >= 15:
            strengths.append('专业竞争相对较小')
        else:
            weaknesses.append('专业竞争激烈')
            suggestions.append('避开热门专业精确匹配岗位，选择专业大类或不限岗位')
        
        # 分数分析
        if scores['exam_ability'] >= 25:
            strengths.append('考试能力强，可冲刺优质岗位')
        elif scores['exam_ability'] < 20:
            weaknesses.append('预估分数偏低')
            suggestions.append('建议加强备考，冲刺到135分以上')
        
        # 综合素质分析
        if scores['comprehensive'] >= 12:
            strengths.append('综合素质较好')
        else:
            if not user_profile.get('political_status') or user_profile.get('political_status') != '党员':
                suggestions.append('建议加入中国共产党，增加竞争力')
        
        # 地域分析
        if scores['location'] >= 8:
            strengths.append('地域选择灵活')
        
        return {
            'total_score': total_score,
            'grade': grade,
            'grade_name': grade_name,
            'dimension_scores': scores,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'suggestions': suggestions
        }
