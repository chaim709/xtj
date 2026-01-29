"""
跟进服务 - 计算待跟进学员
"""
from datetime import datetime, date, timedelta
from sqlalchemy import or_
from app import db
from app.models.student import Student
from app.models.supervision import SupervisionLog
from app.models.homework import HomeworkTask, HomeworkSubmission


class FollowUpService:
    """待跟进计算服务"""
    
    # 默认跟进周期（天）
    DEFAULT_FOLLOW_UP_DAYS = 3
    
    @staticmethod
    def get_need_follow_up_students(supervisor_id=None, days=None):
        """
        获取需要跟进的学员
        
        规则：
        1. 超过N天未联系的学员
        2. 督学记录中设置了下次跟进日期且已到期的学员
        3. 心态评估为焦虑/低落的学员
        4. 标记为需重点关注的学员
        
        Args:
            supervisor_id: 督学人员ID（可选）
            days: 未联系天数阈值
        
        Returns:
            学员列表
        """
        if days is None:
            days = FollowUpService.DEFAULT_FOLLOW_UP_DAYS
        
        today = date.today()
        threshold_date = today - timedelta(days=days)
        
        # 基础查询
        query = Student.query.filter(Student.status == 'active')
        
        if supervisor_id:
            query = query.filter(Student.supervisor_id == supervisor_id)
        
        # 条件1：超过N天未联系 或 从未联系
        condition1 = or_(
            Student.last_contact_date.is_(None),
            Student.last_contact_date <= threshold_date
        )
        
        # 条件2：标记为需重点关注
        condition2 = Student.need_attention == True
        
        # 合并条件
        students = query.filter(or_(condition1, condition2)).all()
        
        # 额外检查：督学记录中设置的下次跟进日期
        follow_up_logs = SupervisionLog.query.filter(
            SupervisionLog.next_follow_up_date <= today
        ).all()
        follow_up_student_ids = set(log.student_id for log in follow_up_logs)
        
        # 额外检查：最近一次心态评估为焦虑/低落的学员
        recent_logs = db.session.query(
            SupervisionLog.student_id
        ).filter(
            SupervisionLog.student_mood.in_(['焦虑', '低落'])
        ).distinct().all()
        mood_student_ids = set(log[0] for log in recent_logs)
        
        # 合并结果
        all_student_ids = set(s.id for s in students)
        all_student_ids.update(follow_up_student_ids)
        all_student_ids.update(mood_student_ids)
        
        # 如果有督学人员限制，过滤一下
        if supervisor_id:
            final_students = Student.query.filter(
                Student.id.in_(all_student_ids),
                Student.supervisor_id == supervisor_id,
                Student.status == 'active'
            ).all()
        else:
            final_students = Student.query.filter(
                Student.id.in_(all_student_ids),
                Student.status == 'active'
            ).all()
        
        return final_students
    
    @staticmethod
    def get_dashboard_statistics(supervisor_id=None):
        """
        获取工作台统计数据
        
        Args:
            supervisor_id: 督学人员ID（可选）
        
        Returns:
            统计数据字典
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        # 学员总数
        student_query = Student.query.filter(Student.status == 'active')
        if supervisor_id:
            student_query = student_query.filter(Student.supervisor_id == supervisor_id)
        total_students = student_query.count()
        
        # 待跟进学员
        follow_up_students = FollowUpService.get_need_follow_up_students(supervisor_id)
        need_follow_up = len(follow_up_students)
        
        # 今日作业
        today_tasks = HomeworkTask.query.filter(
            HomeworkTask.status == 'published',
            db.func.date(HomeworkTask.deadline) == today
        ).count()
        
        # 本周督学记录
        log_query = SupervisionLog.query.filter(
            SupervisionLog.log_date >= week_start
        )
        if supervisor_id:
            log_query = log_query.filter(SupervisionLog.supervisor_id == supervisor_id)
        week_logs = log_query.count()
        
        # 进行中作业数量
        active_homework = HomeworkTask.query.filter(
            HomeworkTask.status == 'published'
        ).count()
        
        # 最近添加的学员
        recent_students_query = Student.query.filter(Student.status == 'active')
        if supervisor_id:
            recent_students_query = recent_students_query.filter(Student.supervisor_id == supervisor_id)
        recent_students = recent_students_query.order_by(
            Student.created_at.desc()
        ).limit(5).all()
        
        return {
            'total_students': total_students,
            'need_follow_up': need_follow_up,
            'today_tasks': today_tasks,
            'week_logs': week_logs,
            'active_homework': active_homework,
            'follow_up_students': follow_up_students[:10],  # 只返回前10个
            'recent_students': recent_students,
        }
    
    @staticmethod
    def get_recent_logs(supervisor_id=None, limit=5):
        """获取最近督学记录"""
        query = SupervisionLog.query
        if supervisor_id:
            query = query.filter(SupervisionLog.supervisor_id == supervisor_id)
        
        return query.order_by(
            SupervisionLog.log_date.desc(),
            SupervisionLog.created_at.desc()
        ).limit(limit).all()
