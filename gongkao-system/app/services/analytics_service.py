"""
数据分析服务 - 第三阶段新增
提供统计数据计算和聚合功能
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy import func, and_, desc
from app.models.student import Student
from app.models.supervision import SupervisionLog
from app.models.tag import WeaknessTag
from app.models.course import ClassBatch, Schedule, StudentBatch, Attendance
from app.models.user import User
from app import db


class AnalyticsService:
    """数据分析服务类"""
    
    @classmethod
    def get_overview_stats(cls, days: int = 30) -> Dict[str, Any]:
        """
        获取概览统计数据
        
        Args:
            days: 统计天数
        
        Returns:
            统计数据字典
        """
        today = date.today()
        start_date = today - timedelta(days=days)
        
        # 学员统计
        total_students = Student.query.count()
        active_students = Student.query.filter_by(status='在学').count()
        new_students = Student.query.filter(
            Student.created_at >= datetime.combine(start_date, datetime.min.time())
        ).count()
        
        # 督学统计
        total_logs = SupervisionLog.query.filter(
            SupervisionLog.created_at >= datetime.combine(start_date, datetime.min.time())
        ).count()
        
        # 需要关注的学员
        attention_students = Student.query.filter_by(
            need_attention=True,
            status='在学'
        ).count()
        
        # 班次统计
        ongoing_batches = ClassBatch.query.filter_by(status='ongoing').count()
        recruiting_batches = ClassBatch.query.filter_by(status='recruiting').count()
        
        # 今日课程数
        today_schedules = Schedule.query.filter_by(schedule_date=today).count()
        
        return {
            'students': {
                'total': total_students,
                'active': active_students,
                'new': new_students,
                'attention': attention_students
            },
            'supervision': {
                'total_logs': total_logs,
                'avg_per_day': round(total_logs / max(days, 1), 1)
            },
            'courses': {
                'ongoing_batches': ongoing_batches,
                'recruiting_batches': recruiting_batches,
                'today_schedules': today_schedules
            }
        }
    
    @classmethod
    def get_student_trend(cls, days: int = 30) -> Dict[str, List]:
        """
        获取学员增长趋势
        
        Args:
            days: 统计天数
        
        Returns:
            日期和数量数组
        """
        today = date.today()
        start_date = today - timedelta(days=days-1)
        
        # 按日期分组统计新增学员
        results = db.session.query(
            func.date(Student.created_at).label('date'),
            func.count(Student.id).label('count')
        ).filter(
            Student.created_at >= datetime.combine(start_date, datetime.min.time())
        ).group_by(
            func.date(Student.created_at)
        ).order_by('date').all()
        
        # 转换为字典便于填充
        date_counts = {str(r.date): r.count for r in results}
        
        # 生成完整的日期序列
        dates = []
        counts = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            dates.append(d.strftime('%m-%d'))
            counts.append(date_counts.get(str(d), 0))
        
        return {
            'dates': dates,
            'counts': counts
        }
    
    @classmethod
    def get_student_status_distribution(cls) -> List[Dict[str, Any]]:
        """
        获取学员状态分布
        
        Returns:
            饼图数据
        """
        results = db.session.query(
            Student.status,
            func.count(Student.id).label('count')
        ).group_by(Student.status).all()
        
        # 状态颜色映射
        colors = {
            '在学': '#4CAF50',
            '结业': '#2196F3',
            '暂停': '#FF9800',
            '退费': '#f44336'
        }
        
        return [{
            'name': r.status or '未知',
            'value': r.count,
            'color': colors.get(r.status, '#9E9E9E')
        } for r in results]
    
    @classmethod
    def get_supervision_ranking(cls, days: int = 30, limit: int = 10) -> Dict[str, List]:
        """
        获取督学工作量排行
        
        Args:
            days: 统计天数
            limit: 返回数量
        
        Returns:
            柱状图数据
        """
        start_date = date.today() - timedelta(days=days)
        
        results = db.session.query(
            User.username,
            func.count(SupervisionLog.id).label('count')
        ).join(
            User, SupervisionLog.supervisor_id == User.id
        ).filter(
            SupervisionLog.created_at >= datetime.combine(start_date, datetime.min.time())
        ).group_by(
            User.id, User.username
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return {
            'names': [r.username for r in results],
            'counts': [r.count for r in results]
        }
    
    @classmethod
    def get_weakness_distribution(cls, limit: int = 10) -> Dict[str, List]:
        """
        获取薄弱知识点分布（Top N）
        
        Args:
            limit: 返回数量
        
        Returns:
            柱状图数据
        """
        results = db.session.query(
            WeaknessTag.module,
            func.count(WeaknessTag.id).label('count')
        ).group_by(
            WeaknessTag.module
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return {
            'modules': [r.module for r in results],
            'counts': [r.count for r in results]
        }
    
    @classmethod
    def get_batch_progress(cls) -> List[Dict[str, Any]]:
        """
        获取班次课程进度
        
        Returns:
            进度数据
        """
        # 获取进行中的班次
        batches = ClassBatch.query.filter_by(status='ongoing').all()
        
        result = []
        today = date.today()
        
        for batch in batches:
            # 计算总天数和已上天数
            total_days = batch.actual_days or 0
            if total_days == 0 and batch.start_date and batch.end_date:
                total_days = (batch.end_date - batch.start_date).days + 1
            
            # 已上课天数
            completed_days = Schedule.query.filter(
                Schedule.batch_id == batch.id,
                Schedule.schedule_date <= today
            ).count()
            
            progress = round(completed_days / total_days * 100, 1) if total_days > 0 else 0
            
            result.append({
                'id': batch.id,
                'name': batch.name,
                'total_days': total_days,
                'completed_days': completed_days,
                'progress': progress,
                'enrolled_count': batch.enrolled_count or 0
            })
        
        return result
    
    @classmethod
    def get_attendance_summary(cls, batch_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取考勤统计
        
        Args:
            batch_id: 班次ID（可选）
        
        Returns:
            考勤统计数据
        """
        query = Attendance.query
        
        if batch_id:
            # 获取该班次的所有课程安排ID
            schedule_ids = [s.id for s in Schedule.query.filter_by(batch_id=batch_id).all()]
            if schedule_ids:
                query = query.filter(Attendance.schedule_id.in_(schedule_ids))
            else:
                return {'present': 0, 'absent': 0, 'late': 0, 'leave': 0, 'rate': 0}
        
        # 统计各状态数量
        results = db.session.query(
            Attendance.status,
            func.count(Attendance.id).label('count')
        ).group_by(Attendance.status).all()
        
        status_counts = {r.status: r.count for r in results}
        
        total = sum(status_counts.values())
        present = status_counts.get('present', 0)
        late = status_counts.get('late', 0)
        
        # 出勤率 = (出勤+迟到) / 总数
        rate = round((present + late) / total * 100, 1) if total > 0 else 0
        
        return {
            'present': present,
            'absent': status_counts.get('absent', 0),
            'late': late,
            'leave': status_counts.get('leave', 0),
            'total': total,
            'rate': rate
        }
    
    @classmethod
    def get_follow_up_stats(cls, days: int = 30) -> Dict[str, Any]:
        """
        获取跟进统计
        
        Args:
            days: 统计天数
        
        Returns:
            跟进统计数据
        """
        today = date.today()
        start_date = today - timedelta(days=days)
        
        # 总跟进次数
        total_follow_ups = SupervisionLog.query.filter(
            SupervisionLog.created_at >= datetime.combine(start_date, datetime.min.time())
        ).count()
        
        # 按联系方式统计
        contact_results = db.session.query(
            SupervisionLog.contact_method,
            func.count(SupervisionLog.id).label('count')
        ).filter(
            SupervisionLog.created_at >= datetime.combine(start_date, datetime.min.time())
        ).group_by(
            SupervisionLog.contact_method
        ).all()
        
        contact_stats = {r.contact_method: r.count for r in contact_results if r.contact_method}
        
        return {
            'total': total_follow_ups,
            'by_method': contact_stats,
            'avg_per_day': round(total_follow_ups / max(days, 1), 1)
        }
    
    @classmethod
    def get_exam_type_distribution(cls) -> List[Dict[str, Any]]:
        """
        获取报考类型分布
        
        Returns:
            饼图数据
        """
        results = db.session.query(
            Student.exam_type,
            func.count(Student.id).label('count')
        ).filter(
            Student.status == '在学'
        ).group_by(
            Student.exam_type
        ).all()
        
        return [{
            'name': r.exam_type or '未指定',
            'value': r.count
        } for r in results]
    
    @classmethod
    def get_class_distribution(cls) -> List[Dict[str, Any]]:
        """
        获取班次分布
        
        Returns:
            饼图数据
        """
        results = db.session.query(
            Student.class_name,
            func.count(Student.id).label('count')
        ).filter(
            Student.status == '在学'
        ).group_by(
            Student.class_name
        ).all()
        
        return [{
            'name': r.class_name or '未指定',
            'value': r.count
        } for r in results]
