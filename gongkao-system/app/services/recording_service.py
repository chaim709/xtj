"""
录播管理服务 - 课程录播的增删改查
"""
from datetime import datetime, date
from app import db
from app.models.course import CourseRecording, ClassBatch, Schedule, Subject
from app.models.teacher import Teacher


class RecordingService:
    """录播管理服务类"""
    
    @staticmethod
    def get_recordings(batch_id=None, subject_id=None, start_date=None, end_date=None,
                       page=1, per_page=20):
        """
        获取录播列表
        
        Args:
            batch_id: 班次ID筛选
            subject_id: 科目ID筛选
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            per_page: 每页数量
        
        Returns:
            分页对象
        """
        query = CourseRecording.query
        
        if batch_id:
            query = query.filter(CourseRecording.batch_id == batch_id)
        if subject_id:
            query = query.filter(CourseRecording.subject_id == subject_id)
        if start_date:
            query = query.filter(CourseRecording.recording_date >= start_date)
        if end_date:
            query = query.filter(CourseRecording.recording_date <= end_date)
        
        query = query.order_by(CourseRecording.recording_date.desc(), CourseRecording.period.asc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_recordings_by_batch(batch_id):
        """
        获取班次下所有录播
        
        Args:
            batch_id: 班次ID
        
        Returns:
            录播列表
        """
        return CourseRecording.query.filter_by(batch_id=batch_id)\
            .order_by(CourseRecording.recording_date.desc(), CourseRecording.period.asc())\
            .all()
    
    @staticmethod
    def get_recordings_by_student(student_id):
        """
        获取学员所在班次的所有录播
        
        Args:
            student_id: 学员ID
        
        Returns:
            录播列表
        """
        from app.models.course import StudentBatch
        
        # 获取学员的所有班次
        student_batches = StudentBatch.query.filter_by(
            student_id=student_id,
            status='active'
        ).all()
        
        batch_ids = [sb.batch_id for sb in student_batches]
        
        if not batch_ids:
            return []
        
        return CourseRecording.query.filter(CourseRecording.batch_id.in_(batch_ids))\
            .order_by(CourseRecording.recording_date.desc(), CourseRecording.period.asc())\
            .all()
    
    @staticmethod
    def get_recording(recording_id):
        """
        获取单个录播
        
        Args:
            recording_id: 录播ID
        
        Returns:
            录播对象或None
        """
        return CourseRecording.query.get(recording_id)
    
    @staticmethod
    def create_recording(data, user_id=None):
        """
        创建录播记录
        
        Args:
            data: 录播数据字典
            user_id: 创建人ID
        
        Returns:
            新创建的录播对象
        """
        recording = CourseRecording(
            batch_id=data['batch_id'],
            schedule_id=data.get('schedule_id'),
            recording_date=data['recording_date'],
            period=data.get('period', 'morning'),
            title=data['title'],
            recording_url=data['recording_url'],
            subject_id=data.get('subject_id'),
            teacher_id=data.get('teacher_id'),
            duration_minutes=data.get('duration_minutes'),
            remark=data.get('remark', ''),
            created_by=user_id
        )
        
        db.session.add(recording)
        db.session.commit()
        
        return recording
    
    @staticmethod
    def update_recording(recording_id, data):
        """
        更新录播记录
        
        Args:
            recording_id: 录播ID
            data: 更新数据
        
        Returns:
            更新后的录播对象
        """
        recording = CourseRecording.query.get(recording_id)
        if not recording:
            raise ValueError('录播记录不存在')
        
        if 'recording_date' in data:
            recording.recording_date = data['recording_date']
        if 'period' in data:
            recording.period = data['period']
        if 'title' in data:
            recording.title = data['title']
        if 'recording_url' in data:
            recording.recording_url = data['recording_url']
        if 'subject_id' in data:
            recording.subject_id = data['subject_id']
        if 'teacher_id' in data:
            recording.teacher_id = data['teacher_id']
        if 'duration_minutes' in data:
            recording.duration_minutes = data['duration_minutes']
        if 'remark' in data:
            recording.remark = data['remark']
        if 'schedule_id' in data:
            recording.schedule_id = data['schedule_id']
        
        db.session.commit()
        
        return recording
    
    @staticmethod
    def delete_recording(recording_id):
        """
        删除录播记录
        
        Args:
            recording_id: 录播ID
        """
        recording = CourseRecording.query.get(recording_id)
        if not recording:
            raise ValueError('录播记录不存在')
        
        db.session.delete(recording)
        db.session.commit()
    
    @staticmethod
    def get_batch_recording_stats(batch_id):
        """
        获取班次录播统计
        
        Args:
            batch_id: 班次ID
        
        Returns:
            统计数据字典
        """
        recordings = CourseRecording.query.filter_by(batch_id=batch_id).all()
        
        total_count = len(recordings)
        total_duration = sum(r.duration_minutes or 0 for r in recordings)
        
        # 按时段统计
        period_stats = {
            'morning': 0,
            'afternoon': 0,
            'evening': 0
        }
        for r in recordings:
            if r.period in period_stats:
                period_stats[r.period] += 1
        
        return {
            'total_count': total_count,
            'total_duration': total_duration,
            'period_stats': period_stats
        }
    
    @staticmethod
    def get_recent_recordings(limit=10):
        """
        获取最近的录播
        
        Args:
            limit: 数量限制
        
        Returns:
            录播列表
        """
        return CourseRecording.query\
            .order_by(CourseRecording.created_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_all_batches():
        """
        获取所有班次（用于下拉选择）
        
        Returns:
            班次列表
        """
        return ClassBatch.query\
            .filter(ClassBatch.status.in_(['recruiting', 'ongoing']))\
            .order_by(ClassBatch.start_date.desc())\
            .all()
    
    @staticmethod
    def get_subjects():
        """
        获取所有科目（用于下拉选择）
        
        Returns:
            科目列表
        """
        return Subject.query.filter_by(status='active').order_by(Subject.sort_order).all()
    
    @staticmethod
    def get_teachers():
        """
        获取所有老师（用于下拉选择）
        
        Returns:
            老师列表
        """
        return Teacher.query.filter_by(status='active').order_by(Teacher.name).all()
