"""
岗位智能推荐服务
基于学员条件和岗位分析，提供个性化推荐
"""
from typing import List, Dict, Any, Optional, Tuple
from app.models.position import Position
from app.models.student import Student
from app.services.position_service import PositionService
from app.services.position_analysis_service import PositionAnalysisService
from app.services.major_service import MajorService


class PositionRecommendService:
    """
    岗位智能推荐服务
    
    提供基于学员条件的个性化岗位推荐，包括：
    - 岗位推荐分数计算
    - 岗位分类（冲刺/稳妥/保底）
    - 推荐理由生成
    """
    
    # 推荐策略配置
    STRATEGIES = {
        'aggressive': {  # 激进策略
            'name': '激进策略',
            'sprint_ratio': 0.30,  # 冲刺岗位占比30%
            'stable_ratio': 0.40,  # 稳妥岗位占比40%
            'safe_ratio': 0.30,    # 保底岗位占比30%
        },
        'balanced': {  # 平衡策略（默认）
            'name': '平衡策略',
            'sprint_ratio': 0.20,
            'stable_ratio': 0.50,
            'safe_ratio': 0.30,
        },
        'conservative': {  # 保守策略
            'name': '保守策略',
            'sprint_ratio': 0.10,
            'stable_ratio': 0.40,
            'safe_ratio': 0.50,
        }
    }
    
    @staticmethod
    def recommend_for_student(
        student_id: int,
        year: int = 2026,
        exam_type: str = '事业单位',
        preferences: Optional[Dict] = None,
        strategy: str = 'balanced',
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        为学员推荐岗位
        
        基于学员条件、岗位分析和偏好设置，智能推荐适合的岗位
        
        Args:
            student_id: 学员ID
            year: 年份
            exam_type: 考试类型
            preferences: 偏好设置
                {
                    'cities': List[str],  # 偏好城市
                    'department_type': str,  # 偏好单位类型
                    'min_recruit': int,  # 最少招录人数
                }
            strategy: 推荐策略 aggressive/balanced/conservative
            limit: 推荐总数限制
            
        Returns:
            {
                'success': bool,
                'student': Dict,
                'total_matched': int,
                'sprint': List[Dict],  # 冲刺岗位
                'stable': List[Dict],  # 稳妥岗位
                'safe': List[Dict],    # 保底岗位
                'summary': Dict        # 统计摘要
            }
        """
        # 获取学员信息
        student = Student.query.get(student_id)
        if not student:
            return {
                'success': False,
                'error': '学员不存在'
            }
        
        # 检查学员信息完整性
        if not student.is_position_eligible():
            return {
                'success': False,
                'error': '学员选岗信息不完整，请先完善：学历、专业、政治面貌、性别、出生日期'
            }
        
        # 构建筛选条件
        filters = {}
        if preferences and preferences.get('cities'):
            filters['cities'] = preferences['cities']
        
        # 使用PositionService匹配岗位
        matched_positions = PositionService.match_positions_for_student(
            student_id, year, exam_type, filters
        )
        
        if not matched_positions:
            return {
                'success': True,
                'student': student.to_dict(),
                'total_matched': 0,
                'sprint': [],
                'stable': [],
                'safe': [],
                'summary': {
                    'message': '未找到符合条件的岗位，建议放宽筛选条件'
                }
            }
        
        # 计算推荐分数并排序
        scored_positions = []
        for item in matched_positions:
            position = Position.query.get(item['position']['id'])
            if not position:
                continue
            
            # 计算推荐分数
            recommend_score = PositionRecommendService.calculate_recommend_score(
                position, student, preferences
            )
            
            # 获取竞争度和性价比分析
            competition = PositionAnalysisService.calculate_competition_score(position)
            value = PositionAnalysisService.calculate_value_score(position)
            
            scored_positions.append({
                'position': position,
                'match_score': item['match_score'],
                'recommend_score': recommend_score,
                'competition': competition,
                'value': value,
                'difficulty_score': item.get('difficulty_score', 0)
            })
        
        # 按推荐分数排序
        scored_positions.sort(key=lambda x: x['recommend_score'], reverse=True)
        
        # 限制数量
        if len(scored_positions) > limit:
            scored_positions = scored_positions[:limit]
        
        # 分类岗位
        classified = PositionRecommendService.classify_positions(
            scored_positions, student, strategy
        )
        
        # 生成推荐理由
        for category in ['sprint', 'stable', 'safe']:
            for item in classified[category]:
                item['reason'] = PositionRecommendService._generate_reason(
                    item, category
                )
        
        # 计算统计摘要
        summary = PositionRecommendService._calculate_summary(
            scored_positions, classified, strategy
        )
        
        return {
            'success': True,
            'student': {
                'id': student.id,
                'name': student.name,
                'education': student.education,
                'major': student.major,
                'political_status': student.political_status,
                'work_years': student.work_years
            },
            'total_matched': len(matched_positions),
            'sprint': classified['sprint'],
            'stable': classified['stable'],
            'safe': classified['safe'],
            'summary': summary
        }
    
    @staticmethod
    def calculate_recommend_score(
        position: Position,
        student: Student,
        preferences: Optional[Dict] = None
    ) -> float:
        """
        计算推荐分数（0-100）
        
        综合考虑条件匹配度、竞争度适配、偏好匹配和发展前景
        
        权重分配：
        - 条件匹配度（40%）：学历、专业、政治面貌等基础条件
        - 竞争度适配（30%）：根据学员水平匹配合适难度
        - 偏好匹配度（20%）：城市、单位类型等偏好
        - 发展前景（10%）：基于性价比评估
        
        Args:
            position: 岗位对象
            student: 学员对象
            preferences: 偏好设置
            
        Returns:
            推荐分数 0-100
        """
        score = 0
        
        # 1. 条件匹配度（40%）- 使用PositionService的匹配结果
        match_result = PositionService._match_single_position(student, position)
        if not match_result['is_match']:
            return 0  # 不符合条件，直接返回0
        
        match_score = match_result['score']  # 已经是0-100分
        score += match_score * 0.4
        
        # 2. 竞争度适配（30%）- 根据学员水平匹配合适难度
        competition = PositionAnalysisService.calculate_competition_score(position)
        comp_score = competition['score']
        
        # 假设学员水平为中等（50分），可根据历史成绩调整
        # TODO: 后续可以根据学员的模考成绩、练习情况等计算真实水平
        student_level = 50
        
        # 竞争度越接近学员水平，适配度越高
        difficulty_fit = 100 - abs(comp_score - student_level)
        score += difficulty_fit * 0.3
        
        # 3. 偏好匹配度（20%）
        preference_score = 100  # 默认满分
        
        if preferences:
            # 城市偏好
            if preferences.get('cities') and position.city:
                if position.city in preferences['cities']:
                    preference_score = 100
                else:
                    preference_score = 60  # 不在偏好城市，降低分数
            
            # 单位类型偏好
            if preferences.get('department_type'):
                dept = position.department_name or ''
                if preferences['department_type'] in dept:
                    preference_score = min(preference_score, 100)
                else:
                    preference_score = min(preference_score, 70)
            
            # 最少招录人数偏好
            if preferences.get('min_recruit'):
                if position.recruit_count and position.recruit_count >= preferences['min_recruit']:
                    preference_score = min(preference_score, 100)
                else:
                    preference_score = min(preference_score, 80)
        
        score += preference_score * 0.2
        
        # 4. 发展前景（10%）- 基于性价比评估
        value = PositionAnalysisService.calculate_value_score(position)
        prospect_score = value['score']
        score += prospect_score * 0.1
        
        return round(score, 1)
    
    @staticmethod
    def classify_positions(
        scored_positions: List[Dict],
        student: Student,
        strategy: str = 'balanced'
    ) -> Dict[str, List[Dict]]:
        """
        将岗位分类为冲刺/稳妥/保底三档
        
        分类规则：
        - 冲刺岗位：高分数、高难度、高回报
        - 稳妥岗位：中等分数、中等难度、推荐报考
        - 保底岗位：低难度、高稳定性、确保上岸
        
        Args:
            scored_positions: 已评分的岗位列表
            student: 学员对象
            strategy: 推荐策略
            
        Returns:
            {
                'sprint': List,  # 冲刺岗位
                'stable': List,  # 稳妥岗位
                'safe': List     # 保底岗位
            }
        """
        if not scored_positions:
            return {'sprint': [], 'stable': [], 'safe': []}
        
        # 获取策略配置
        strategy_config = PositionRecommendService.STRATEGIES.get(
            strategy, PositionRecommendService.STRATEGIES['balanced']
        )
        
        total = len(scored_positions)
        sprint_count = max(1, int(total * strategy_config['sprint_ratio']))
        stable_count = max(1, int(total * strategy_config['stable_ratio']))
        safe_count = max(1, int(total * strategy_config['safe_ratio']))
        
        # 按竞争度分数排序（用于区分难度）
        positions_by_competition = sorted(
            scored_positions,
            key=lambda x: x['competition']['score'],
            reverse=True
        )
        
        # 按推荐分数排序（用于选择最佳岗位）
        positions_by_recommend = sorted(
            scored_positions,
            key=lambda x: x['recommend_score'],
            reverse=True
        )
        
        # 分类逻辑
        sprint = []
        stable = []
        safe = []
        used_ids = set()
        
        # 1. 冲刺岗位：从高竞争度中选择推荐分数高的
        high_competition = [p for p in positions_by_competition 
                           if p['competition']['score'] >= 60]
        for pos in high_competition:
            if len(sprint) >= sprint_count:
                break
            if pos['position'].id not in used_ids:
                sprint.append(PositionRecommendService._format_position(pos))
                used_ids.add(pos['position'].id)
        
        # 如果高竞争不够，从推荐分数top中补充
        if len(sprint) < sprint_count:
            for pos in positions_by_recommend:
                if len(sprint) >= sprint_count:
                    break
                if pos['position'].id not in used_ids:
                    sprint.append(PositionRecommendService._format_position(pos))
                    used_ids.add(pos['position'].id)
        
        # 2. 保底岗位：从低竞争度中选择
        low_competition = [p for p in positions_by_competition 
                          if p['competition']['score'] < 40]
        low_competition.sort(key=lambda x: x['recommend_score'], reverse=True)
        for pos in low_competition:
            if len(safe) >= safe_count:
                break
            if pos['position'].id not in used_ids:
                safe.append(PositionRecommendService._format_position(pos))
                used_ids.add(pos['position'].id)
        
        # 3. 稳妥岗位：剩余的岗位
        for pos in positions_by_recommend:
            if len(stable) >= stable_count:
                break
            if pos['position'].id not in used_ids:
                stable.append(PositionRecommendService._format_position(pos))
                used_ids.add(pos['position'].id)
        
        return {
            'sprint': sprint[:sprint_count],
            'stable': stable[:stable_count],
            'safe': safe[:safe_count]
        }
    
    @staticmethod
    def _format_position(scored_pos: Dict) -> Dict:
        """
        格式化岗位数据
        """
        position = scored_pos['position']
        return {
            'position': position.to_dict(),
            'match_score': scored_pos['match_score'],
            'recommend_score': scored_pos['recommend_score'],
            'competition': scored_pos['competition'],
            'value': scored_pos['value'],
            'difficulty_score': scored_pos.get('difficulty_score', 0)
        }
    
    @staticmethod
    def _generate_reason(item: Dict, category: str) -> str:
        """
        生成推荐理由
        
        根据岗位类别和分析结果生成针对性的推荐理由
        """
        competition = item['competition']
        value = item['value']
        recommend_score = item['recommend_score']
        
        if category == 'sprint':
            # 冲刺岗位
            reasons = ["该岗位为冲刺目标"]
            if value['level'] == 'high':
                reasons.append("性价比高")
            if competition['level'] == 'high':
                reasons.append("竞争激烈")
            reasons.append("建议充分准备后冲刺")
            return '，'.join(reasons) + '。'
        
        elif category == 'stable':
            # 稳妥岗位
            reasons = ["该岗位为稳妥选择"]
            if recommend_score >= 80:
                reasons.append("推荐指数高")
            if competition['level'] == 'medium':
                reasons.append("竞争度适中")
            reasons.append("建议重点关注")
            return '，'.join(reasons) + '。'
        
        else:  # safe
            # 保底岗位
            reasons = ["该岗位为保底选择"]
            if competition['level'] == 'low':
                reasons.append("竞争压力小")
            reasons.append("上岸机会大")
            reasons.append("建议作为备选")
            return '，'.join(reasons) + '。'
    
    @staticmethod
    def _calculate_summary(
        all_positions: List[Dict],
        classified: Dict,
        strategy: str
    ) -> Dict[str, Any]:
        """
        计算统计摘要
        """
        # 平均竞争度
        avg_competition = sum(p['competition']['score'] for p in all_positions) / len(all_positions)
        
        # 平均性价比
        avg_value = sum(p['value']['score'] for p in all_positions) / len(all_positions)
        
        # 平均推荐分数
        avg_recommend = sum(p['recommend_score'] for p in all_positions) / len(all_positions)
        
        strategy_config = PositionRecommendService.STRATEGIES.get(
            strategy, PositionRecommendService.STRATEGIES['balanced']
        )
        
        return {
            'avg_competition': round(avg_competition, 1),
            'avg_value': round(avg_value, 1),
            'avg_recommend': round(avg_recommend, 1),
            'sprint_count': len(classified['sprint']),
            'stable_count': len(classified['stable']),
            'safe_count': len(classified['safe']),
            'strategy': strategy_config['name'],
            'message': f"采用{strategy_config['name']}，为您推荐{len(classified['sprint'])}个冲刺岗位、{len(classified['stable'])}个稳妥岗位、{len(classified['safe'])}个保底岗位"
        }
