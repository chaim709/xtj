"""
督学服务 - 督学日志管理
"""
from datetime import datetime, date, timedelta
from app import db
from app.models.supervision import SupervisionLog
from app.models.student import Student


class SupervisionService:
    """督学服务类"""
    
    @staticmethod
    def create_log(data):
        """
        创建督学日志
        
        Args:
            data: 日志数据字典
        
        Returns:
            创建的日志对象
        """
        log = SupervisionLog(
            student_id=data.get('student_id'),
            supervisor_id=data.get('supervisor_id'),
            contact_type=data.get('contact_type'),
            contact_duration=data.get('contact_duration'),
            content=data.get('content'),
            student_mood=data.get('student_mood'),
            study_status=data.get('study_status'),
            self_discipline=data.get('self_discipline'),
            actions=data.get('actions'),
            next_follow_up_date=data.get('next_follow_up_date'),
            tags=data.get('tags'),
            log_date=data.get('log_date') or date.today(),
        )
        
        db.session.add(log)
        
        # 更新学员的最后联系日期
        student = Student.query.get(data.get('student_id'))
        if student:
            student.last_contact_date = date.today()
        
        db.session.commit()
        return log
    
    @staticmethod
    def get_log(log_id):
        """获取日志详情"""
        return SupervisionLog.query.get(log_id)
    
    @staticmethod
    def get_logs_by_student(student_id, limit=None):
        """
        获取学员的督学记录
        
        Args:
            student_id: 学员ID
            limit: 限制数量
        
        Returns:
            日志列表
        """
        query = SupervisionLog.query.filter_by(student_id=student_id)\
            .order_by(SupervisionLog.log_date.desc(), SupervisionLog.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_logs_by_supervisor(supervisor_id, start_date=None, end_date=None, page=1, per_page=20):
        """
        获取督学人员的记录
        
        Args:
            supervisor_id: 督学人员ID
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            per_page: 每页数量
        
        Returns:
            分页结果
        """
        query = SupervisionLog.query.filter_by(supervisor_id=supervisor_id)
        
        if start_date:
            query = query.filter(SupervisionLog.log_date >= start_date)
        if end_date:
            query = query.filter(SupervisionLog.log_date <= end_date)
        
        query = query.order_by(SupervisionLog.log_date.desc(), SupervisionLog.created_at.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_recent_logs(supervisor_id=None, days=7):
        """
        获取最近N天的督学记录
        
        Args:
            supervisor_id: 督学人员ID（可选）
            days: 天数
        
        Returns:
            日志列表
        """
        start_date = date.today() - timedelta(days=days)
        
        query = SupervisionLog.query.filter(SupervisionLog.log_date >= start_date)
        
        if supervisor_id:
            query = query.filter_by(supervisor_id=supervisor_id)
        
        return query.order_by(SupervisionLog.log_date.desc()).all()
    
    @staticmethod
    def get_today_logs(supervisor_id=None):
        """获取今日督学记录"""
        query = SupervisionLog.query.filter(SupervisionLog.log_date == date.today())
        
        if supervisor_id:
            query = query.filter_by(supervisor_id=supervisor_id)
        
        return query.all()
    
    @staticmethod
    def get_statistics(supervisor_id=None, start_date=None, end_date=None):
        """
        获取督学统计
        
        Args:
            supervisor_id: 督学人员ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计数据
        """
        query = SupervisionLog.query
        
        if supervisor_id:
            query = query.filter_by(supervisor_id=supervisor_id)
        if start_date:
            query = query.filter(SupervisionLog.log_date >= start_date)
        if end_date:
            query = query.filter(SupervisionLog.log_date <= end_date)
        
        logs = query.all()
        
        # 统计
        total = len(logs)
        mood_stats = {}
        status_stats = {}
        
        for log in logs:
            if log.student_mood:
                mood_stats[log.student_mood] = mood_stats.get(log.student_mood, 0) + 1
            if log.study_status:
                status_stats[log.study_status] = status_stats.get(log.study_status, 0) + 1
        
        return {
            'total': total,
            'mood_stats': mood_stats,
            'status_stats': status_stats,
        }
