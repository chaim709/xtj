"""
作业服务 - 作业管理业务逻辑
"""
from datetime import datetime
from app import db
from app.models.homework import HomeworkTask, HomeworkSubmission
from app.models.student import Student
from app.services.tag_service import TagService
import json


class HomeworkService:
    """作业服务类"""
    
    @staticmethod
    def create_task(data):
        """
        创建作业任务
        
        Args:
            data: 任务数据字典
        
        Returns:
            创建的任务对象
        """
        # 处理目标学员
        target_students = data.get('target_students', [])
        if isinstance(target_students, list):
            target_students = ','.join(str(s) for s in target_students)
        
        task = HomeworkTask(
            task_name=data.get('task_name'),
            task_type=data.get('task_type'),
            module=data.get('module'),
            sub_module=data.get('sub_module'),
            question_count=data.get('question_count'),
            suggested_time=data.get('suggested_time'),
            deadline=data.get('deadline'),
            target_class=data.get('target_class'),
            target_students=target_students,
            description=data.get('description'),
            creator_id=data.get('creator_id'),
            publish_time=datetime.utcnow(),
            status='published',
        )
        
        db.session.add(task)
        db.session.commit()
        return task
    
    @staticmethod
    def get_task(task_id):
        """获取任务详情"""
        return HomeworkTask.query.get(task_id)
    
    @staticmethod
    def get_tasks(status=None, creator_id=None, page=1, per_page=20):
        """
        获取作业列表
        
        Args:
            status: 状态筛选
            creator_id: 创建人ID
            page: 页码
            per_page: 每页数量
        
        Returns:
            分页结果
        """
        query = HomeworkTask.query
        
        if status:
            query = query.filter_by(status=status)
        if creator_id:
            query = query.filter_by(creator_id=creator_id)
        
        query = query.order_by(HomeworkTask.created_at.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def close_task(task_id):
        """关闭作业任务"""
        task = HomeworkTask.query.get(task_id)
        if task:
            task.status = 'closed'
            db.session.commit()
        return task
    
    @staticmethod
    def record_submission(task_id, student_id, data, recorder_id):
        """
        录入学员作业完成情况
        
        Args:
            task_id: 任务ID
            student_id: 学员ID
            data: 提交数据
            recorder_id: 录入人ID
        
        Returns:
            提交记录对象
        """
        task = HomeworkTask.query.get(task_id)
        if not task:
            raise ValueError('作业任务不存在')
        
        # 检查是否已提交
        existing = HomeworkSubmission.query.filter_by(
            task_id=task_id,
            student_id=student_id
        ).first()
        
        if existing:
            # 更新现有记录
            existing.completed_count = data.get('completed_count')
            existing.correct_count = data.get('correct_count')
            existing.time_spent = data.get('time_spent')
            existing.wrong_questions = data.get('wrong_questions')
            existing.feedback = data.get('feedback')
            existing.recorder_id = recorder_id
            existing.calculate_accuracy()
            
            # 检查是否逾期
            if task.deadline and datetime.utcnow() > task.deadline:
                existing.is_late = True
            
            db.session.commit()
            submission = existing
        else:
            # 创建新记录
            submission = HomeworkSubmission(
                task_id=task_id,
                student_id=student_id,
                completed_count=data.get('completed_count'),
                correct_count=data.get('correct_count'),
                time_spent=data.get('time_spent'),
                wrong_questions=data.get('wrong_questions'),
                feedback=data.get('feedback'),
                recorder_id=recorder_id,
            )
            submission.calculate_accuracy()
            
            # 检查是否逾期
            if task.deadline and datetime.utcnow() > task.deadline:
                submission.is_late = True
            
            db.session.add(submission)
            db.session.commit()
        
        # 自动打标签（正确率低于70%）
        if submission.accuracy_rate is not None and submission.accuracy_rate < 70:
            TagService.auto_tag_from_homework(
                student_id=student_id,
                module=task.module,
                sub_module=task.sub_module,
                accuracy_rate=submission.accuracy_rate
            )
        
        return submission
    
    @staticmethod
    def get_submissions_by_task(task_id):
        """获取作业的所有提交记录"""
        return HomeworkSubmission.query.filter_by(task_id=task_id)\
            .order_by(HomeworkSubmission.submit_time.desc()).all()
    
    @staticmethod
    def get_submissions_by_student(student_id, limit=None):
        """获取学员的作业提交记录"""
        query = HomeworkSubmission.query.filter_by(student_id=student_id)\
            .order_by(HomeworkSubmission.submit_time.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_task_statistics(task_id):
        """获取作业统计信息"""
        task = HomeworkTask.query.get(task_id)
        if not task:
            return None
        
        submissions = task.submissions.all()
        
        # 目标学员
        target_ids = []
        if task.target_students:
            target_ids = [int(x) for x in task.target_students.split(',') if x.strip()]
        
        total_target = len(target_ids) if target_ids else 0
        completed = len(submissions)
        
        # 统计
        if completed > 0:
            avg_rate = sum(s.accuracy_rate or 0 for s in submissions) / completed
            avg_time = sum(s.time_spent or 0 for s in submissions) / completed
            late_count = sum(1 for s in submissions if s.is_late)
        else:
            avg_rate = 0
            avg_time = 0
            late_count = 0
        
        # 未完成学员
        completed_ids = set(s.student_id for s in submissions)
        uncompleted_ids = set(target_ids) - completed_ids
        uncompleted_students = Student.query.filter(Student.id.in_(uncompleted_ids)).all() if uncompleted_ids else []
        
        return {
            'total_target': total_target,
            'completed': completed,
            'completion_rate': (completed / total_target * 100) if total_target > 0 else 0,
            'avg_accuracy_rate': round(avg_rate, 1),
            'avg_time_spent': round(avg_time, 1),
            'late_count': late_count,
            'uncompleted_students': uncompleted_students,
        }
