"""
考勤服务 - 管理学员考勤记录
"""
from datetime import datetime, date
from app import db
from app.models.course import Attendance, Schedule, ClassBatch, StudentBatch


class AttendanceService:
    """考勤服务类"""
    
    @staticmethod
    def get_attendance(attendance_id):
        """获取单个考勤记录"""
        return Attendance.query.get(attendance_id)
    
    @staticmethod
    def get_attendance_by_date(batch_id, attendance_date):
        """
        获取班次在指定日期的所有考勤记录
        
        Args:
            batch_id: 班次ID
            attendance_date: 日期
        
        Returns:
            List[Attendance]: 考勤记录列表
        """
        return Attendance.query.filter_by(
            batch_id=batch_id,
            attendance_date=attendance_date
        ).all()
    
    @staticmethod
    def get_student_attendance(student_id, batch_id=None):
        """
        获取学员的考勤记录
        
        Args:
            student_id: 学员ID
            batch_id: 班次ID（可选）
        
        Returns:
            List[Attendance]: 考勤记录列表
        """
        query = Attendance.query.filter_by(student_id=student_id)
        
        if batch_id:
            query = query.filter_by(batch_id=batch_id)
        
        return query.order_by(Attendance.attendance_date.desc()).all()
    
    @staticmethod
    def record_attendance(data):
        """
        记录考勤
        
        Args:
            data: {student_id, batch_id, schedule_id, attendance_date, status, check_in_time, remark}
        
        Returns:
            Attendance: 创建的考勤记录
        """
        # 检查是否已存在
        existing = Attendance.query.filter_by(
            student_id=data.get('student_id'),
            schedule_id=data.get('schedule_id')
        ).first()
        
        if existing:
            # 更新现有记录
            existing.status = data.get('status')
            existing.check_in_time = data.get('check_in_time')
            existing.remark = data.get('remark')
            db.session.commit()
            return existing
        
        # 创建新记录
        attendance = Attendance(
            student_id=data.get('student_id'),
            batch_id=data.get('batch_id'),
            schedule_id=data.get('schedule_id'),
            attendance_date=data.get('attendance_date'),
            status=data.get('status'),
            check_in_time=data.get('check_in_time'),
            remark=data.get('remark')
        )
        db.session.add(attendance)
        db.session.commit()
        return attendance
    
    @staticmethod
    def batch_record_attendance(batch_id, schedule_id, attendance_date, records):
        """
        批量记录考勤
        
        Args:
            batch_id: 班次ID
            schedule_id: 课表ID
            attendance_date: 日期
            records: [{student_id, status, remark}, ...]
        
        Returns:
            int: 记录数量
        """
        count = 0
        for record in records:
            data = {
                'batch_id': batch_id,
                'schedule_id': schedule_id,
                'attendance_date': attendance_date,
                'student_id': record.get('student_id'),
                'status': record.get('status', 'present'),
                'remark': record.get('remark'),
            }
            AttendanceService.record_attendance(data)
            count += 1
        
        return count
    
    @staticmethod
    def get_batch_statistics(batch_id):
        """
        获取班次考勤统计
        
        Args:
            batch_id: 班次ID
        
        Returns:
            dict: {
                total_days: int,
                recorded_days: int,
                student_stats: [{student_id, student_name, present, absent, late, leave, rate}, ...]
            }
        """
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        # 获取班次学员
        student_batches = batch.student_batches.filter_by(status='active').all()
        
        # 获取课表天数
        total_days = batch.schedules.count()
        
        # 获取已记录考勤的天数
        recorded_days = db.session.query(Attendance.attendance_date).filter_by(
            batch_id=batch_id
        ).distinct().count()
        
        # 统计每个学员的考勤
        student_stats = []
        for sb in student_batches:
            student = sb.student
            attendances = Attendance.query.filter_by(
                student_id=student.id,
                batch_id=batch_id
            ).all()
            
            present = sum(1 for a in attendances if a.status == 'present')
            absent = sum(1 for a in attendances if a.status == 'absent')
            late = sum(1 for a in attendances if a.status == 'late')
            leave = sum(1 for a in attendances if a.status == 'leave')
            
            total = present + absent + late + leave
            rate = round(present / total * 100, 1) if total > 0 else 0
            
            student_stats.append({
                'student_id': student.id,
                'student_name': student.name,
                'present': present,
                'absent': absent,
                'late': late,
                'leave': leave,
                'total': total,
                'rate': rate
            })
        
        # 按出勤率排序
        student_stats.sort(key=lambda x: x['rate'], reverse=True)
        
        return {
            'total_days': total_days,
            'recorded_days': recorded_days,
            'student_stats': student_stats
        }
    
    @staticmethod
    def get_daily_summary(batch_id, attendance_date):
        """
        获取某天的考勤汇总
        
        Args:
            batch_id: 班次ID
            attendance_date: 日期
        
        Returns:
            dict: {present, absent, late, leave, not_recorded}
        """
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        # 获取班次学员数
        total_students = batch.student_batches.filter_by(status='active').count()
        
        # 获取当天考勤记录
        attendances = Attendance.query.filter_by(
            batch_id=batch_id,
            attendance_date=attendance_date
        ).all()
        
        present = sum(1 for a in attendances if a.status == 'present')
        absent = sum(1 for a in attendances if a.status == 'absent')
        late = sum(1 for a in attendances if a.status == 'late')
        leave = sum(1 for a in attendances if a.status == 'leave')
        
        recorded = len(attendances)
        not_recorded = total_students - recorded
        
        return {
            'total_students': total_students,
            'present': present,
            'absent': absent,
            'late': late,
            'leave': leave,
            'not_recorded': not_recorded
        }
    
    @staticmethod
    def get_students_not_checked(batch_id, attendance_date):
        """
        获取未签到的学员
        
        Args:
            batch_id: 班次ID
            attendance_date: 日期
        
        Returns:
            List[Student]: 学员列表
        """
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            return []
        
        # 获取已签到的学员ID
        checked_student_ids = db.session.query(Attendance.student_id).filter_by(
            batch_id=batch_id,
            attendance_date=attendance_date
        ).all()
        checked_student_ids = [x[0] for x in checked_student_ids]
        
        # 获取班次学员中未签到的
        student_batches = batch.student_batches.filter(
            StudentBatch.status == 'active',
            ~StudentBatch.student_id.in_(checked_student_ids) if checked_student_ids else True
        ).all()
        
        return [sb.student for sb in student_batches]
