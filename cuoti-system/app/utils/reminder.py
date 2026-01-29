# -*- coding: utf-8 -*-
"""错题复习提醒服务"""
from datetime import datetime, timedelta
from app import db
from app.models import Student, Mistake, Question, MistakeReview


class ReminderService:
    """复习提醒服务"""
    
    def __init__(self, student_id):
        self.student_id = student_id
        self.student = Student.query.get(student_id)
    
    def sync_mistakes_to_reviews(self):
        """同步错题到复习记录"""
        # 获取所有错题
        mistakes = Mistake.query.filter_by(student_id=self.student_id).all()
        
        count = 0
        for mistake in mistakes:
            # 获取或创建复习记录
            review = MistakeReview.get_or_create(self.student_id, mistake.question_id)
            if review.id is None:
                count += 1
        
        db.session.commit()
        return count
    
    def get_due_reviews(self, limit=20):
        """获取到期需要复习的题目"""
        now = datetime.now()
        
        reviews = MistakeReview.query.filter(
            MistakeReview.student_id == self.student_id,
            MistakeReview.mastered == False,
            MistakeReview.next_review_at <= now
        ).order_by(MistakeReview.next_review_at).limit(limit).all()
        
        return reviews
    
    def get_due_count(self):
        """获取待复习数量"""
        now = datetime.now()
        
        return MistakeReview.query.filter(
            MistakeReview.student_id == self.student_id,
            MistakeReview.mastered == False,
            MistakeReview.next_review_at <= now
        ).count()
    
    def get_upcoming_reviews(self, days=7):
        """获取未来几天的复习计划"""
        now = datetime.now()
        end = now + timedelta(days=days)
        
        reviews = MistakeReview.query.filter(
            MistakeReview.student_id == self.student_id,
            MistakeReview.mastered == False,
            MistakeReview.next_review_at > now,
            MistakeReview.next_review_at <= end
        ).order_by(MistakeReview.next_review_at).all()
        
        # 按日期分组
        schedule = {}
        for review in reviews:
            date_key = review.next_review_at.strftime('%Y-%m-%d')
            if date_key not in schedule:
                schedule[date_key] = []
            schedule[date_key].append(review)
        
        return schedule
    
    def get_mastered_count(self):
        """获取已掌握数量"""
        return MistakeReview.query.filter(
            MistakeReview.student_id == self.student_id,
            MistakeReview.mastered == True
        ).count()
    
    def get_review_stats(self):
        """获取复习统计"""
        total = MistakeReview.query.filter_by(student_id=self.student_id).count()
        mastered = self.get_mastered_count()
        due = self.get_due_count()
        
        return {
            'total': total,
            'mastered': mastered,
            'due': due,
            'remaining': total - mastered,
            'mastery_rate': round(mastered / total * 100, 1) if total > 0 else 0
        }
    
    def record_review_result(self, question_id, is_correct):
        """记录复习结果"""
        review = MistakeReview.query.filter_by(
            student_id=self.student_id,
            question_id=question_id
        ).first()
        
        if review:
            review.record_review(is_correct)
            db.session.commit()
            return True
        return False
