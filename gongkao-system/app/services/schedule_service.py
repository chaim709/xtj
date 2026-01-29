"""
课表服务 - 管理排课和变更记录
"""
from datetime import datetime, date, timedelta
from io import BytesIO
import json
from app import db
from app.models.course import Schedule, ScheduleChangeLog, ClassBatch, Subject
from app.models.teacher import Teacher


class ScheduleService:
    """课表服务类"""
    
    # ==================== 课表查询 ====================
    
    @staticmethod
    def get_schedules(batch_id):
        """
        获取班次的所有课表
        
        Args:
            batch_id: 班次ID
        
        Returns:
            List[Schedule]: 课表列表
        """
        return Schedule.query.filter_by(batch_id=batch_id).order_by(
            Schedule.schedule_date, Schedule.day_number
        ).all()
    
    @staticmethod
    def get_schedule(schedule_id):
        """获取单个课表"""
        return Schedule.query.get(schedule_id)
    
    @staticmethod
    def get_schedule_by_date(batch_id, schedule_date):
        """获取班次在指定日期的课表"""
        return Schedule.query.filter_by(
            batch_id=batch_id,
            schedule_date=schedule_date
        ).first()
    
    @staticmethod
    def get_today_schedules():
        """获取今日所有课表"""
        today = date.today()
        return Schedule.query.filter_by(schedule_date=today).join(ClassBatch).filter(
            ClassBatch.status == 'ongoing'
        ).all()
    
    @staticmethod
    def get_schedules_in_range(start_date, end_date, batch_id=None):
        """
        获取日期范围内的课表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            batch_id: 班次ID（可选）
        
        Returns:
            List[Schedule]: 课表列表
        """
        query = Schedule.query.filter(
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date
        )
        
        if batch_id:
            query = query.filter(Schedule.batch_id == batch_id)
        
        return query.order_by(Schedule.schedule_date).all()
    
    # ==================== 课表创建 ====================
    
    @staticmethod
    def create_schedule(data):
        """
        创建单个课表
        
        Args:
            data: {batch_id, schedule_date, day_number, subject_id, 
                   morning_teacher_id, afternoon_teacher_id, evening_type, evening_teacher_id, remark}
        
        Returns:
            Schedule: 创建的课表
        """
        schedule = Schedule(
            batch_id=data.get('batch_id'),
            schedule_date=data.get('schedule_date'),
            day_number=data.get('day_number'),
            subject_id=data.get('subject_id'),
            morning_teacher_id=data.get('morning_teacher_id'),
            afternoon_teacher_id=data.get('afternoon_teacher_id'),
            evening_type=data.get('evening_type', 'self_study'),
            evening_teacher_id=data.get('evening_teacher_id'),
            remark=data.get('remark')
        )
        db.session.add(schedule)
        db.session.commit()
        return schedule
    
    @staticmethod
    def batch_create_schedules(batch_id, schedule_list):
        """
        批量创建课表
        
        Args:
            batch_id: 班次ID
            schedule_list: 课表数据列表
        
        Returns:
            List[Schedule]: 创建的课表列表
        """
        schedules = []
        for data in schedule_list:
            data['batch_id'] = batch_id
            schedule = Schedule(
                batch_id=data.get('batch_id'),
                schedule_date=data.get('schedule_date'),
                day_number=data.get('day_number'),
                subject_id=data.get('subject_id'),
                morning_teacher_id=data.get('morning_teacher_id'),
                afternoon_teacher_id=data.get('afternoon_teacher_id'),
                evening_type=data.get('evening_type', 'self_study'),
                evening_teacher_id=data.get('evening_teacher_id'),
                remark=data.get('remark')
            )
            db.session.add(schedule)
            schedules.append(schedule)
        
        db.session.commit()
        return schedules
    
    @staticmethod
    def generate_schedules(batch_id, subject_days_list):
        """
        根据科目和天数自动生成课表
        
        Args:
            batch_id: 班次ID
            subject_days_list: [{'subject_id': 1, 'days': 4}, ...]
        
        Returns:
            List[Schedule]: 生成的课表列表
        """
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        # 删除现有课表
        Schedule.query.filter_by(batch_id=batch_id).delete()
        
        # 生成新课表
        schedules = []
        current_date = batch.start_date
        day_number = 1
        
        for item in subject_days_list:
            subject_id = item.get('subject_id')
            days = item.get('days', 1)
            
            for _ in range(days):
                schedule = Schedule(
                    batch_id=batch_id,
                    schedule_date=current_date,
                    day_number=day_number,
                    subject_id=subject_id,
                    evening_type='self_study'
                )
                db.session.add(schedule)
                schedules.append(schedule)
                
                current_date += timedelta(days=1)
                day_number += 1
        
        # 更新班次结束日期
        if schedules:
            batch.end_date = schedules[-1].schedule_date
            batch.actual_days = len(schedules)
        
        db.session.commit()
        return schedules
    
    @staticmethod
    def import_from_excel(batch_id, file_content, filename):
        """
        从Excel导入课表
        
        Args:
            batch_id: 班次ID
            file_content: 文件内容
            filename: 文件名
        
        Returns:
            dict: {'success': int, 'failed': int, 'errors': []}
        """
        import pandas as pd
        from io import BytesIO
        
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        try:
            # 读取Excel
            df = pd.read_excel(BytesIO(file_content))
            
            # 预期列：日期, 科目, 上午老师, 下午老师, 晚间安排, 备注
            required_columns = ['日期', '科目']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f'缺少必要列: {col}')
            
            # 获取科目和老师映射
            subjects = {s.name: s.id for s in Subject.query.all()}
            subjects.update({s.short_name: s.id for s in Subject.query.all() if s.short_name})
            
            teachers = {t.name: t.id for t in Teacher.query.filter_by(status='active').all()}
            
            evening_type_map = {
                '自习': 'self_study',
                '习题': 'exercise',
                '上课': 'class'
            }
            
            # 删除现有课表
            Schedule.query.filter_by(batch_id=batch_id).delete()
            
            success = 0
            failed = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # 解析日期
                    schedule_date = pd.to_datetime(row['日期']).date()
                    
                    # 解析科目
                    subject_name = str(row['科目']).strip()
                    subject_id = subjects.get(subject_name)
                    if not subject_id:
                        raise ValueError(f'科目不存在: {subject_name}')
                    
                    # 解析老师
                    morning_teacher_id = None
                    afternoon_teacher_id = None
                    evening_teacher_id = None
                    
                    if '上午老师' in df.columns and pd.notna(row.get('上午老师')):
                        teacher_name = str(row['上午老师']).strip()
                        morning_teacher_id = teachers.get(teacher_name)
                    
                    if '下午老师' in df.columns and pd.notna(row.get('下午老师')):
                        teacher_name = str(row['下午老师']).strip()
                        afternoon_teacher_id = teachers.get(teacher_name)
                    
                    # 解析晚间安排
                    evening_type = 'self_study'
                    if '晚间安排' in df.columns and pd.notna(row.get('晚间安排')):
                        evening_str = str(row['晚间安排']).strip()
                        evening_type = evening_type_map.get(evening_str, 'self_study')
                    
                    # 备注
                    remark = None
                    if '备注' in df.columns and pd.notna(row.get('备注')):
                        remark = str(row['备注']).strip()
                    
                    # 创建课表
                    schedule = Schedule(
                        batch_id=batch_id,
                        schedule_date=schedule_date,
                        day_number=index + 1,
                        subject_id=subject_id,
                        morning_teacher_id=morning_teacher_id,
                        afternoon_teacher_id=afternoon_teacher_id,
                        evening_type=evening_type,
                        evening_teacher_id=evening_teacher_id,
                        remark=remark
                    )
                    db.session.add(schedule)
                    success += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f'第{index + 2}行: {str(e)}')
            
            # 更新班次信息
            if success > 0:
                schedules = Schedule.query.filter_by(batch_id=batch_id).order_by(Schedule.schedule_date).all()
                if schedules:
                    batch.start_date = schedules[0].schedule_date
                    batch.end_date = schedules[-1].schedule_date
                    batch.actual_days = len(schedules)
            
            db.session.commit()
            
            return {
                'success': success,
                'failed': failed,
                'errors': errors
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f'导入失败: {str(e)}')
    
    @staticmethod
    def copy_from_batch(source_batch_id, target_batch_id):
        """
        从另一个班次复制课表
        
        Args:
            source_batch_id: 源班次ID
            target_batch_id: 目标班次ID
        
        Returns:
            List[Schedule]: 复制的课表列表
        """
        source_batch = ClassBatch.query.get(source_batch_id)
        target_batch = ClassBatch.query.get(target_batch_id)
        
        if not source_batch or not target_batch:
            raise ValueError('班次不存在')
        
        source_schedules = Schedule.query.filter_by(batch_id=source_batch_id).order_by(
            Schedule.day_number
        ).all()
        
        if not source_schedules:
            raise ValueError('源班次没有课表')
        
        # 删除目标班次现有课表
        Schedule.query.filter_by(batch_id=target_batch_id).delete()
        
        # 计算日期偏移
        date_offset = (target_batch.start_date - source_batch.start_date).days
        
        # 复制课表
        new_schedules = []
        for src in source_schedules:
            new_date = src.schedule_date + timedelta(days=date_offset)
            
            schedule = Schedule(
                batch_id=target_batch_id,
                schedule_date=new_date,
                day_number=src.day_number,
                subject_id=src.subject_id,
                morning_teacher_id=src.morning_teacher_id,
                afternoon_teacher_id=src.afternoon_teacher_id,
                evening_type=src.evening_type,
                evening_teacher_id=src.evening_teacher_id,
                remark=src.remark
            )
            db.session.add(schedule)
            new_schedules.append(schedule)
        
        # 更新目标班次结束日期
        if new_schedules:
            target_batch.end_date = new_schedules[-1].schedule_date
            target_batch.actual_days = len(new_schedules)
        
        db.session.commit()
        return new_schedules
    
    # ==================== 课表修改 ====================
    
    @staticmethod
    def update_schedule(schedule_id, data, operator_id, reason=None):
        """
        更新课表，自动记录变更
        
        Args:
            schedule_id: 课表ID
            data: 更新数据
            operator_id: 操作人ID
            reason: 变更原因
        
        Returns:
            Schedule: 更新后的课表
        """
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            raise ValueError('课表不存在')
        
        # 记录原值
        original = {
            'subject_id': schedule.subject_id,
            'morning_teacher_id': schedule.morning_teacher_id,
            'afternoon_teacher_id': schedule.afternoon_teacher_id,
            'evening_type': schedule.evening_type,
            'evening_teacher_id': schedule.evening_teacher_id,
            'schedule_date': schedule.schedule_date.isoformat() if schedule.schedule_date else None,
        }
        
        # 判断变更类型
        change_type = None
        
        # 检查是否换老师
        if ('morning_teacher_id' in data and data['morning_teacher_id'] != schedule.morning_teacher_id) or \
           ('afternoon_teacher_id' in data and data['afternoon_teacher_id'] != schedule.afternoon_teacher_id) or \
           ('evening_teacher_id' in data and data['evening_teacher_id'] != schedule.evening_teacher_id):
            change_type = 'teacher_change'
        
        # 检查是否调课
        if 'schedule_date' in data and data['schedule_date'] != schedule.schedule_date:
            change_type = 'reschedule'
        
        # 更新字段
        if 'subject_id' in data:
            schedule.subject_id = data['subject_id']
        if 'morning_teacher_id' in data:
            schedule.morning_teacher_id = data['morning_teacher_id']
        if 'afternoon_teacher_id' in data:
            schedule.afternoon_teacher_id = data['afternoon_teacher_id']
        if 'evening_type' in data:
            schedule.evening_type = data['evening_type']
        if 'evening_teacher_id' in data:
            schedule.evening_teacher_id = data['evening_teacher_id']
        if 'schedule_date' in data:
            schedule.schedule_date = data['schedule_date']
        if 'remark' in data:
            schedule.remark = data['remark']
        
        schedule.updated_at = datetime.utcnow()
        
        # 记录变更
        if change_type:
            new_value = {
                'subject_id': schedule.subject_id,
                'morning_teacher_id': schedule.morning_teacher_id,
                'afternoon_teacher_id': schedule.afternoon_teacher_id,
                'evening_type': schedule.evening_type,
                'evening_teacher_id': schedule.evening_teacher_id,
                'schedule_date': schedule.schedule_date.isoformat() if schedule.schedule_date else None,
            }
            
            ScheduleService.record_change(
                schedule_id=schedule_id,
                change_type=change_type,
                original=original,
                new=new_value,
                operator_id=operator_id,
                reason=reason
            )
        
        db.session.commit()
        return schedule
    
    @staticmethod
    def delete_schedule(schedule_id):
        """删除课表"""
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            raise ValueError('课表不存在')
        
        db.session.delete(schedule)
        db.session.commit()
        return True
    
    @staticmethod
    def delete_batch_schedules(batch_id):
        """删除班次所有课表"""
        count = Schedule.query.filter_by(batch_id=batch_id).delete()
        db.session.commit()
        return count
    
    # ==================== 变更记录 ====================
    
    @staticmethod
    def get_change_logs(schedule_id=None, batch_id=None, teacher_id=None, page=1, per_page=20):
        """
        获取变更记录
        
        Args:
            schedule_id: 课表ID筛选
            batch_id: 班次ID筛选
            teacher_id: 老师ID筛选
            page: 页码
            per_page: 每页数量
        
        Returns:
            Pagination: 分页对象
        """
        query = ScheduleChangeLog.query
        
        if schedule_id:
            query = query.filter(ScheduleChangeLog.schedule_id == schedule_id)
        
        if batch_id:
            query = query.join(Schedule).filter(Schedule.batch_id == batch_id)
        
        if teacher_id:
            # 筛选涉及该老师的变更
            query = query.filter(
                db.or_(
                    ScheduleChangeLog.original_value.like(f'%"morning_teacher_id": {teacher_id}%'),
                    ScheduleChangeLog.original_value.like(f'%"afternoon_teacher_id": {teacher_id}%'),
                    ScheduleChangeLog.new_value.like(f'%"morning_teacher_id": {teacher_id}%'),
                    ScheduleChangeLog.new_value.like(f'%"afternoon_teacher_id": {teacher_id}%'),
                )
            )
        
        return query.order_by(ScheduleChangeLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def record_change(schedule_id, change_type, original, new, operator_id, reason=None):
        """
        记录变更
        
        Args:
            schedule_id: 课表ID
            change_type: 变更类型
            original: 原值
            new: 新值
            operator_id: 操作人ID
            reason: 变更原因
        
        Returns:
            ScheduleChangeLog: 变更记录
        """
        log = ScheduleChangeLog(
            schedule_id=schedule_id,
            change_type=change_type,
            original_value=json.dumps(original, ensure_ascii=False, default=str),
            new_value=json.dumps(new, ensure_ascii=False, default=str),
            reason=reason,
            operator_id=operator_id
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    # ==================== 导出 ====================
    
    @staticmethod
    def export_to_excel(batch_id):
        """
        导出课表为Excel
        
        Args:
            batch_id: 班次ID
        
        Returns:
            BytesIO: Excel文件内容
        """
        import pandas as pd
        
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        schedules = ScheduleService.get_schedules(batch_id)
        
        # 构建数据
        data = []
        for s in schedules:
            data.append({
                '日期': s.schedule_date.strftime('%Y-%m-%d') if s.schedule_date else '',
                '第几天': s.day_number,
                '科目': s.subject.name if s.subject else '',
                '上午老师': s.morning_teacher.name if s.morning_teacher else '',
                '下午老师': s.afternoon_teacher.name if s.afternoon_teacher else '',
                '晚间安排': s.evening_type_display,
                '晚间老师': s.evening_teacher.name if s.evening_teacher else '',
                '备注': s.remark or ''
            })
        
        df = pd.DataFrame(data)
        
        # 导出
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=batch.name)
        
        output.seek(0)
        return output
    
    @staticmethod
    def get_schedule_template():
        """
        获取课表导入模板
        
        Returns:
            BytesIO: Excel模板文件
        """
        import pandas as pd
        
        # 模板数据
        data = [
            {
                '日期': '2026-03-01',
                '科目': '言语',
                '上午老师': '张老师',
                '下午老师': '张老师',
                '晚间安排': '自习',
                '备注': ''
            },
            {
                '日期': '2026-03-02',
                '科目': '言语',
                '上午老师': '张老师',
                '下午老师': '张老师',
                '晚间安排': '习题',
                '备注': ''
            }
        ]
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='课表模板')
        
        output.seek(0)
        return output
