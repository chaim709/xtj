"""
督学服务 - 督学日志管理与督学管理
"""
from datetime import datetime, date, timedelta
import json
from sqlalchemy import func, and_, or_
from app import db
from app.models.supervision import SupervisionLog
from app.models.student import Student
from app.models.study_plan import StudyPlan, PlanGoal, PlanTask, PlanProgress, PlanTemplate
from app.models.user import User


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
    
    # ==================== 督学管理功能 ====================
    
    @staticmethod
    def get_management_overview(supervisor_id=None):
        """
        获取督学管理概览数据
        
        Args:
            supervisor_id: 督学人员ID（可选，管理员为空查看所有）
        
        Returns:
            概览统计数据
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        # 学员查询基础
        student_query = Student.query.filter_by(status='active')
        if supervisor_id:
            student_query = student_query.filter_by(supervisor_id=supervisor_id)
        
        total_students = student_query.count()
        
        # 待跟进学员（超过设定天数未联系或今日需跟进）
        pending_followup = student_query.filter(
            or_(
                Student.last_contact_date == None,
                Student.last_contact_date < today - timedelta(days=3),
                Student.id.in_(
                    db.session.query(SupervisionLog.student_id).filter(
                        SupervisionLog.next_follow_up_date == today
                    )
                )
            )
        ).count()
        
        # 本周已联系学员
        week_contacted = db.session.query(func.count(func.distinct(SupervisionLog.student_id))).filter(
            SupervisionLog.log_date >= week_start,
            SupervisionLog.log_date <= today
        )
        if supervisor_id:
            week_contacted = week_contacted.filter(SupervisionLog.supervisor_id == supervisor_id)
        week_contacted = week_contacted.scalar() or 0
        
        # 逾期任务数
        overdue_tasks = PlanTask.query.join(StudyPlan).filter(
            PlanTask.is_completed == False,
            PlanTask.due_date < today,
            StudyPlan.status == 'active'
        )
        if supervisor_id:
            overdue_tasks = overdue_tasks.join(Student, StudyPlan.student_id == Student.id).filter(
                Student.supervisor_id == supervisor_id
            )
        overdue_count = overdue_tasks.count()
        
        # 计划完成率
        active_plans = StudyPlan.query.filter_by(status='active')
        if supervisor_id:
            active_plans = active_plans.join(Student).filter(Student.supervisor_id == supervisor_id)
        
        plans = active_plans.all()
        if plans:
            total_progress = sum(p.task_progress for p in plans)
            avg_progress = round(total_progress / len(plans), 1)
        else:
            avg_progress = 0
        
        return {
            'total_students': total_students,
            'pending_followup': pending_followup,
            'week_contacted': week_contacted,
            'overdue_tasks': overdue_count,
            'avg_plan_progress': avg_progress,
        }
    
    @staticmethod
    def get_students_for_supervision(supervisor_id=None, filter_type='all', page=1, per_page=20):
        """
        获取督学学员列表
        
        Args:
            supervisor_id: 督学人员ID
            filter_type: 筛选类型 (all/pending/contacted/overdue)
            page: 页码
            per_page: 每页数量
        
        Returns:
            学员列表及督学信息
        """
        today = date.today()
        
        query = Student.query.filter_by(status='active')
        if supervisor_id:
            query = query.filter_by(supervisor_id=supervisor_id)
        
        if filter_type == 'pending':
            # 待跟进：3天未联系或有今日跟进提醒
            query = query.filter(
                or_(
                    Student.last_contact_date == None,
                    Student.last_contact_date < today - timedelta(days=3),
                    Student.id.in_(
                        db.session.query(SupervisionLog.student_id).filter(
                            SupervisionLog.next_follow_up_date == today
                        )
                    )
                )
            )
        elif filter_type == 'contacted':
            # 本周已联系
            week_start = today - timedelta(days=today.weekday())
            query = query.filter(
                Student.last_contact_date >= week_start
            )
        elif filter_type == 'overdue':
            # 有逾期任务的学员
            query = query.filter(
                Student.id.in_(
                    db.session.query(StudyPlan.student_id).join(PlanTask).filter(
                        PlanTask.is_completed == False,
                        PlanTask.due_date < today,
                        StudyPlan.status == 'active'
                    )
                )
            )
        
        students = query.order_by(Student.last_contact_date.asc().nullsfirst()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 附加督学信息
        result = []
        for s in students.items:
            # 获取最近督学记录
            last_log = SupervisionLog.query.filter_by(student_id=s.id)\
                .order_by(SupervisionLog.log_date.desc()).first()
            
            # 获取当前学习计划
            current_plan = StudyPlan.query.filter_by(
                student_id=s.id, status='active'
            ).first()
            
            # 判断是否需要跟进
            needs_followup = False
            if not s.last_contact_date or s.last_contact_date < today - timedelta(days=3):
                needs_followup = True
            if last_log and last_log.next_follow_up_date == today:
                needs_followup = True
            
            result.append({
                'id': s.id,
                'name': s.name,
                'phone': s.phone,
                'last_contact_date': s.last_contact_date.isoformat() if s.last_contact_date else None,
                'days_since_contact': (today - s.last_contact_date).days if s.last_contact_date else None,
                'last_mood': last_log.student_mood if last_log else None,
                'last_status': last_log.study_status if last_log else None,
                'current_plan': current_plan.name if current_plan else None,
                'plan_progress': current_plan.task_progress if current_plan else 0,
                'needs_followup': needs_followup,
                'supervisor_id': s.supervisor_id,
            })
        
        return {
            'items': result,
            'total': students.total,
            'pages': students.pages,
            'page': page,
        }
    
    @staticmethod
    def get_plans_overview(supervisor_id=None, status='active', page=1, per_page=20):
        """
        获取学习计划概览
        
        Args:
            supervisor_id: 督学人员ID
            status: 计划状态
            page: 页码
            per_page: 每页数量
        
        Returns:
            计划列表
        """
        query = StudyPlan.query
        
        if status:
            query = query.filter_by(status=status)
        
        if supervisor_id:
            query = query.join(Student).filter(Student.supervisor_id == supervisor_id)
        
        plans = query.order_by(StudyPlan.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for p in plans.items:
            result.append({
                **p.to_dict(),
                'overdue_tasks': p.tasks.filter(
                    PlanTask.is_completed == False,
                    PlanTask.due_date < date.today()
                ).count(),
            })
        
        return {
            'items': result,
            'total': plans.total,
            'pages': plans.pages,
            'page': page,
        }
    
    @staticmethod
    def get_supervision_logs_overview(supervisor_id=None, student_id=None, 
                                      start_date=None, end_date=None,
                                      page=1, per_page=20):
        """
        获取督学记录概览
        
        Args:
            supervisor_id: 督学人员ID
            student_id: 学员ID
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            per_page: 每页数量
        
        Returns:
            督学记录列表
        """
        query = SupervisionLog.query
        
        if supervisor_id:
            query = query.filter_by(supervisor_id=supervisor_id)
        if student_id:
            query = query.filter_by(student_id=student_id)
        if start_date:
            query = query.filter(SupervisionLog.log_date >= start_date)
        if end_date:
            query = query.filter(SupervisionLog.log_date <= end_date)
        
        logs = query.order_by(SupervisionLog.log_date.desc(), SupervisionLog.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for log in logs.items:
            student = Student.query.get(log.student_id)
            result.append({
                **log.to_dict(),
                'student_name': student.name if student else None,
                'self_discipline': log.self_discipline,
                'actions': log.actions,
                'tags': log.tags,
            })
        
        return {
            'items': result,
            'total': logs.total,
            'pages': logs.pages,
            'page': page,
        }
    
    @staticmethod
    def get_performance_stats(supervisor_id=None, start_date=None, end_date=None):
        """
        获取业绩统计数据
        
        Args:
            supervisor_id: 督学人员ID（可选）
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            业绩统计数据
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # 督学工作量统计
        workload_query = db.session.query(
            SupervisionLog.supervisor_id,
            func.count(SupervisionLog.id).label('log_count'),
            func.count(func.distinct(SupervisionLog.student_id)).label('student_count')
        ).filter(
            SupervisionLog.log_date >= start_date,
            SupervisionLog.log_date <= end_date
        ).group_by(SupervisionLog.supervisor_id)
        
        if supervisor_id:
            workload_query = workload_query.filter(SupervisionLog.supervisor_id == supervisor_id)
        
        workload_data = []
        for row in workload_query.all():
            user = User.query.get(row.supervisor_id)
            workload_data.append({
                'supervisor_id': row.supervisor_id,
                'supervisor_name': user.username if user else '未知',
                'log_count': row.log_count,
                'student_count': row.student_count,
            })
        
        # 心态分布统计
        mood_query = db.session.query(
            SupervisionLog.student_mood,
            func.count(SupervisionLog.id).label('count')
        ).filter(
            SupervisionLog.log_date >= start_date,
            SupervisionLog.log_date <= end_date,
            SupervisionLog.student_mood != None
        ).group_by(SupervisionLog.student_mood)
        
        if supervisor_id:
            mood_query = mood_query.filter(SupervisionLog.supervisor_id == supervisor_id)
        
        mood_stats = {row.student_mood: row.count for row in mood_query.all()}
        
        # 学习状态分布
        status_query = db.session.query(
            SupervisionLog.study_status,
            func.count(SupervisionLog.id).label('count')
        ).filter(
            SupervisionLog.log_date >= start_date,
            SupervisionLog.log_date <= end_date,
            SupervisionLog.study_status != None
        ).group_by(SupervisionLog.study_status)
        
        if supervisor_id:
            status_query = status_query.filter(SupervisionLog.supervisor_id == supervisor_id)
        
        status_stats = {row.study_status: row.count for row in status_query.all()}
        
        # 日趋势统计
        daily_query = db.session.query(
            SupervisionLog.log_date,
            func.count(SupervisionLog.id).label('count')
        ).filter(
            SupervisionLog.log_date >= start_date,
            SupervisionLog.log_date <= end_date
        ).group_by(SupervisionLog.log_date).order_by(SupervisionLog.log_date)
        
        if supervisor_id:
            daily_query = daily_query.filter(SupervisionLog.supervisor_id == supervisor_id)
        
        daily_trend = [
            {'date': row.log_date.isoformat(), 'count': row.count}
            for row in daily_query.all()
        ]
        
        # 计划完成率统计
        plan_stats = db.session.query(
            StudyPlan.phase,
            func.count(StudyPlan.id).label('total'),
            func.avg(
                func.cast(
                    db.session.query(func.count(PlanTask.id)).filter(
                        PlanTask.plan_id == StudyPlan.id,
                        PlanTask.is_completed == True
                    ).correlate(StudyPlan).scalar_subquery() * 100 /
                    func.nullif(
                        db.session.query(func.count(PlanTask.id)).filter(
                            PlanTask.plan_id == StudyPlan.id
                        ).correlate(StudyPlan).scalar_subquery(),
                        0
                    ),
                    db.Float
                )
            ).label('avg_progress')
        ).group_by(StudyPlan.phase)
        
        phase_stats = []
        for row in plan_stats.all():
            phase_map = {'foundation': '基础阶段', 'improvement': '提高阶段', 'sprint': '冲刺阶段'}
            phase_stats.append({
                'phase': row.phase,
                'phase_display': phase_map.get(row.phase, row.phase),
                'total': row.total,
                'avg_progress': round(row.avg_progress or 0, 1),
            })
        
        return {
            'workload': workload_data,
            'mood_stats': mood_stats,
            'status_stats': status_stats,
            'daily_trend': daily_trend,
            'phase_stats': phase_stats,
        }
    
    # ==================== 计划模板功能 ====================
    
    @staticmethod
    def get_plan_templates(is_active=True):
        """获取计划模板列表"""
        query = PlanTemplate.query
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        return query.order_by(PlanTemplate.created_at.desc()).all()
    
    @staticmethod
    def create_plan_template(data, user_id):
        """创建计划模板"""
        template = PlanTemplate(
            name=data.get('name'),
            phase=data.get('phase', 'foundation'),
            duration_days=data.get('duration_days', 30),
            description=data.get('description'),
            goals_template=json.dumps(data.get('goals', []), ensure_ascii=False) if data.get('goals') else None,
            tasks_template=json.dumps(data.get('tasks', []), ensure_ascii=False) if data.get('tasks') else None,
            created_by=user_id,
        )
        db.session.add(template)
        db.session.commit()
        return template
    
    @staticmethod
    def create_plan_from_template(template_id, student_ids, user_id):
        """
        从模板批量创建学习计划
        
        Args:
            template_id: 模板ID
            student_ids: 学员ID列表
            user_id: 创建人ID
        
        Returns:
            创建的计划列表
        """
        template = PlanTemplate.query.get(template_id)
        if not template:
            raise ValueError('模板不存在')
        
        today = date.today()
        end_date = today + timedelta(days=template.duration_days)
        
        created_plans = []
        for student_id in student_ids:
            # 创建计划
            plan = StudyPlan(
                student_id=student_id,
                name=template.name,
                phase=template.phase,
                start_date=today,
                end_date=end_date,
                status='active',
                notes=f'基于模板"{template.name}"创建',
                created_by=user_id,
            )
            db.session.add(plan)
            db.session.flush()  # 获取plan.id
            
            # 创建目标
            for goal_data in template.goals_list:
                goal = PlanGoal(
                    plan_id=plan.id,
                    goal_type=goal_data.get('type', 'accuracy'),
                    module=goal_data.get('module'),
                    description=goal_data.get('description', ''),
                    target_value=goal_data.get('target', 0),
                    unit=goal_data.get('unit', '%'),
                    deadline=end_date,
                )
                db.session.add(goal)
            
            # 创建任务
            for i, task_data in enumerate(template.tasks_list):
                # 计算任务截止日期
                if task_data.get('day_offset'):
                    due_date = today + timedelta(days=task_data['day_offset'])
                else:
                    due_date = today + timedelta(days=(i + 1) * 7)  # 默认每周一个任务
                
                task = PlanTask(
                    plan_id=plan.id,
                    task_type=task_data.get('type', 'weekly'),
                    title=task_data.get('title', ''),
                    description=task_data.get('description'),
                    priority=task_data.get('priority', 3),
                    due_date=due_date,
                )
                db.session.add(task)
            
            created_plans.append(plan)
        
        db.session.commit()
        return created_plans
    
    @staticmethod
    def assign_students_to_supervisor(student_ids, supervisor_id):
        """
        批量分配学员给督学老师
        
        Args:
            student_ids: 学员ID列表
            supervisor_id: 督学老师ID
        
        Returns:
            更新的学员数量
        """
        count = Student.query.filter(Student.id.in_(student_ids)).update(
            {'supervisor_id': supervisor_id},
            synchronize_session=False
        )
        db.session.commit()
        return count
