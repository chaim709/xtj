"""
数据导入服务 - 督学系统
"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app import db
from app.models import (
    User, Student, Teacher, WeaknessTag, ModuleCategory,
    SupervisionLog, HomeworkTask, HomeworkSubmission,
    Subject, Project, Package, ClassType, ClassBatch,
    Schedule, ScheduleChangeLog, StudentBatch, Attendance,
    CourseRecording, StudyPlan, PlanGoal, PlanTask, PlanProgress
)
from app.migrate.utils import parse_datetime, IMPORT_ORDER
from app.migrate.formatters import JsonFormatter, ExcelFormatter
from app.migrate.version import VersionAdapter, CURRENT_VERSION


class ConflictStrategy(Enum):
    SKIP = 'skip'
    OVERWRITE = 'overwrite'
    ERROR = 'error'


@dataclass
class ValidationResult:
    is_valid: bool
    version: str
    modules: List[str]
    total_records: int
    errors: List[str]
    warnings: List[str]


@dataclass
class PreviewResult:
    is_valid: bool
    version: str
    modules: List[str]
    record_counts: Dict[str, int]
    conflict_counts: Dict[str, int]
    total_records: int
    total_conflicts: int


@dataclass
class ImportResult:
    success: bool
    imported_counts: Dict[str, int]
    skipped_counts: Dict[str, int]
    conflict_counts: Dict[str, int]
    total_imported: int
    total_skipped: int
    duration: float
    errors: List[str]
    warnings: List[str]


class ImportService:
    """数据导入服务"""
    
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
    
    UNIQUE_FIELDS = {
        'users': 'username',
        'students': 'phone',
        'teachers': 'phone',
    }
    
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        errors = []
        warnings = []
        
        if not os.path.exists(file_path):
            return ValidationResult(False, '', [], 0, [f'文件不存在: {file_path}'], [])
        
        data = None
        try:
            if file_path.endswith('.json'):
                is_valid, error, data = JsonFormatter.validate_file(file_path)
                if not is_valid:
                    errors.append(error)
                else:
                    data = JsonFormatter.load_from_file(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                is_valid, error, _ = ExcelFormatter.validate_file(file_path)
                if not is_valid:
                    errors.append(error)
                else:
                    data = ExcelFormatter.load_from_file(file_path)
            else:
                errors.append('不支持的文件格式')
        except Exception as e:
            errors.append(f'读取文件失败: {str(e)}')
        
        if errors:
            return ValidationResult(False, '', [], 0, errors, warnings)
        
        is_valid, error = VersionAdapter.validate_data_structure(data)
        if not is_valid:
            return ValidationResult(False, '', [], 0, [error], warnings)
        
        version = VersionAdapter.detect_version(data)
        if not VersionAdapter.is_compatible(version):
            errors.append(f'数据版本{version}不兼容')
        elif version != CURRENT_VERSION:
            warnings.append(f'数据版本{version}将被迁移到{CURRENT_VERSION}')
        
        meta = data.get('meta', {})
        modules = meta.get('modules', list(data.get('data', {}).keys()))
        total_records = meta.get('total_records', sum(len(r) for r in data.get('data', {}).values()))
        
        return ValidationResult(len(errors) == 0, version, modules, total_records, errors, warnings)
    
    @classmethod
    def preview(cls, file_path: str) -> PreviewResult:
        validation = cls.validate(file_path)
        if not validation.is_valid:
            return PreviewResult(False, '', [], {}, {}, 0, 0)
        
        if file_path.endswith('.json'):
            data = JsonFormatter.load_from_file(file_path)
        else:
            data = ExcelFormatter.load_from_file(file_path)
        
        export_data = data.get('data', {})
        record_counts = {}
        conflict_counts = {}
        
        for module_name, records in export_data.items():
            record_counts[module_name] = len(records)
            conflict_counts[module_name] = cls._detect_conflicts(module_name, records)
        
        return PreviewResult(
            True, validation.version, validation.modules,
            record_counts, conflict_counts,
            sum(record_counts.values()), sum(conflict_counts.values())
        )
    
    @classmethod
    def import_data(cls, file_path: str, strategy: ConflictStrategy = ConflictStrategy.SKIP,
                   dry_run: bool = False) -> ImportResult:
        start_time = datetime.now()
        errors = []
        warnings = []
        imported_counts = {}
        skipped_counts = {}
        conflict_counts = {}
        
        try:
            validation = cls.validate(file_path)
            if not validation.is_valid:
                return ImportResult(False, {}, {}, {}, 0, 0, 0, validation.errors, validation.warnings)
            
            warnings.extend(validation.warnings)
            
            if file_path.endswith('.json'):
                data = JsonFormatter.load_from_file(file_path)
            else:
                data = ExcelFormatter.load_from_file(file_path)
            
            version = VersionAdapter.detect_version(data)
            if version != CURRENT_VERSION:
                data = VersionAdapter.migrate_data(data, version, CURRENT_VERSION)
            
            export_data = data.get('data', {})
            id_mapping = {}
            sorted_modules = cls._sort_modules(list(export_data.keys()))
            
            if dry_run:
                for module_name in sorted_modules:
                    records = export_data.get(module_name, [])
                    conflicts = cls._detect_conflicts(module_name, records)
                    imported_counts[module_name] = len(records) - conflicts
                    conflict_counts[module_name] = conflicts
                    skipped_counts[module_name] = conflicts if strategy == ConflictStrategy.SKIP else 0
            else:
                for module_name in sorted_modules:
                    records = export_data.get(module_name, [])
                    if not records:
                        continue
                    
                    imported, skipped, conflicts, module_errors = cls._import_module(
                        module_name, records, strategy, id_mapping
                    )
                    
                    imported_counts[module_name] = imported
                    skipped_counts[module_name] = skipped
                    conflict_counts[module_name] = conflicts
                    errors.extend(module_errors)
                
                if not errors or strategy != ConflictStrategy.ERROR:
                    db.session.commit()
                else:
                    db.session.rollback()
                    return ImportResult(False, imported_counts, skipped_counts, conflict_counts,
                                      0, sum(skipped_counts.values()),
                                      (datetime.now() - start_time).total_seconds(), errors, warnings)
            
            return ImportResult(
                True, imported_counts, skipped_counts, conflict_counts,
                sum(imported_counts.values()), sum(skipped_counts.values()),
                (datetime.now() - start_time).total_seconds(), errors, warnings
            )
            
        except Exception as e:
            db.session.rollback()
            return ImportResult(False, imported_counts, skipped_counts, conflict_counts,
                              0, 0, (datetime.now() - start_time).total_seconds(),
                              [f'导入失败: {str(e)}'], warnings)
    
    @classmethod
    def _detect_conflicts(cls, module_name: str, records: List[Dict]) -> int:
        model = cls.MODELS.get(module_name)
        unique_field = cls.UNIQUE_FIELDS.get(module_name)
        if model is None or unique_field is None:
            return 0
        
        conflicts = 0
        for record in records:
            unique_value = record.get(unique_field)
            if unique_value:
                existing = model.query.filter(getattr(model, unique_field) == unique_value).first()
                if existing:
                    conflicts += 1
        return conflicts
    
    @classmethod
    def _import_module(cls, module_name: str, records: List[Dict],
                      strategy: ConflictStrategy, id_mapping: Dict) -> tuple:
        model = cls.MODELS.get(module_name)
        if model is None:
            return 0, 0, 0, [f'未知模块: {module_name}']
        
        unique_field = cls.UNIQUE_FIELDS.get(module_name)
        imported = 0
        skipped = 0
        conflicts = 0
        errors = []
        
        if module_name not in id_mapping:
            id_mapping[module_name] = {}
        
        for record in records:
            try:
                old_id = record.get('id')
                existing = None
                
                if unique_field and record.get(unique_field):
                    existing = model.query.filter(
                        getattr(model, unique_field) == record.get(unique_field)
                    ).first()
                
                if existing:
                    conflicts += 1
                    if strategy == ConflictStrategy.SKIP:
                        skipped += 1
                        if old_id:
                            id_mapping[module_name][old_id] = existing.id
                        continue
                    elif strategy == ConflictStrategy.ERROR:
                        errors.append(f'{module_name}: 冲突 {unique_field}={record.get(unique_field)}')
                        continue
                    elif strategy == ConflictStrategy.OVERWRITE:
                        cls._update_record(existing, record, module_name, id_mapping)
                        if old_id:
                            id_mapping[module_name][old_id] = existing.id
                        imported += 1
                        continue
                
                new_record = cls._create_record(model, record, module_name, id_mapping)
                db.session.add(new_record)
                db.session.flush()
                
                if old_id:
                    id_mapping[module_name][old_id] = new_record.id
                
                imported += 1
                
            except Exception as e:
                errors.append(f'{module_name}: 导入失败 - {str(e)}')
        
        return imported, skipped, conflicts, errors
    
    @classmethod
    def _create_record(cls, model, record: Dict, module_name: str, id_mapping: Dict):
        processed = cls._process_record(record, module_name, id_mapping)
        processed.pop('id', None)
        
        for key, value in processed.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    processed[key] = parse_datetime(value)
                except:
                    pass
        
        return model(**processed)
    
    @classmethod
    def _update_record(cls, existing, record: Dict, module_name: str, id_mapping: Dict):
        processed = cls._process_record(record, module_name, id_mapping)
        processed.pop('id', None)
        processed.pop('created_at', None)
        
        for key, value in processed.items():
            if hasattr(existing, key):
                if isinstance(value, str) and 'T' in value:
                    try:
                        value = parse_datetime(value)
                    except:
                        pass
                setattr(existing, key, value)
    
    @classmethod
    def _process_record(cls, record: Dict, module_name: str, id_mapping: Dict) -> Dict:
        processed = record.copy()
        
        fk_mappings = {
            'user_id': 'users',
            'student_id': 'students',
            'teacher_id': 'teachers',
            'batch_id': 'class_batches',
            'task_id': 'homework_tasks',
            'plan_id': 'study_plans',
            'project_id': 'projects',
            'package_id': 'packages',
            'class_type_id': 'class_types',
            'subject_id': 'subjects',
        }
        
        for fk_field, ref_module in fk_mappings.items():
            if fk_field in processed and processed[fk_field] is not None:
                old_fk = processed[fk_field]
                if ref_module in id_mapping and old_fk in id_mapping[ref_module]:
                    processed[fk_field] = id_mapping[ref_module][old_fk]
        
        return processed
    
    @classmethod
    def _sort_modules(cls, modules: List[str]) -> List[str]:
        result = [m for m in IMPORT_ORDER if m in modules]
        for m in modules:
            if m not in result:
                result.append(m)
        return result
