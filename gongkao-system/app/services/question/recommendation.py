# -*- coding: utf-8 -*-
"""智能推荐系统"""
from app import db
from app.models import Student, Mistake, Question, WorkbookItem
from sqlalchemy import func
import random


class RecommendationService:
    """智能推荐服务"""
    
    def __init__(self, student_id):
        self.student_id = student_id
        self.student = Student.query.get(student_id)
    
    def get_weak_categories(self, limit=5):
        """获取薄弱分类"""
        # 统计各分类的错题数
        weak_cats = db.session.query(
            Question.subcategory,
            Question.category,
            func.count(Mistake.id).label('mistake_count')
        ).join(Mistake).filter(
            Mistake.student_id == self.student_id,
            Question.subcategory.isnot(None)
        ).group_by(Question.subcategory, Question.category).order_by(
            func.count(Mistake.id).desc()
        ).limit(limit).all()
        
        return [{'subcategory': r[0], 'category': r[1], 'count': r[2]} for r in weak_cats]
    
    def get_weak_knowledge_points(self, limit=10):
        """获取薄弱知识点"""
        weak_kps = db.session.query(
            Question.knowledge_point,
            Question.subcategory,
            func.count(Mistake.id).label('mistake_count')
        ).join(Mistake).filter(
            Mistake.student_id == self.student_id,
            Question.knowledge_point.isnot(None)
        ).group_by(Question.knowledge_point, Question.subcategory).order_by(
            func.count(Mistake.id).desc()
        ).limit(limit).all()
        
        return [{'knowledge_point': r[0], 'subcategory': r[1], 'count': r[2]} for r in weak_kps]
    
    def recommend_similar_questions(self, count=10, mode='weak'):
        """
        推荐相似题目
        
        Args:
            count: 推荐数量
            mode: 推荐模式
                - 'weak': 基于薄弱板块推荐
                - 'similar': 基于错题相似度推荐
                - 'random': 随机推荐（避开已做对的题）
        """
        # 获取学员已做错的题目ID
        mistake_question_ids = [m.question_id for m in 
            Mistake.query.filter_by(student_id=self.student_id).all()]
        
        recommendations = []
        
        if mode == 'weak':
            # 基于薄弱板块推荐
            weak_cats = self.get_weak_categories(3)
            
            for cat_info in weak_cats:
                subcategory = cat_info['subcategory']
                
                # 找该板块下未做错过的题目
                questions = Question.query.filter(
                    Question.subcategory == subcategory,
                    ~Question.id.in_(mistake_question_ids) if mistake_question_ids else True
                ).limit(count // len(weak_cats) + 1).all()
                
                for q in questions:
                    recommendations.append({
                        'question': q,
                        'reason': f'基于薄弱板块：{subcategory}',
                        'priority': cat_info['count']
                    })
        
        elif mode == 'similar':
            # 基于错题的知识点推荐相似题
            weak_kps = self.get_weak_knowledge_points(5)
            
            for kp_info in weak_kps:
                kp = kp_info['knowledge_point']
                
                questions = Question.query.filter(
                    Question.knowledge_point == kp,
                    ~Question.id.in_(mistake_question_ids) if mistake_question_ids else True
                ).limit(count // len(weak_kps) + 1).all()
                
                for q in questions:
                    recommendations.append({
                        'question': q,
                        'reason': f'基于知识点：{kp}',
                        'priority': kp_info['count']
                    })
        
        else:  # random
            # 随机推荐
            questions = Question.query.filter(
                ~Question.id.in_(mistake_question_ids) if mistake_question_ids else True
            ).order_by(func.random()).limit(count).all()
            
            for q in questions:
                recommendations.append({
                    'question': q,
                    'reason': '随机推荐',
                    'priority': 0
                })
        
        # 按优先级排序并去重
        seen_ids = set()
        unique_recs = []
        for rec in sorted(recommendations, key=lambda x: -x['priority']):
            if rec['question'].id not in seen_ids:
                seen_ids.add(rec['question'].id)
                unique_recs.append(rec)
                if len(unique_recs) >= count:
                    break
        
        return unique_recs
    
    def generate_practice_set(self, count=20, include_mistakes=True, include_new=True):
        """
        生成练习题集
        
        Args:
            count: 题目数量
            include_mistakes: 是否包含错题重做
            include_new: 是否包含新题
        """
        practice_questions = []
        
        if include_mistakes:
            # 获取错题（按错误次数排序）
            mistake_questions = db.session.query(
                Question,
                func.count(Mistake.id).label('mistake_count')
            ).join(Mistake).filter(
                Mistake.student_id == self.student_id
            ).group_by(Question.id).order_by(
                func.count(Mistake.id).desc()
            ).limit(count // 2).all()
            
            for q, mc in mistake_questions:
                practice_questions.append({
                    'question': q,
                    'type': 'mistake',
                    'mistake_count': mc
                })
        
        if include_new:
            # 获取推荐新题
            remaining = count - len(practice_questions)
            if remaining > 0:
                recommendations = self.recommend_similar_questions(remaining, mode='weak')
                for rec in recommendations:
                    practice_questions.append({
                        'question': rec['question'],
                        'type': 'recommended',
                        'reason': rec['reason']
                    })
        
        # 打乱顺序
        random.shuffle(practice_questions)
        
        return practice_questions
    
    def get_recommendation_summary(self):
        """获取推荐摘要"""
        weak_cats = self.get_weak_categories(3)
        weak_kps = self.get_weak_knowledge_points(5)
        
        # 统计错题总数
        total_mistakes = Mistake.query.filter_by(student_id=self.student_id).count()
        
        return {
            'total_mistakes': total_mistakes,
            'weak_categories': weak_cats,
            'weak_knowledge_points': weak_kps,
            'suggested_focus': weak_cats[0]['subcategory'] if weak_cats else None
        }
