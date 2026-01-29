# -*- coding: utf-8 -*-
"""学员统计服务"""
from app import db
from app.models import Student, Submission, Mistake, Question, StudentStats, Workbook
from datetime import datetime, timedelta
from sqlalchemy import func


class StudentStatsService:
    """学员统计服务"""
    
    def __init__(self, student_id):
        self.student_id = student_id
        self.student = Student.query.get(student_id)
    
    def get_overview(self, period='all'):
        """获取总览数据"""
        # 计算时间范围
        start_date = self._get_start_date(period)
        
        # 查询提交记录
        query = Submission.query.filter_by(student_id=self.student_id)
        if start_date:
            query = query.filter(Submission.created_at >= start_date)
        
        submissions = query.all()
        
        # 汇总统计
        total_attempted = sum(s.total_attempted or 0 for s in submissions)
        total_correct = sum(s.correct_count or 0 for s in submissions)
        total_mistakes = sum(s.mistake_count or 0 for s in submissions)
        
        # 计算正确率
        accuracy_rate = 0
        if total_attempted > 0:
            accuracy_rate = round(total_correct / total_attempted * 100, 1)
        
        # 计算学习天数
        study_dates = set(s.created_at.date() for s in submissions if s.created_at)
        study_days = len(study_dates)
        
        # 错题数（去重）
        mistake_query = Mistake.query.filter_by(student_id=self.student_id)
        if start_date:
            mistake_query = mistake_query.filter(Mistake.created_at >= start_date)
        unique_mistakes = mistake_query.distinct(Mistake.question_id).count()
        
        return {
            'total_attempted': total_attempted,
            'total_correct': total_correct,
            'total_mistakes': total_mistakes,
            'unique_mistakes': unique_mistakes,
            'accuracy_rate': accuracy_rate,
            'study_days': study_days,
            'submission_count': len(submissions),
            'period': period
        }
    
    def get_category_stats(self, period='all'):
        """获取分类统计（一级分类）"""
        return self._get_dimension_stats('category', period)
    
    def get_subcategory_stats(self, period='all'):
        """获取板块统计（二级分类）"""
        return self._get_dimension_stats('subcategory', period)
    
    def get_workbook_stats(self, period='all'):
        """获取题册统计"""
        start_date = self._get_start_date(period)
        
        query = db.session.query(
            Submission.workbook_id,
            func.sum(Submission.total_attempted).label('total_attempted'),
            func.sum(Submission.correct_count).label('total_correct'),
            func.sum(Submission.mistake_count).label('total_mistakes'),
            func.count(Submission.id).label('submission_count')
        ).filter_by(student_id=self.student_id)
        
        if start_date:
            query = query.filter(Submission.created_at >= start_date)
        
        query = query.group_by(Submission.workbook_id)
        
        results = []
        for row in query.all():
            workbook = Workbook.query.get(row.workbook_id)
            total_attempted = row.total_attempted or 0
            total_correct = row.total_correct or 0
            accuracy = round(total_correct / total_attempted * 100, 1) if total_attempted > 0 else 0
            
            results.append({
                'workbook_id': row.workbook_id,
                'workbook_name': workbook.name if workbook else '未知',
                'total_attempted': total_attempted,
                'total_correct': total_correct,
                'total_mistakes': row.total_mistakes or 0,
                'accuracy_rate': accuracy,
                'submission_count': row.submission_count
            })
        
        # 按正确率排序
        results.sort(key=lambda x: x['accuracy_rate'])
        return results
    
    def get_knowledge_point_stats(self, period='all'):
        """获取知识点统计"""
        start_date = self._get_start_date(period)
        
        # 从错题中统计知识点
        query = db.session.query(
            Question.knowledge_point,
            Question.subcategory,
            func.count(Mistake.id).label('mistake_count')
        ).join(Mistake).filter(Mistake.student_id == self.student_id)
        
        if start_date:
            query = query.filter(Mistake.created_at >= start_date)
        
        query = query.group_by(Question.knowledge_point, Question.subcategory)
        
        results = []
        for row in query.all():
            if row.knowledge_point:
                results.append({
                    'knowledge_point': row.knowledge_point,
                    'subcategory': row.subcategory,
                    'mistake_count': row.mistake_count
                })
        
        # 按错题数排序
        results.sort(key=lambda x: x['mistake_count'], reverse=True)
        return results
    
    def get_weakness_analysis(self, period='all'):
        """获取弱项分析"""
        subcategory_stats = self.get_subcategory_stats(period)
        
        # 找出正确率最低的板块
        weak_items = []
        for stat in subcategory_stats:
            if stat['total_attempted'] >= 5:  # 至少做了5题才算
                if stat['accuracy_rate'] < 70:
                    weak_items.append({
                        'name': stat['dimension_value'],
                        'accuracy_rate': stat['accuracy_rate'],
                        'total_attempted': stat['total_attempted'],
                        'level': 'danger' if stat['accuracy_rate'] < 60 else 'warning'
                    })
        
        # 按正确率排序
        weak_items.sort(key=lambda x: x['accuracy_rate'])
        return weak_items[:5]  # 返回最弱的5个
    
    def get_trend_data(self, days=30):
        """获取正确率趋势数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 按日期分组统计
        query = db.session.query(
            func.date(Submission.created_at).label('date'),
            func.sum(Submission.total_attempted).label('total_attempted'),
            func.sum(Submission.correct_count).label('total_correct')
        ).filter(
            Submission.student_id == self.student_id,
            Submission.created_at >= start_date
        ).group_by(func.date(Submission.created_at)).order_by(func.date(Submission.created_at))
        
        results = []
        for row in query.all():
            total = row.total_attempted or 0
            correct = row.total_correct or 0
            accuracy = round(correct / total * 100, 1) if total > 0 else 0
            
            results.append({
                'date': row.date.strftime('%m-%d') if hasattr(row.date, 'strftime') else str(row.date),
                'total_attempted': total,
                'accuracy_rate': accuracy
            })
        
        return results
    
    def get_frequent_mistakes(self, limit=10):
        """获取高频错题"""
        # 统计每道题的错误次数
        query = db.session.query(
            Mistake.question_id,
            func.count(Mistake.id).label('count')
        ).filter_by(student_id=self.student_id).group_by(
            Mistake.question_id
        ).order_by(func.count(Mistake.id).desc()).limit(limit)
        
        results = []
        for row in query.all():
            question = Question.query.get(row.question_id)
            if question:
                results.append({
                    'question_id': row.question_id,
                    'count': row.count,
                    'stem': question.stem[:80] + '...' if len(question.stem) > 80 else question.stem,
                    'category': question.category,
                    'subcategory': question.subcategory,
                    'answer': question.answer
                })
        
        return results
    
    def _get_dimension_stats(self, dimension, period='all'):
        """通用维度统计"""
        start_date = self._get_start_date(period)
        
        # 获取维度字段
        if dimension == 'category':
            dim_field = Submission.category
        elif dimension == 'subcategory':
            dim_field = Submission.subcategory
        else:
            return []
        
        query = db.session.query(
            dim_field.label('dimension_value'),
            func.sum(Submission.total_attempted).label('total_attempted'),
            func.sum(Submission.correct_count).label('total_correct'),
            func.sum(Submission.mistake_count).label('total_mistakes'),
            func.count(Submission.id).label('submission_count')
        ).filter(
            Submission.student_id == self.student_id,
            dim_field.isnot(None)
        )
        
        if start_date:
            query = query.filter(Submission.created_at >= start_date)
        
        query = query.group_by(dim_field)
        
        results = []
        for row in query.all():
            total_attempted = row.total_attempted or 0
            total_correct = row.total_correct or 0
            accuracy = round(total_correct / total_attempted * 100, 1) if total_attempted > 0 else 0
            
            results.append({
                'dimension': dimension,
                'dimension_value': row.dimension_value,
                'total_attempted': total_attempted,
                'total_correct': total_correct,
                'total_mistakes': row.total_mistakes or 0,
                'accuracy_rate': accuracy,
                'submission_count': row.submission_count
            })
        
        # 按正确率排序（从低到高，方便识别弱项）
        results.sort(key=lambda x: x['accuracy_rate'])
        return results
    
    def _get_start_date(self, period):
        """获取时间范围起始日期"""
        if period == '7d':
            return datetime.now() - timedelta(days=7)
        elif period == '30d':
            return datetime.now() - timedelta(days=30)
        elif period == '90d':
            return datetime.now() - timedelta(days=90)
        else:
            return None  # 全部
    
    def get_full_report_data(self, period='all'):
        """获取完整报告数据"""
        return {
            'student': {
                'id': self.student.id,
                'name': self.student.name,
                'phone': self.student.phone
            },
            'period': period,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'overview': self.get_overview(period),
            'category_stats': self.get_category_stats(period),
            'subcategory_stats': self.get_subcategory_stats(period),
            'workbook_stats': self.get_workbook_stats(period),
            'knowledge_point_stats': self.get_knowledge_point_stats(period),
            'weakness_analysis': self.get_weakness_analysis(period),
            'trend_data': self.get_trend_data(30),
            'frequent_mistakes': self.get_frequent_mistakes(10)
        }
