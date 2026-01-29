# -*- coding: utf-8 -*-
"""学习计划生成器"""
from datetime import datetime, timedelta
from app import db
from app.models import Student, Submission, Mistake, Question
from app.utils.stats import StudentStatsService
from sqlalchemy import func


class StudyPlanGenerator:
    """学习计划生成器"""
    
    def __init__(self, student_id):
        self.student_id = student_id
        self.student = Student.query.get(student_id)
        self.stats_service = StudentStatsService(student_id)
    
    def analyze_weaknesses(self):
        """分析薄弱点"""
        # 获取板块统计
        subcategory_stats = self.stats_service.get_subcategory_stats('all')
        
        # 识别薄弱板块（正确率<70%且做题数>=5）
        weak_areas = []
        for stat in subcategory_stats:
            if stat['total_attempted'] >= 5 and stat['accuracy_rate'] < 70:
                weak_areas.append({
                    'name': stat['dimension_value'],
                    'accuracy_rate': stat['accuracy_rate'],
                    'total_attempted': stat['total_attempted'],
                    'total_mistakes': stat['total_mistakes'],
                    'priority': self._calculate_priority(stat)
                })
        
        # 按优先级排序
        weak_areas.sort(key=lambda x: -x['priority'])
        
        return weak_areas
    
    def _calculate_priority(self, stat):
        """计算优先级（综合考虑正确率和做题量）"""
        # 正确率越低优先级越高
        accuracy_score = (100 - stat['accuracy_rate']) / 100
        
        # 错题越多优先级越高
        mistake_score = min(stat['total_mistakes'] / 10, 1)
        
        return accuracy_score * 0.7 + mistake_score * 0.3
    
    def generate_daily_plan(self, target_questions=20, days=7):
        """
        生成每日学习计划
        
        Args:
            target_questions: 每日目标题数
            days: 计划天数
        """
        weak_areas = self.analyze_weaknesses()
        overview = self.stats_service.get_overview('all')
        
        if not weak_areas:
            # 没有明显薄弱点，均衡练习
            return self._generate_balanced_plan(target_questions, days)
        
        plan = {
            'student_name': self.student.name,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'overview': {
                'total_attempted': overview['total_attempted'],
                'accuracy_rate': overview['accuracy_rate'],
                'weak_areas_count': len(weak_areas)
            },
            'weak_areas': weak_areas[:5],  # 最多显示5个薄弱点
            'daily_plans': [],
            'recommendations': []
        }
        
        # 分配每日任务
        for day in range(1, days + 1):
            date = (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d')
            weekday = (datetime.now() + timedelta(days=day)).strftime('%A')
            
            daily_tasks = []
            remaining = target_questions
            
            # 优先分配给薄弱板块
            for i, area in enumerate(weak_areas[:3]):
                if remaining <= 0:
                    break
                
                # 根据优先级分配题数
                if i == 0:
                    count = min(remaining, int(target_questions * 0.4))
                elif i == 1:
                    count = min(remaining, int(target_questions * 0.3))
                else:
                    count = min(remaining, int(target_questions * 0.2))
                
                daily_tasks.append({
                    'category': area['name'],
                    'count': count,
                    'type': 'weak',
                    'current_accuracy': area['accuracy_rate']
                })
                remaining -= count
            
            # 剩余题数用于复习已做错的题
            if remaining > 0:
                daily_tasks.append({
                    'category': '错题复习',
                    'count': remaining,
                    'type': 'review'
                })
            
            plan['daily_plans'].append({
                'day': day,
                'date': date,
                'weekday': weekday,
                'tasks': daily_tasks,
                'total_questions': target_questions
            })
        
        # 生成建议
        plan['recommendations'] = self._generate_recommendations(weak_areas, overview)
        
        return plan
    
    def _generate_balanced_plan(self, target_questions, days):
        """生成均衡练习计划"""
        # 获取所有分类
        categories = db.session.query(
            Question.subcategory
        ).distinct().filter(Question.subcategory.isnot(None)).all()
        
        category_list = [c[0] for c in categories]
        
        plan = {
            'student_name': self.student.name,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'overview': self.stats_service.get_overview('all'),
            'weak_areas': [],
            'daily_plans': [],
            'recommendations': ['保持当前学习状态，各板块均衡练习']
        }
        
        for day in range(1, days + 1):
            date = (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d')
            
            # 轮换分类
            today_categories = category_list[(day-1) % len(category_list):(day-1) % len(category_list) + 3]
            if len(today_categories) < 3:
                today_categories += category_list[:3-len(today_categories)]
            
            daily_tasks = []
            per_category = target_questions // len(today_categories)
            
            for cat in today_categories:
                daily_tasks.append({
                    'category': cat,
                    'count': per_category,
                    'type': 'balanced'
                })
            
            plan['daily_plans'].append({
                'day': day,
                'date': date,
                'tasks': daily_tasks,
                'total_questions': target_questions
            })
        
        return plan
    
    def _generate_recommendations(self, weak_areas, overview):
        """生成学习建议"""
        recommendations = []
        
        if overview['accuracy_rate'] < 60:
            recommendations.append('整体正确率偏低，建议放慢做题速度，注重理解')
        elif overview['accuracy_rate'] < 75:
            recommendations.append('正确率有提升空间，建议每天复习错题')
        else:
            recommendations.append('正确率良好，继续保持！')
        
        if weak_areas:
            top_weak = weak_areas[0]
            recommendations.append(f"重点攻克"{top_weak['name']}"，当前正确率仅{top_weak['accuracy_rate']}%")
        
        if overview['total_attempted'] < 100:
            recommendations.append('刷题量还不够，建议每天保持20题以上的练习量')
        
        recommendations.append('坚持使用艾宾浩斯复习，巩固已学知识')
        
        return recommendations
    
    def generate_plan_pdf(self, days=7):
        """生成学习计划PDF"""
        from app.utils.report_generator import generate_student_report
        # TODO: 实现单独的学习计划PDF
        pass
