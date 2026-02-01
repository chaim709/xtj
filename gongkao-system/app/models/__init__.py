"""
数据模型包
"""
from app.models.user import User
from app.models.student import Student
from app.models.tag import WeaknessTag, ModuleCategory
from app.models.supervision import SupervisionLog
from app.models.homework import HomeworkTask, HomeworkSubmission

# 第二阶段新增模型
from app.models.teacher import Teacher
from app.models.course import (
    Subject,
    Project,
    Package,
    ClassType,
    ClassBatch,
    Schedule,
    ScheduleChangeLog,
    StudentBatch,
    Attendance,
    CourseRecording,
)

# 学习计划模型
from app.models.study_plan import (
    PlanTemplate,
    StudyPlan,
    PlanGoal,
    PlanTask,
    PlanProgress,
)

# 智能选岗模型
from app.models.position import Position, StudentPosition
from app.models.major import MajorCategory, Major

# 题库与错题模型（从cuoti-system合并）
from app.models.question import (
    Institution,
    WorkbookTemplate,
    Question,
    Workbook,
    WorkbookItem,
    WorkbookPage,
    Submission,
    Mistake,
    MistakeReview,
    StudentStats,
    StudentClass,
)

# 打卡与消息模型
from app.models.checkin import CheckinRecord
from app.models.message import StudentMessage, WxSubscribeTemplate

__all__ = [
    # 第一阶段模型
    'User',
    'Student',
    'WeaknessTag',
    'ModuleCategory',
    'SupervisionLog',
    'HomeworkTask',
    'HomeworkSubmission',
    # 第二阶段模型
    'Teacher',
    'Subject',
    'Project',
    'Package',
    'ClassType',
    'ClassBatch',
    'Schedule',
    'ScheduleChangeLog',
    'StudentBatch',
    'Attendance',
    'CourseRecording',
    # 学习计划模型
    'PlanTemplate',
    'StudyPlan',
    'PlanGoal',
    'PlanTask',
    'PlanProgress',
    # 智能选岗模型
    'Position',
    'StudentPosition',
    'MajorCategory',
    'Major',
    # 题库与错题模型
    'Institution',
    'WorkbookTemplate',
    'Question',
    'Workbook',
    'WorkbookItem',
    'WorkbookPage',
    'Submission',
    'Mistake',
    'MistakeReview',
    'StudentStats',
    'StudentClass',
    # 打卡与消息模型
    'CheckinRecord',
    'StudentMessage',
    'WxSubscribeTemplate',
]
