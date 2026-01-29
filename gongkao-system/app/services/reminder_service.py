"""
提醒服务 - 第三阶段新增
提供各类提醒数据查询功能
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import func, and_, or_
from flask import current_app
from app.models.student import Student
from app.models.supervision import SupervisionLog
from app.models.course import Schedule, ClassBatch, StudentBatch
from app import db


class ReminderService:
    """提醒服务类"""
    
    @classmethod
    def get_pending_follow_ups(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取待跟进学员列表
        
        规则：超过配置天数（默认7天）未记录督学日志的在学学员
        
        Args:
            limit: 返回数量限制
        
        Returns:
            待跟进学员列表
        """
        # 获取配置的提醒天数
        reminder_days = current_app.config.get('FOLLOW_UP_REMINDER_DAYS', 7)
        threshold_date = datetime.now() - timedelta(days=reminder_days)
        
        # 子查询：获取每个学员最后一次督学日志时间
        last_log_subquery = db.session.query(
            SupervisionLog.student_id,
            func.max(SupervisionLog.created_at).label('last_log_time')
        ).group_by(SupervisionLog.student_id).subquery()
        
        # 主查询：在学学员 + 最后日志时间早于阈值 或 从未有日志
        students = db.session.query(
            Student,
            last_log_subquery.c.last_log_time
        ).outerjoin(
            last_log_subquery,
            Student.id == last_log_subquery.c.student_id
        ).filter(
            Student.status == '在学',
            or_(
                last_log_subquery.c.last_log_time < threshold_date,
                last_log_subquery.c.last_log_time.is_(None)
            )
        ).order_by(
            # 无日志的排最前，然后按最后日志时间升序
            last_log_subquery.c.last_log_time.asc().nullsfirst()
        ).limit(limit).all()
        
        result = []
        for student, last_log_time in students:
            if last_log_time:
                days_since = (datetime.now() - last_log_time).days
                last_log_str = last_log_time.strftime('%Y-%m-%d')
            else:
                days_since = None  # 从未跟进
                last_log_str = None
            
            result.append({
                'id': student.id,
                'name': student.name,
                'phone': student.phone,
                'class_name': student.class_name,
                'exam_type': student.exam_type,
                'last_follow_up': last_log_str,
                'days_since_follow_up': days_since,
                'need_attention': student.need_attention
            })
        
        return result
    
    @classmethod
    def get_today_schedules_reminder(cls) -> List[Dict[str, Any]]:
        """
        获取今日课程提醒
        
        Returns:
            今日课程列表
        """
        today = date.today()
        
        schedules = Schedule.query.filter_by(
            schedule_date=today
        ).order_by(Schedule.batch_id).all()
        
        result = []
        for schedule in schedules:
            batch = schedule.batch
            subject = schedule.subject
            
            if not batch:
                continue
            
            # 获取老师信息
            from app.models.teacher import Teacher
            morning_teacher = Teacher.query.get(schedule.morning_teacher_id) if schedule.morning_teacher_id else None
            afternoon_teacher = Teacher.query.get(schedule.afternoon_teacher_id) if schedule.afternoon_teacher_id else None
            
            result.append({
                'id': schedule.id,
                'batch_id': batch.id,
                'batch_name': batch.name,
                'day_number': schedule.day_number,
                'subject_name': subject.name if subject else '未指定',
                'morning_teacher': morning_teacher.name if morning_teacher else '待定',
                'afternoon_teacher': afternoon_teacher.name if afternoon_teacher else '待定',
                'evening_type': schedule.evening_type,
                'classroom': batch.classroom,
                'enrolled_count': batch.enrolled_count
            })
        
        return result
    
    @classmethod
    def get_attention_students(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取需要重点关注的学员
        
        Returns:
            需关注学员列表
        """
        students = Student.query.filter(
            Student.status == '在学',
            Student.need_attention == True
        ).order_by(Student.created_at.desc()).limit(limit).all()
        
        result = []
        for student in students:
            # 获取最后一次督学日志
            last_log = SupervisionLog.query.filter_by(
                student_id=student.id
            ).order_by(SupervisionLog.created_at.desc()).first()
            
            result.append({
                'id': student.id,
                'name': student.name,
                'phone': student.phone,
                'class_name': student.class_name,
                'last_mood': last_log.mood if last_log else None,
                'last_status': last_log.study_status if last_log else None,
                'last_log_date': last_log.created_at.strftime('%Y-%m-%d') if last_log else None
            })
        
        return result
    
    @classmethod
    def get_upcoming_batches(cls, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取即将开课的班次
        
        Args:
            days: 未来天数
        
        Returns:
            即将开课班次列表
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        
        batches = ClassBatch.query.filter(
            ClassBatch.status == 'recruiting',
            ClassBatch.start_date >= today,
            ClassBatch.start_date <= end_date
        ).order_by(ClassBatch.start_date).all()
        
        result = []
        for batch in batches:
            days_until = (batch.start_date - today).days if batch.start_date else 0
            
            result.append({
                'id': batch.id,
                'name': batch.name,
                'start_date': batch.start_date.isoformat() if batch.start_date else None,
                'days_until': days_until,
                'enrolled_count': batch.enrolled_count,
                'max_students': batch.max_students,
                'class_type_name': batch.class_type.name if batch.class_type else None
            })
        
        return result
    
    @classmethod
    def get_ending_batches(cls, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取即将结课的班次
        
        Args:
            days: 未来天数
        
        Returns:
            即将结课班次列表
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        
        batches = ClassBatch.query.filter(
            ClassBatch.status == 'ongoing',
            ClassBatch.end_date >= today,
            ClassBatch.end_date <= end_date
        ).order_by(ClassBatch.end_date).all()
        
        result = []
        for batch in batches:
            days_until = (batch.end_date - today).days if batch.end_date else 0
            
            result.append({
                'id': batch.id,
                'name': batch.name,
                'end_date': batch.end_date.isoformat() if batch.end_date else None,
                'days_until': days_until,
                'enrolled_count': batch.enrolled_count
            })
        
        return result
    
    @classmethod
    def get_dashboard_reminders(cls) -> Dict[str, Any]:
        """
        获取工作台提醒汇总
        
        Returns:
            提醒汇总数据
        """
        # 待跟进学员数量
        reminder_days = current_app.config.get('FOLLOW_UP_REMINDER_DAYS', 7)
        threshold_date = datetime.now() - timedelta(days=reminder_days)
        
        # 子查询
        last_log_subquery = db.session.query(
            SupervisionLog.student_id,
            func.max(SupervisionLog.created_at).label('last_log_time')
        ).group_by(SupervisionLog.student_id).subquery()
        
        pending_count = db.session.query(
            func.count(Student.id)
        ).outerjoin(
            last_log_subquery,
            Student.id == last_log_subquery.c.student_id
        ).filter(
            Student.status == '在学',
            or_(
                last_log_subquery.c.last_log_time < threshold_date,
                last_log_subquery.c.last_log_time.is_(None)
            )
        ).scalar() or 0
        
        # 今日课程数
        today = date.today()
        today_schedule_count = Schedule.query.filter_by(schedule_date=today).count()
        
        # 需关注学员数
        attention_count = Student.query.filter(
            Student.status == '在学',
            Student.need_attention == True
        ).count()
        
        # 即将开课班次数（7天内）
        upcoming_count = ClassBatch.query.filter(
            ClassBatch.status == 'recruiting',
            ClassBatch.start_date >= today,
            ClassBatch.start_date <= today + timedelta(days=7)
        ).count()
        
        return {
            'pending_follow_ups': pending_count,
            'today_schedules': today_schedule_count,
            'attention_students': attention_count,
            'upcoming_batches': upcoming_count,
            'reminder_days': reminder_days
        }
