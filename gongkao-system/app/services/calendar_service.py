"""
日历服务 - 第三阶段新增
提供课程日历数据转换和查询功能
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy import func, extract
from app.models.course import Schedule, ClassBatch, Subject
from app.models.teacher import Teacher
from app import db


class CalendarService:
    """日历服务类"""
    
    # 时段颜色配置
    TIME_SLOT_COLORS = {
        'morning': '#f59e0b',      # 上午 - 琥珀色
        'afternoon': '#ea580c',    # 下午 - 橙色
        'evening': '#6366f1',      # 晚上 - 靛蓝色
    }
    
    # 班次状态颜色（现代渐变色系）
    STATUS_COLORS = {
        'recruiting': '#a855f7',   # 招生中 - 紫色
        'ongoing': '#22c55e',      # 进行中 - 绿色
        'ended': '#94a3b8',        # 已结束 - 灰色
    }
    
    @classmethod
    def get_calendar_events(
        cls,
        start_date: date,
        end_date: date,
        batch_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        subject_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取日历事件列表（FullCalendar格式）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            batch_id: 班次ID筛选
            teacher_id: 老师ID筛选
            subject_id: 科目ID筛选
        
        Returns:
            FullCalendar事件列表
        """
        # 构建查询
        query = Schedule.query.filter(
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date
        )
        
        if batch_id:
            query = query.filter_by(batch_id=batch_id)
        
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        if teacher_id:
            # 筛选包含该老师的课程
            query = query.filter(
                db.or_(
                    Schedule.morning_teacher_id == teacher_id,
                    Schedule.afternoon_teacher_id == teacher_id,
                    Schedule.evening_teacher_id == teacher_id
                )
            )
        
        schedules = query.order_by(Schedule.schedule_date).all()
        
        # 转换为FullCalendar事件格式
        events = []
        for schedule in schedules:
            # 获取关联数据
            batch = schedule.batch
            subject = schedule.subject
            
            if not batch:
                continue
            
            batch_name = batch.name
            subject_name = subject.name if subject else '未指定'
            color = cls.STATUS_COLORS.get(batch.status, '#607D8B')
            
            # 创建全天事件（显示科目）
            events.append({
                'id': f'schedule_{schedule.id}',
                'title': f'{batch_name} - {subject_name}',
                'start': schedule.schedule_date.isoformat(),
                'allDay': True,
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'schedule_id': schedule.id,
                    'batch_id': batch.id,
                    'batch_name': batch_name,
                    'subject_name': subject_name,
                    'day_number': schedule.day_number,
                    'morning_teacher': cls._get_teacher_name(schedule.morning_teacher_id),
                    'afternoon_teacher': cls._get_teacher_name(schedule.afternoon_teacher_id),
                    'evening_type': schedule.evening_type,
                    'evening_teacher': cls._get_teacher_name(schedule.evening_teacher_id),
                    'remark': schedule.remark
                }
            })
        
        return events
    
    @classmethod
    def get_day_schedules(cls, target_date: date) -> List[Dict[str, Any]]:
        """
        获取指定日期的所有课程详情
        
        Args:
            target_date: 目标日期
        
        Returns:
            课程详情列表
        """
        schedules = Schedule.query.filter_by(
            schedule_date=target_date
        ).order_by(Schedule.batch_id).all()
        
        result = []
        for schedule in schedules:
            batch = schedule.batch
            subject = schedule.subject
            
            if not batch:
                continue
            
            result.append({
                'id': schedule.id,
                'batch_id': batch.id,
                'batch_name': batch.name,
                'batch_status': batch.status,
                'day_number': schedule.day_number,
                'subject_id': schedule.subject_id,
                'subject_name': subject.name if subject else '未指定',
                'sessions': {
                    'morning': {
                        'time': '09:00-12:00',
                        'teacher_id': schedule.morning_teacher_id,
                        'teacher_name': cls._get_teacher_name(schedule.morning_teacher_id)
                    },
                    'afternoon': {
                        'time': '14:30-17:30',
                        'teacher_id': schedule.afternoon_teacher_id,
                        'teacher_name': cls._get_teacher_name(schedule.afternoon_teacher_id)
                    },
                    'evening': {
                        'time': '18:30-21:00',
                        'type': schedule.evening_type,
                        'teacher_id': schedule.evening_teacher_id,
                        'teacher_name': cls._get_teacher_name(schedule.evening_teacher_id) if schedule.evening_type == 'class' else None
                    }
                },
                'remark': schedule.remark,
                'classroom': batch.classroom
            })
        
        return result
    
    @classmethod
    def get_month_summary(cls, year: int, month: int) -> Dict[str, Any]:
        """
        获取月度课程概览
        
        Args:
            year: 年份
            month: 月份
        
        Returns:
            月度统计数据
        """
        # 计算月份的开始和结束日期
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # 统计数据
        schedules = Schedule.query.filter(
            Schedule.schedule_date >= first_day,
            Schedule.schedule_date <= last_day
        ).all()
        
        # 按日期分组统计
        daily_counts = {}
        batch_ids = set()
        
        for schedule in schedules:
            date_str = schedule.schedule_date.isoformat()
            if date_str not in daily_counts:
                daily_counts[date_str] = 0
            daily_counts[date_str] += 1
            batch_ids.add(schedule.batch_id)
        
        return {
            'year': year,
            'month': month,
            'total_days': len(daily_counts),
            'total_schedules': len(schedules),
            'active_batches': len(batch_ids),
            'daily_counts': daily_counts
        }
    
    @classmethod
    def _get_teacher_name(cls, teacher_id: Optional[int]) -> Optional[str]:
        """
        获取老师姓名
        
        Args:
            teacher_id: 老师ID
        
        Returns:
            老师姓名或None
        """
        if not teacher_id:
            return None
        teacher = Teacher.query.get(teacher_id)
        return teacher.name if teacher else None
    
    @classmethod
    def get_week_schedules(cls, start_date: date) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取一周的课程安排
        
        Args:
            start_date: 周开始日期
        
        Returns:
            按日期分组的课程字典
        """
        end_date = start_date + timedelta(days=6)
        
        schedules = Schedule.query.filter(
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date
        ).order_by(Schedule.schedule_date, Schedule.batch_id).all()
        
        # 按日期分组
        week_data = {}
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            week_data[current_date.isoformat()] = []
        
        for schedule in schedules:
            date_str = schedule.schedule_date.isoformat()
            if date_str in week_data:
                batch = schedule.batch
                subject = schedule.subject
                
                if batch:
                    week_data[date_str].append({
                        'id': schedule.id,
                        'batch_name': batch.name,
                        'subject_name': subject.name if subject else '未指定',
                        'batch_status': batch.status
                    })
        
        return week_data
    
    @classmethod
    def get_yearly_heatmap_data(cls, year: int) -> Dict[str, Any]:
        """
        获取全年排课热力图数据（GitHub风格）
        
        Args:
            year: 年份
        
        Returns:
            热力图数据，包含每天的课程数
        """
        # 计算年份的开始和结束日期
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # 查询该年所有课程安排
        schedules = Schedule.query.filter(
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date
        ).all()
        
        # 按日期统计课程数
        daily_counts = defaultdict(int)
        for schedule in schedules:
            date_str = schedule.schedule_date.isoformat()
            daily_counts[date_str] += 1
        
        # 生成完整的日期序列（用于热力图）
        heatmap_data = []
        current_date = start_date
        
        # 找到该年第一天是星期几（0=周一，6=周日）
        first_weekday = start_date.weekday()
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            count = daily_counts.get(date_str, 0)
            
            heatmap_data.append({
                'date': date_str,
                'count': count,
                'weekday': current_date.weekday(),  # 0=周一，6=周日
                'week': current_date.isocalendar()[1],  # 第几周
                'month': current_date.month
            })
            
            current_date += timedelta(days=1)
        
        # 计算最大值用于颜色映射
        max_count = max([d['count'] for d in heatmap_data]) if heatmap_data else 0
        
        return {
            'year': year,
            'data': heatmap_data,
            'max_count': max_count,
            'total_days': len([d for d in heatmap_data if d['count'] > 0]),
            'total_schedules': sum(daily_counts.values())
        }
    
    @classmethod
    def get_yearly_monthly_stats(cls, year: int) -> List[Dict[str, Any]]:
        """
        获取全年按月统计数据
        
        Args:
            year: 年份
        
        Returns:
            每月的统计数据列表
        """
        monthly_stats = []
        
        for month in range(1, 13):
            # 计算月份的开始和结束日期
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            
            # 查询该月的课程安排
            schedules = Schedule.query.filter(
                Schedule.schedule_date >= first_day,
                Schedule.schedule_date <= last_day
            ).all()
            
            # 统计
            schedule_count = len(schedules)
            unique_days = len(set(s.schedule_date for s in schedules))
            batch_ids = set(s.batch_id for s in schedules)
            
            monthly_stats.append({
                'month': month,
                'month_name': f'{month}月',
                'schedule_count': schedule_count,
                'teaching_days': unique_days,
                'batch_count': len(batch_ids),
                'workload': unique_days  # 授课天数作为工作量指标
            })
        
        return monthly_stats
    
    @classmethod
    def get_yearly_batch_timeline(cls, year: int) -> List[Dict[str, Any]]:
        """
        获取全年班次时间线数据
        
        Args:
            year: 年份
        
        Returns:
            班次时间线数据
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # 查询在该年内有课程的班次
        batches = ClassBatch.query.filter(
            db.or_(
                db.and_(ClassBatch.start_date >= start_date, ClassBatch.start_date <= end_date),
                db.and_(ClassBatch.end_date >= start_date, ClassBatch.end_date <= end_date),
                db.and_(ClassBatch.start_date <= start_date, ClassBatch.end_date >= end_date)
            )
        ).order_by(ClassBatch.start_date).all()
        
        timeline_data = []
        for batch in batches:
            # 计算在该年内的实际日期范围
            actual_start = max(batch.start_date, start_date) if batch.start_date else start_date
            actual_end = min(batch.end_date, end_date) if batch.end_date else end_date
            
            # 统计该班次的课程数
            schedule_count = Schedule.query.filter(
                Schedule.batch_id == batch.id,
                Schedule.schedule_date >= actual_start,
                Schedule.schedule_date <= actual_end
            ).count()
            
            timeline_data.append({
                'id': batch.id,
                'name': batch.name,
                'status': batch.status,
                'start_date': actual_start.isoformat(),
                'end_date': actual_end.isoformat(),
                'duration_days': (actual_end - actual_start).days + 1,
                'schedule_count': schedule_count,
                'enrolled_count': batch.enrolled_count or 0
            })
        
        return timeline_data
    
    @classmethod
    def get_yearly_subject_distribution(cls, year: int) -> List[Dict[str, Any]]:
        """
        获取全年科目分布统计
        
        Args:
            year: 年份
        
        Returns:
            科目分布数据
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # 按科目统计课程数
        results = db.session.query(
            Subject.name,
            func.count(Schedule.id).label('count')
        ).join(
            Schedule, Schedule.subject_id == Subject.id
        ).filter(
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date
        ).group_by(
            Subject.id, Subject.name
        ).order_by(
            func.count(Schedule.id).desc()
        ).all()
        
        # 计算总数用于百分比
        total = sum(r.count for r in results) if results else 1
        
        return [{
            'name': r.name,
            'count': r.count,
            'percentage': round(r.count / total * 100, 1)
        } for r in results]
