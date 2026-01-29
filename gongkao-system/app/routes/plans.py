"""
学习计划路由
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.plan_service import PlanService
from app.models.student import Student

plans_bp = Blueprint('plans', __name__)


# ==================== 计划管理 ====================

@plans_bp.route('/students/<int:student_id>/plans')
@login_required
def list_by_student(student_id):
    """学员的学习计划列表"""
    student = Student.query.get_or_404(student_id)
    plans = PlanService.get_plans_by_student(student_id)
    active_plan = PlanService.get_active_plan(student_id)
    
    return render_template('plans/list.html',
                         student=student,
                         plans=plans,
                         active_plan=active_plan)


@plans_bp.route('/students/<int:student_id>/plans/create', methods=['GET', 'POST'])
@login_required
def create(student_id):
    """创建学习计划"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        phase = request.form.get('phase', 'foundation')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        notes = request.form.get('notes')
        
        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        # 创建计划
        plan = PlanService.create_plan(
            student_id=student_id,
            name=name,
            phase=phase,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            created_by=current_user.id
        )
        
        # 处理AI建议采纳
        if request.form.get('adopt_goals'):
            goals_data = request.form.getlist('goal_description[]')
            goals_type = request.form.getlist('goal_type[]')
            goals_target = request.form.getlist('goal_target[]')
            goals_unit = request.form.getlist('goal_unit[]')
            goals_module = request.form.getlist('goal_module[]')
            
            for i in range(len(goals_data)):
                if goals_data[i]:
                    PlanService.create_goal(
                        plan_id=plan.id,
                        goal_type=goals_type[i] if i < len(goals_type) else 'accuracy',
                        description=goals_data[i],
                        target_value=float(goals_target[i]) if i < len(goals_target) and goals_target[i] else 0,
                        unit=goals_unit[i] if i < len(goals_unit) else '%',
                        module=goals_module[i] if i < len(goals_module) else None
                    )
        
        if request.form.get('adopt_tasks'):
            tasks_title = request.form.getlist('task_title[]')
            tasks_type = request.form.getlist('task_type[]')
            
            for i in range(len(tasks_title)):
                if tasks_title[i]:
                    PlanService.create_task(
                        plan_id=plan.id,
                        task_type=tasks_type[i] if i < len(tasks_type) else 'daily',
                        title=tasks_title[i]
                    )
        
        flash('学习计划创建成功！', 'success')
        return redirect(url_for('plans.detail', plan_id=plan.id))
    
    # GET请求
    ai_suggestion = None
    if request.args.get('generate_ai') == '1':
        ai_suggestion = PlanService.generate_ai_suggestion(student_id)
    
    return render_template('plans/form.html',
                         student=student,
                         plan=None,
                         ai_suggestion=ai_suggestion)


@plans_bp.route('/plans/<int:plan_id>')
@login_required
def detail(plan_id):
    """计划详情"""
    plan = PlanService.get_plan_by_id(plan_id)
    if not plan:
        flash('计划不存在', 'error')
        return redirect(url_for('dashboard.index'))
    
    goals = PlanService.get_goals_by_plan(plan_id)
    tasks = PlanService.get_tasks_by_plan(plan_id)
    progress_records = PlanService.get_progress_by_plan(plan_id)
    
    return render_template('plans/detail.html',
                         plan=plan,
                         goals=goals,
                         tasks=tasks,
                         progress_records=progress_records)


