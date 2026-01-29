"""
数据导出服务 - 督学系统
"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app import db
from app.models import (
    User, Student, Teacher, WeaknessTag, ModuleCategory,
    SupervisionLog, HomeworkTask, HomeworkSubmission,
    Subject, Project, Package, ClassType, ClassBatch,
    Schedule, ScheduleChangeLog, StudentBatch, Attendance,
    CourseRecording, StudyPlan, PlanGoal, PlanTask, PlanProgress
)
from app.migrate.utils import (
    model_to_dict, calculate_checksum, get_backup_dir,
    generate_backup_filename, IMPORT_ORDER, MODULE_NAMES
)
from app.migrate.formatters import JsonFormatter, ExcelFormatter
from app.migrate.version import CURRENT_VERSION


@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    file_path: str
    export_type: str
    format_type: str
    modules: List[str]
    total_records: int
    record_counts: Dict[str, int]
    duration: float
    error: Optional[str] = None


class ExportService:
    """数据导出服务"""
    
    MODELS = {
        'users': User,
        'teachers': Teacher,
        'subjects': Subject,
        'projects': Project,
        'packages': Package,
        'class_types': ClassType,
        'class_batches': ClassBatch,
        'schedules': Schedule,
        'schedule_change_logs': ScheduleChangeLog,
        'course_recordings': CourseRecording,
        'weakness_tags': WeaknessTag,
        'module_categories': ModuleCategory,
        'students': Student,
        'student_batches': StudentBatch,
        'supervision_logs': SupervisionLog,
        'homework_tasks': HomeworkTask,
        'homework_submissions': HomeworkSubmission,
        'attendances': Attendance,
        'study_plans': StudyPlan,
        'plan_goals': PlanGoal,
        'plan_tasks': PlanTask,
        'plan_progresses': PlanProgress,
    }
    
    EXCLUDE_FIELDS = {
        'users': ['password_hash'],
    }
    
    @classmethod
    def export_full(cls, format_type: str = 'json', output_path: str = None) -> ExportResult:
        return cls._export(
            export_type='full',
            format_type=format_type,
            output_path=output_path,
            modules=None,
            since=None
        )
    
    @classmethod
    def export_incremental(cls, since: datetime, format_type: str = 'json', 
                          output_path: str = None) -> ExportResult:
        return cls._export(
            export_type='incremental',
            format_type=format_type,
            output_path=output_path,
            modules=None,
            since=since
        )
    
    @classmethod
    def export_modules(cls, modules: List[str], format_type: str = 'json',
                      output_path: str = None) -> ExportResult:
        valid_modules = [m for m in modules if m in cls.MODELS]
        if not valid_modules:
            return ExportResult(
                success=False, file_path='', export_type='module',
                format_type=format_type, modules=[], total_records=0,
                record_counts={}, duration=0,
                error=f'无效的模块名称。有效模块: {", ".join(cls.MODELS.keys())}'
            )
        expanded_modules = cls._expand_dependencies(valid_modules)
        return cls._export(
            export_type='module',
            format_type=format_type,
            output_path=output_path,
            modules=expanded_modules,
            since=None
        )
    
    @classmethod
    def _export(cls, export_type: str, format_type: str, output_path: str,
               modules: Optional[List[str]], since: Optional[datetime]) -> ExportResult:
        start_time = datetime.now()
        
        try:
            if output_path is None:
                backup_dir = get_backup_dir()
                filename = generate_backup_filename(format_type, export_type)
                output_path = os.path.join(backup_dir, filename)
            
            if modules is None:
                modules = list(cls.MODELS.keys())
            
            modules = cls._sort_by_dependency(modules)
            
            data = {}
            record_counts = {}
            total_records = 0
            
            for module_name in modules:
                records = cls._export_module(module_name, since)
                data[module_name] = records
                record_counts[module_name] = len(records)
                total_records += len(records)
            
            export_data = {
                'meta': {
                    'version': CURRENT_VERSION,
                    'system': 'gongkao-duxue-system',
                    'export_time': datetime.now().isoformat(),
                    'export_type': export_type,
                    'modules': modules,
                    'incremental_since': since.isoformat() if since else None,
                    'total_records': total_records,
                },
                'data': data,
            }
            
            export_data['meta']['checksum'] = calculate_checksum(data)
            
            if format_type == 'json':
                JsonFormatter.save_to_file(export_data, output_path)
            elif format_type == 'excel':
                ExcelFormatter.save_to_file(export_data, output_path)
            else:
                raise ValueError(f'不支持的格式类型: {format_type}')
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return ExportResult(
                success=True, file_path=output_path, export_type=export_type,
                format_type=format_type, modules=modules, total_records=total_records,
                record_counts=record_counts, duration=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return ExportResult(
                success=False, file_path=output_path or '', export_type=export_type,
                format_type=format_type, modules=modules or [], total_records=0,
                record_counts={}, duration=duration, error=str(e)
            )
    
    @classmethod
    def _export_module(cls, module_name: str, since: Optional[datetime]) -> List[Dict]:
        model = cls.MODELS.get(module_name)
        if model is None:
            return []
        
        exclude_fields = cls.EXCLUDE_FIELDS.get(module_name, [])
        query = model.query
        
        if since is not None:
            if hasattr(model, 'updated_at'):
                query = query.filter(model.updated_at >= since)
            elif hasattr(model, 'created_at'):
                query = query.filter(model.created_at >= since)
        
        records = query.all()
        return [model_to_dict(record, exclude_fields) for record in records]
    
    @classmethod
    def _expand_dependencies(cls, modules: List[str]) -> List[str]:
        dependencies = {
            'students': ['users'],
            'teachers': ['users'],
            'class_batches': ['class_types', 'projects', 'packages'],
            'schedules': ['class_batches', 'teachers', 'subjects'],
            'student_batches': ['students', 'class_batches'],
            'supervision_logs': ['students', 'users'],
            'homework_tasks': ['class_batches'],
            'homework_submissions': ['homework_tasks', 'students'],
            'attendances': ['students', 'class_batches'],
            'study_plans': ['students'],
            'plan_goals': ['study_plans'],
            'plan_tasks': ['study_plans'],
            'plan_progresses': ['study_plans'],
        }
        
        expanded = set(modules)
        changed = True
        while changed:
            changed = False
            for module in list(expanded):
                for dep in dependencies.get(module, []):
                    if dep not in expanded:
                        expanded.add(dep)
                        changed = True
        return list(expanded)
    
    @classmethod
    def _sort_by_dependency(cls, modules: List[str]) -> List[str]:
        result = [m for m in IMPORT_ORDER if m in modules]
        for m in modules:
            if m not in result:
                result.append(m)
        return result
    
    @classmethod
    def get_export_stats(cls) -> Dict[str, int]:
        stats = {}
        for module_name, model in cls.MODELS.items():
            try:
                stats[module_name] = model.query.count()
            except Exception:
                stats[module_name] = 0
        return stats
    
    @classmethod
    def get_export_stats_detail(cls) -> Dict[str, Any]:
        stats = cls.get_export_stats()
        return {
            'modules': [
                {'name': name, 'display_name': MODULE_NAMES.get(name, name), 'count': count}
                for name, count in stats.items()
            ],
            'total_records': sum(stats.values()),
            'available_formats': ['json', 'excel'],
            'export_types': ['full', 'incremental', 'module'],
        }
