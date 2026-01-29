"""
学习计划服务层
"""
from datetime import datetime, date
from app import db
from app.models.study_plan import StudyPlan, PlanGoal, PlanTask, PlanProgress
from app.models.student import Student
from app.models.tag import WeaknessTag


class PlanService:
    """学习计划服务"""
    
    # ==================== 计划管理 ====================
    
    @staticmethod
    def get_plans_by_student(student_id):
        """获取学员的所有计划"""
        return StudyPlan.query.filter_by(student_id=student_id)\
            .order_by(StudyPlan.created_at.desc()).all()
    
    @staticmethod
    def get_active_plan(student_id):
        """获取学员当前进行中的计划"""
        return StudyPlan.query.filter_by(
            student_id=student_id,
            status='active'
        ).first()
    
    @staticmethod
    def get_plan_by_id(plan_id):
        """根据ID获取计划"""
        return StudyPlan.query.get(plan_id)
    
    @staticmethod
    def create_plan(student_id, name, phase, start_date, end_date=None, notes=None, created_by=None):
        """创建学习计划"""
        plan = StudyPlan(
            student_id=student_id,
            name=name,
            phase=phase,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            created_by=created_by,
            status='active'
        )
        db.session.add(plan)
        db.session.commit()
        return plan
    
    @staticmethod
    def update_plan(plan_id, **kwargs):
        """更新计划"""
        plan = StudyPlan.query.get(plan_id)
        if not plan:
            return None
        
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        db.session.commit()
        return plan
    
    @staticmethod
    def delete_plan(plan_id):
        """删除计划"""
        plan = StudyPlan.query.get(plan_id)
        if plan:
            db.session.delete(plan)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def complete_plan(plan_id):
        """完成计划"""
        plan = StudyPlan.query.get(plan_id)
        if plan:
            plan.status = 'completed'
            db.session.commit()
            return plan
        return None
    
    @staticmethod
    def pause_plan(plan_id):
        """暂停计划"""
        plan = StudyPlan.query.get(plan_id)
        if plan:
            plan.status = 'paused'
            db.session.commit()
            return plan
        return None
    
    @staticmethod
    def resume_plan(plan_id):
        """恢复计划"""
        plan = StudyPlan.query.get(plan_id)
        if plan:
            plan.status = 'active'
            db.session.commit()
            return plan
        return None
    
    # ==================== 目标管理 ====================
    
    @staticmethod
    def get_goals_by_plan(plan_id):
        """获取计划的所有目标"""
        return PlanGoal.query.filter_by(plan_id=plan_id)\
            .order_by(PlanGoal.deadline).all()
    
    @staticmethod
    def get_goal_by_id(goal_id):
        """根据ID获取目标"""
        return PlanGoal.query.get(goal_id)
    
    @staticmethod
    def create_goal(plan_id, goal_type, description, target_value, unit='%', module=None, deadline=None):
        """创建阶段目标"""
        goal = PlanGoal(
            plan_id=plan_id,
            goal_type=goal_type,
            module=module,
            description=description,
            target_value=target_value,
            unit=unit,
            deadline=deadline,
            current_value=0,
            status='pending'
        )
        db.session.add(goal)
        db.session.commit()
        return goal
    
    @staticmethod
    def update_goal(goal_id, **kwargs):
        """更新目标"""
        goal = PlanGoal.query.get(goal_id)
        if not goal:
            return None
        
        for key, value in kwargs.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        
        # 检查是否达成目标
        if goal.current_value >= goal.target_value and goal.status == 'pending':
            goal.status = 'achieved'
            goal.achieved_at = datetime.utcnow()
        
        db.session.commit()
        return goal
    
    @staticmethod
    def update_goal_progress(goal_id, current_value):
        """更新目标进度"""
        goal = PlanGoal.query.get(goal_id)
        if not goal:
            return None
        
        goal.current_value = current_value
        
        # 检查是否达成目标
        if current_value >= goal.target_value and goal.status == 'pending':
            goal.status = 'achieved'
            goal.achieved_at = datetime.utcnow()
        
        db.session.commit()
        return goal
    
    @staticmethod
    def delete_goal(goal_id):
        """删除目标"""
        goal = PlanGoal.query.get(goal_id)
        if goal:
            db.session.delete(goal)
            db.session.commit()
            return True
        return False
    
    # ==================== 任务管理 ====================
    
    @staticmethod
    def get_tasks_by_plan(plan_id, include_completed=True):
        """获取计划的所有任务"""
        query = PlanTask.query.filter_by(plan_id=plan_id)
        if not include_completed:
            query = query.filter_by(is_completed=False)
        return query.order_by(PlanTask.due_date, PlanTask.priority.desc()).all()
    
    @staticmethod
    def get_pending_tasks(plan_id):
        """获取未完成的任务"""
        return PlanTask.query.filter_by(
            plan_id=plan_id,
            is_completed=False
        ).order_by(PlanTask.due_date, PlanTask.priority.desc()).all()
    
    @staticmethod
    def get_task_by_id(task_id):
        """根据ID获取任务"""
        return PlanTask.query.get(task_id)
    
    @staticmethod
    def create_task(plan_id, task_type, title, description=None, priority=3, due_date=None):
        """创建任务"""
        task = PlanTask(
            plan_id=plan_id,
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            is_completed=False
        )
        db.session.add(task)
        db.session.commit()
        return task
    
    @staticmethod
    def update_task(task_id, **kwargs):
        """更新任务"""
        task = PlanTask.query.get(task_id)
        if not task:
            return None
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        db.session.commit()
        return task
    
    @staticmethod
    def complete_task(task_id, completed_by=None):
        """完成任务"""
        task = PlanTask.query.get(task_id)
        if not task:
            return None
        
        task.is_completed = True
        task.completed_at = datetime.utcnow()
        task.completed_by = completed_by
        
        db.session.commit()
        return task
    
    @staticmethod
    def uncomplete_task(task_id):
        """取消完成任务"""
        task = PlanTask.query.get(task_id)
        if not task:
            return None
        
        task.is_completed = False
        task.completed_at = None
        task.completed_by = None
        
        db.session.commit()
        return task
    
    @staticmethod
    def delete_task(task_id):
        """删除任务"""
        task = PlanTask.query.get(task_id)
        if task:
            db.session.delete(task)
            db.session.commit()
            return True
        return False
    
    # ==================== 进度记录 ====================
    
    @staticmethod
    def get_progress_by_plan(plan_id):
        """获取计划的进度记录"""
        return PlanProgress.query.filter_by(plan_id=plan_id)\
            .order_by(PlanProgress.record_date.desc()).all()
    
    @staticmethod
    def create_progress(plan_id, record_date, content, record_type='evaluation', overall_score=None, created_by=None):
        """创建进度记录"""
        progress = PlanProgress(
            plan_id=plan_id,
            record_date=record_date,
            record_type=record_type,
            content=content,
            overall_score=overall_score,
            created_by=created_by
        )
        db.session.add(progress)
        db.session.commit()
        return progress
    
    @staticmethod
    def delete_progress(progress_id):
        """删除进度记录"""
        progress = PlanProgress.query.get(progress_id)
        if progress:
            db.session.delete(progress)
            db.session.commit()
            return True
        return False
    
    # ==================== AI建议生成 ====================
    
    @staticmethod
    def get_student_context(student_id):
        """获取学员上下文数据，用于AI生成建议"""
        student = Student.query.get(student_id)
        if not student:
            return None
        
        # 获取薄弱项标签
        weakness_tags = WeaknessTag.query.filter_by(student_id=student_id).all()
        
        # 计算距考试天数
        days_until_exam = None
        if student.exam_date:
            delta = student.exam_date - date.today()
            days_until_exam = delta.days if delta.days > 0 else 0
        
        # 获取作业统计（简化版）
        homework_stats = {
            'avg_accuracy': 0,
            'completion_rate': 0,
            'recent_trend': 'stable'
        }
        
        # 如果有作业提交记录，计算统计
        from app.models.homework import HomeworkSubmission
        submissions = HomeworkSubmission.query.filter_by(student_id=student_id).all()
        if submissions:
            scores = [s.score for s in submissions if s.score is not None]
            if scores:
                homework_stats['avg_accuracy'] = round(sum(scores) / len(scores))
            total_tasks = len(set(s.task_id for s in submissions))
            if total_tasks > 0:
                homework_stats['completion_rate'] = round(len(submissions) / total_tasks * 100)
        
        return {
            'student': {
                'id': student.id,
                'name': student.name,
                'exam_type': student.exam_type,
                'exam_date': student.exam_date.isoformat() if student.exam_date else None,
                'has_basic': student.has_basic,
                'base_level': student.base_level,
                'learning_style': student.learning_style
            },
            'weakness_tags': [
                {'module': tag.module, 'accuracy': tag.accuracy_rate}
                for tag in weakness_tags
            ],
            'homework_stats': homework_stats,
            'days_until_exam': days_until_exam
        }
    
    @staticmethod
    def generate_ai_suggestion(student_id):
        """
        生成AI建议（本地规则版本）
        
        后续可以接入大模型API来生成更智能的建议
        """
        context = PlanService.get_student_context(student_id)
        if not context:
            return None
        
        # 分析薄弱项
        weakness_tags = context.get('weakness_tags', [])
        weak_modules = [t for t in weakness_tags if t.get('accuracy', 100) < 70]
        weak_modules.sort(key=lambda x: x.get('accuracy', 100))
        
        # 确定学习阶段建议
        days = context.get('days_until_exam')
        if days is None:
            phase_suggestion = 'improvement'
        elif days <= 30:
            phase_suggestion = 'sprint'
        elif days <= 60:
            phase_suggestion = 'improvement'
        else:
            phase_suggestion = 'foundation'
        
        phase_map = {
            'foundation': '基础阶段',
            'improvement': '提高阶段',
            'sprint': '冲刺阶段'
        }
        
        # 生成目标建议
        recommended_goals = []
        focus_modules = []
        
        for tag in weak_modules[:3]:  # 最多关注3个薄弱模块
            module = tag.get('module', '')
            current = tag.get('accuracy', 0)
            target = min(current + 20, 85)  # 目标提升20%，最高85%
            
            focus_modules.append(module)
            recommended_goals.append({
                'type': 'accuracy',
                'module': module,
                'target': target,
                'unit': '%',
                'description': f'{module}正确率达到{target}%'
            })
        
        # 添加真题数量目标
        if days and days <= 60:
            recommended_goals.append({
                'type': 'quantity',
                'module': '真题',
                'target': 10 if days > 30 else 5,
                'unit': '套',
                'description': f'完成{10 if days > 30 else 5}套真题'
            })
        
        # 生成任务建议
        recommended_tasks = []
        
        for module in focus_modules[:2]:
            recommended_tasks.append({
                'type': 'daily',
                'title': f'{module}专项练习30道',
                'priority': 4
            })
        
        recommended_tasks.append({
            'type': 'weekly',
            'title': '完成一套真题计时模拟',
            'priority': 5
        })
        
        if days and days > 15:
            recommended_tasks.append({
                'type': 'milestone',
                'title': '第一次全真模考',
                'priority': 5,
                'days_from_now': min(15, days // 2)
            })
        
        # 生成备注
        notes_parts = []
        if focus_modules:
            notes_parts.append(f"重点突破模块：{'、'.join(focus_modules)}")
        if days:
            notes_parts.append(f"距考试{days}天")
        if context['student'].get('has_basic'):
            notes_parts.append("学员有一定基础，可适当加大练习强度")
        else:
            notes_parts.append("学员基础薄弱，注意循序渐进")
        
        return {
            'phase_suggestion': phase_suggestion,
            'phase_display': phase_map.get(phase_suggestion, phase_suggestion),
            'focus_modules': focus_modules,
            'recommended_goals': recommended_goals,
            'recommended_tasks': recommended_tasks,
            'notes': '；'.join(notes_parts) + '。',
            'context': context
        }