@plans_bp.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(plan_id):
    """编辑计划"""
    plan = PlanService.get_plan_by_id(plan_id)
    if not plan:
        flash('计划不存在', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        phase = request.form.get('phase')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        notes = request.form.get('notes')
        status = request.form.get('status')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else plan.start_date
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        PlanService.update_plan(
            plan_id=plan_id,
            name=name,
            phase=phase,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            status=status
        )
        
        flash('计划更新成功！', 'success')
        return redirect(url_for('plans.detail', plan_id=plan_id))
    
    return render_template('plans/form.html',
                         student=plan.student,
                         plan=plan,
                         ai_suggestion=None)


@plans_bp.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete(plan_id):
    """删除计划"""
    plan = PlanService.get_plan_by_id(plan_id)
    if not plan:
        flash('计划不存在', 'error')
        return redirect(url_for('dashboard.index'))
    
    student_id = plan.student_id
    PlanService.delete_plan(plan_id)
    
    flash('计划已删除', 'success')
    return redirect(url_for('students.detail', id=student_id))


@plans_bp.route('/plans/<int:plan_id>/complete', methods=['POST'])
@login_required
def complete(plan_id):
    """完成计划"""
    PlanService.complete_plan(plan_id)
    flash('计划已标记为完成', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


@plans_bp.route('/plans/<int:plan_id>/pause', methods=['POST'])
@login_required
def pause(plan_id):
    """暂停计划"""
    PlanService.pause_plan(plan_id)
    flash('计划已暂停', 'info')
    return redirect(url_for('plans.detail', plan_id=plan_id))


@plans_bp.route('/plans/<int:plan_id>/resume', methods=['POST'])
@login_required
def resume(plan_id):
    """恢复计划"""
    PlanService.resume_plan(plan_id)
    flash('计划已恢复', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


# ==================== 目标管理 ====================

@plans_bp.route('/plans/<int:plan_id>/goals', methods=['POST'])
@login_required
def add_goal(plan_id):
    """添加目标"""
    goal_type = request.form.get('goal_type', 'accuracy')
    module = request.form.get('module')
    description = request.form.get('description')
    target_value = float(request.form.get('target_value', 0))
    unit = request.form.get('unit', '%')
    deadline_str = request.form.get('deadline')
    
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
    
    PlanService.create_goal(
        plan_id=plan_id,
        goal_type=goal_type,
        module=module,
        description=description,
        target_value=target_value,
        unit=unit,
        deadline=deadline
    )
    
    flash('目标添加成功', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


@plans_bp.route('/goals/<int:goal_id>/update', methods=['POST'])
@login_required
def update_goal(goal_id):
    """更新目标进度"""
    goal = PlanService.get_goal_by_id(goal_id)
    if not goal:
        return jsonify({'success': False, 'message': '目标不存在'})
    
    current_value = float(request.form.get('current_value', 0))
    PlanService.update_goal_progress(goal_id, current_value)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': '进度已更新'})
    
    flash('目标进度已更新', 'success')
    return redirect(url_for('plans.detail', plan_id=goal.plan_id))


@plans_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    """删除目标"""
    goal = PlanService.get_goal_by_id(goal_id)
    if not goal:
        flash('目标不存在', 'error')
        return redirect(url_for('dashboard.index'))
    
    plan_id = goal.plan_id
    PlanService.delete_goal(goal_id)
    
    flash('目标已删除', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


# ==================== 任务管理 ====================

@plans_bp.route('/plans/<int:plan_id>/tasks', methods=['POST'])
@login_required
def add_task(plan_id):
    """添加任务"""
    task_type = request.form.get('task_type', 'daily')
    title = request.form.get('title')
    description = request.form.get('description')
    priority = int(request.form.get('priority', 3))
    due_date_str = request.form.get('due_date')
    
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
    
    PlanService.create_task(
        plan_id=plan_id,
        task_type=task_type,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date
    )
    
    flash('任务添加成功', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


@plans_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """完成任务"""
    task = PlanService.get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    PlanService.complete_task(task_id, completed_by=current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': '任务已完成'})
    
    flash('任务已完成', 'success')
    return redirect(url_for('plans.detail', plan_id=task.plan_id))


@plans_bp.route('/tasks/<int:task_id>/uncomplete', methods=['POST'])
@login_required
def uncomplete_task(task_id):
    """取消完成任务"""
    task = PlanService.get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    PlanService.uncomplete_task(task_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': '任务已恢复'})
    
    flash('任务已恢复为未完成', 'info')
    return redirect(url_for('plans.detail', plan_id=task.plan_id))


@plans_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """删除任务"""
    task = PlanService.get_task_by_id(task_id)
    if not task:
        flash('任务不存在', 'error')
        return redirect(url_for('dashboard.index'))
    
    plan_id = task.plan_id
    PlanService.delete_task(task_id)
    
    flash('任务已删除', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


# ==================== 进度记录 ====================

@plans_bp.route('/plans/<int:plan_id>/progress', methods=['POST'])
@login_required
def add_progress(plan_id):
    """添加进度记录"""
    record_date_str = request.form.get('record_date')
    record_type = request.form.get('record_type', 'evaluation')
    content = request.form.get('content')
    overall_score = request.form.get('overall_score')
    
    record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date() if record_date_str else date.today()
    overall_score = int(overall_score) if overall_score else None
    
    PlanService.create_progress(
        plan_id=plan_id,
        record_date=record_date,
        record_type=record_type,
        content=content,
        overall_score=overall_score,
        created_by=current_user.id
    )
    
    flash('进度记录已添加', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


@plans_bp.route('/progress/<int:progress_id>/delete', methods=['POST'])
@login_required
def delete_progress(progress_id):
    """删除进度记录"""
    from app.models.study_plan import PlanProgress
    progress = PlanProgress.query.get(progress_id)
    if not progress:
        flash('记录不存在', 'error')
        return redirect(url_for('dashboard.index'))
    
    plan_id = progress.plan_id
    PlanService.delete_progress(progress_id)
    
    flash('记录已删除', 'success')
    return redirect(url_for('plans.detail', plan_id=plan_id))


# ==================== AI建议 ====================

@plans_bp.route('/students/<int:student_id>/plans/ai-suggest')
@login_required
def ai_suggest(student_id):
    """获取AI建议"""
    suggestion = PlanService.generate_ai_suggestion(student_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(suggestion)
    
    # 重定向到创建页面并带上AI建议
    return redirect(url_for('plans.create', student_id=student_id, generate_ai=1))
