"""
老师服务 - 管理老师信息和排课
"""
from datetime import datetime, date
from decimal import Decimal
from app import db
from app.models.teacher import Teacher
from app.models.course import Schedule, Subject


class TeacherService:
    """老师服务类"""
    
    # ==================== 老师管理 ====================
    
    @staticmethod
    def get_teachers(subject_id=None, status='active', page=1, per_page=20):
        """
        获取老师列表
        
        Args:
            subject_id: 科目ID筛选
            status: 状态筛选
            page: 页码
            per_page: 每页数量
        
        Returns:
            Pagination: 分页对象
        """
        query = Teacher.query
        
        if status:
            query = query.filter(Teacher.status == status)
        
        if subject_id:
            # 模糊匹配科目ID
            query = query.filter(
                db.or_(
                    Teacher.subject_ids.like(f'{subject_id},%'),
                    Teacher.subject_ids.like(f'%,{subject_id},%'),
                    Teacher.subject_ids.like(f'%,{subject_id}'),
                    Teacher.subject_ids == str(subject_id)
                )
            )
        
        return query.order_by(Teacher.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_all_teachers(subject_id=None, status='active'):
        """获取所有老师（不分页）"""
        query = Teacher.query
        
        if status:
            query = query.filter(Teacher.status == status)
        
        if subject_id:
            query = query.filter(
                db.or_(
                    Teacher.subject_ids.like(f'{subject_id},%'),
                    Teacher.subject_ids.like(f'%,{subject_id},%'),
                    Teacher.subject_ids.like(f'%,{subject_id}'),
                    Teacher.subject_ids == str(subject_id)
                )
            )
        
        return query.order_by(Teacher.name).all()
    
    @staticmethod
    def get_teacher(teacher_id):
        """获取单个老师"""
        return Teacher.query.get(teacher_id)
    
    @staticmethod
    def create_teacher(data):
        """
        创建老师
        
        Args:
            data: {name, phone, subject_ids, daily_rate, hourly_rate, ...}
        
        Returns:
            Teacher: 创建的老师
        """
        teacher = Teacher(
            name=data.get('name'),
            phone=data.get('phone'),
            subject_ids=data.get('subject_ids', ''),
            daily_rate=Decimal(str(data.get('daily_rate', 0))) if data.get('daily_rate') else None,
            hourly_rate=Decimal(str(data.get('hourly_rate', 0))) if data.get('hourly_rate') else None,
            id_card=data.get('id_card'),
            bank_account=data.get('bank_account'),
            bank_name=data.get('bank_name'),
            remark=data.get('remark'),
            status='active'
        )
        db.session.add(teacher)
        db.session.commit()
        return teacher
    
    @staticmethod
    def update_teacher(teacher_id, data):
        """更新老师"""
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            raise ValueError('老师不存在')
        
        if 'name' in data:
            teacher.name = data['name']
        if 'phone' in data:
            teacher.phone = data['phone']
        if 'subject_ids' in data:
            teacher.subject_ids = data['subject_ids']
        if 'daily_rate' in data:
            teacher.daily_rate = Decimal(str(data['daily_rate'])) if data['daily_rate'] else None
        if 'hourly_rate' in data:
            teacher.hourly_rate = Decimal(str(data['hourly_rate'])) if data['hourly_rate'] else None
        if 'id_card' in data:
            teacher.id_card = data['id_card']
        if 'bank_account' in data:
            teacher.bank_account = data['bank_account']
        if 'bank_name' in data:
            teacher.bank_name = data['bank_name']
        if 'remark' in data:
            teacher.remark = data['remark']
        
        teacher.updated_at = datetime.utcnow()
        db.session.commit()
        return teacher
    
    @staticmethod
    def toggle_teacher_status(teacher_id):
        """切换老师状态"""
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            raise ValueError('老师不存在')
        
        teacher.status = 'inactive' if teacher.status == 'active' else 'active'
        teacher.updated_at = datetime.utcnow()
        db.session.commit()
        return teacher
    
    @staticmethod
    def delete_teacher(teacher_id):
        """删除老师"""
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            raise ValueError('老师不存在')
        
        # 检查是否有排课
        has_schedule = Schedule.query.filter(
            db.or_(
                Schedule.morning_teacher_id == teacher_id,
                Schedule.afternoon_teacher_id == teacher_id,
                Schedule.evening_teacher_id == teacher_id
            )
        ).count() > 0
        
        if has_schedule:
            raise ValueError('该老师有排课记录，无法删除')
        
        db.session.delete(teacher)
        db.session.commit()
        return True
    
    # ==================== 排课相关 ====================
    
    @staticmethod
    def get_teacher_schedules(teacher_id, start_date=None, end_date=None):
        """
        获取老师的排课记录
        
        Args:
            teacher_id: 老师ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[Schedule]: 排课列表
        """
        query = Schedule.query.filter(
            db.or_(
                Schedule.morning_teacher_id == teacher_id,
                Schedule.afternoon_teacher_id == teacher_id,
                Schedule.evening_teacher_id == teacher_id
            )
        )
        
        if start_date:
            query = query.filter(Schedule.schedule_date >= start_date)
        if end_date:
            query = query.filter(Schedule.schedule_date <= end_date)
        
        return query.order_by(Schedule.schedule_date).all()
    
    @staticmethod
    def check_conflict(teacher_id, check_date, exclude_schedule_id=None):
        """
        检查老师在指定日期是否有时间冲突
        
        Args:
            teacher_id: 老师ID
            check_date: 检查日期
            exclude_schedule_id: 排除的课表ID（用于编辑时）
        
        Returns:
            dict: {has_conflict: bool, schedules: List[Schedule]}
        """
        query = Schedule.query.filter(
            Schedule.schedule_date == check_date,
            db.or_(
                Schedule.morning_teacher_id == teacher_id,
                Schedule.afternoon_teacher_id == teacher_id,
                Schedule.evening_teacher_id == teacher_id
            )
        )
        
        if exclude_schedule_id:
            query = query.filter(Schedule.id != exclude_schedule_id)
        
        schedules = query.all()
        
        return {
            'has_conflict': len(schedules) > 0,
            'schedules': schedules
        }
    
    @staticmethod
    def get_available_teachers(subject_id, check_date):
        """
        获取指定日期可用的老师
        
        Args:
            subject_id: 科目ID
            check_date: 日期
        
        Returns:
            List[Teacher]: 可用老师列表
        """
        # 获取教授该科目的老师
        all_teachers = TeacherService.get_all_teachers(subject_id=subject_id, status='active')
        
        available = []
        for teacher in all_teachers:
            conflict = TeacherService.check_conflict(teacher.id, check_date)
            if not conflict['has_conflict']:
                available.append(teacher)
        
        return available
    
    # ==================== 统计 ====================
    
    @staticmethod
    def get_workload(teacher_id, start_date, end_date):
        """
        获取老师工作量统计
        
        Args:
            teacher_id: 老师ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            dict: {total_days, morning_count, afternoon_count, evening_count, total_amount}
        """
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            raise ValueError('老师不存在')
        
        return teacher.calculate_workload(start_date, end_date)
    
    @staticmethod
    def get_all_workload(start_date, end_date):
        """
        获取所有老师的工作量统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[dict]: 工作量列表
        """
        teachers = Teacher.query.filter_by(status='active').all()
        
        result = []
        for teacher in teachers:
            workload = teacher.calculate_workload(start_date, end_date)
            if workload['total_days'] > 0:
                result.append({
                    'teacher': teacher,
                    'workload': workload
                })
        
        # 按工作天数排序
        result.sort(key=lambda x: x['workload']['total_days'], reverse=True)
        
        return result
