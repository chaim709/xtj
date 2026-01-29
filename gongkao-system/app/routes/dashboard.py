"""
工作台路由 - 督学人员首页
"""
from datetime import datetime, date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.follow_up_service import FollowUpService
from app.services.schedule_service import ScheduleService
from app.services.reminder_service import ReminderService  # 第三阶段新增
from app.models.course import Project, ClassBatch
from app.models.teacher import Teacher

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """工作台首页"""
    # 获取统计数据
    supervisor_id = None if current_user.is_admin() else current_user.id
    
    stats = FollowUpService.get_dashboard_statistics(supervisor_id)
    recent_logs = FollowUpService.get_recent_logs(supervisor_id, limit=5)
    
    # 第二阶段新增：课程统计
    course_stats = get_course_statistics()
    today_schedules = ScheduleService.get_today_schedules()
    
    # 第三阶段新增：提醒数据
    reminders = ReminderService.get_dashboard_reminders()
    pending_follow_ups = ReminderService.get_pending_follow_ups(limit=5)
    attention_students = ReminderService.get_attention_students(limit=5)
    
    return render_template('dashboard/index.html',
                         stats=stats,
                         recent_logs=recent_logs,
                         course_stats=course_stats,
                         today_schedules=today_schedules,
                         reminders=reminders,
                         pending_follow_ups=pending_follow_ups,
                         attention_students=attention_students,
                         now=datetime.now)


def get_course_statistics():
    """
    获取课程相关统计数据
    
    Returns:
        dict: 课程统计数据
    """
    # 招生中的项目数量
    recruiting_projects = Project.query.filter_by(status='recruiting').count()
    
    # 正在进行的班次
    ongoing_batches = ClassBatch.query.filter_by(status='ongoing').count()
    
    # 招生中的班次
    recruiting_batches = ClassBatch.query.filter_by(status='recruiting').count()
    
    # 今日上课班次数
    today = date.today()
    today_batch_count = len(set(s.batch_id for s in ScheduleService.get_today_schedules()))
    
    # 活跃老师数量
    active_teachers = Teacher.query.filter_by(status='active').count()
    
    return {
        'recruiting_projects': recruiting_projects,
        'ongoing_batches': ongoing_batches,
        'recruiting_batches': recruiting_batches,
        'today_batch_count': today_batch_count,
        'active_teachers': active_teachers,
    }
