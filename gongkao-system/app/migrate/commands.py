"""
数据迁移 CLI 命令 - 督学系统
"""
import click
from datetime import datetime
from flask.cli import AppGroup

from app.migrate.exporter import ExportService
from app.migrate.importer import ImportService, ConflictStrategy
from app.migrate.utils import MODULE_NAMES


migrate_cli = AppGroup('migrate', help='数据迁移工具')


@migrate_cli.command('export')
@click.option('--format', 'format_type', type=click.Choice(['json', 'excel']), 
              default='json', help='导出格式')
@click.option('--output', '-o', type=click.Path(), default=None, help='输出文件路径')
@click.option('--modules', '-m', type=str, default=None, help='导出模块，逗号分隔')
@click.option('--since', type=str, default=None, help='增量导出起始时间')
def export_command(format_type, output, modules, since):
    """导出数据"""
    click.echo('\n📦 开始导出数据...\n')
    
    module_list = [m.strip() for m in modules.split(',')] if modules else None
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            click.echo(click.style(f'❌ 时间格式错误: {since}', fg='red'))
            return
    
    if since_dt:
        result = ExportService.export_incremental(since_dt, format_type, output)
    elif module_list:
        result = ExportService.export_modules(module_list, format_type, output)
    else:
        result = ExportService.export_full(format_type, output)
    
    click.echo('=' * 50)
    
    if result.success:
        click.echo(click.style('\n✅ 导出成功!', fg='green', bold=True))
        click.echo(f'\n📁 文件: {result.file_path}')
        click.echo(f'⏱️  用时: {result.duration:.2f} 秒')
        click.echo(f'📊 总记录: {result.total_records}')
        for module_name, count in result.record_counts.items():
            click.echo(f'   - {MODULE_NAMES.get(module_name, module_name)}: {count}')
    else:
        click.echo(click.style('\n❌ 导出失败!', fg='red', bold=True))
        click.echo(f'错误: {result.error}')
    click.echo()


@migrate_cli.command('import')
@click.argument('file', type=click.Path(exists=True))
@click.option('--conflict', type=click.Choice(['skip', 'overwrite', 'error']), default='skip')
@click.option('--dry-run', is_flag=True, help='预览模式')
def import_command(file, conflict, dry_run):
    """导入数据"""
    click.echo('\n📥 开始导入数据...\n')
    click.echo(f'📁 文件: {file}')
    
    validation = ImportService.validate(file)
    if not validation.is_valid:
        click.echo(click.style('\n❌ 文件验证失败!', fg='red'))
        for error in validation.errors:
            click.echo(f'   - {error}')
        return
    
    click.echo(click.style('   ✓ 文件格式正确', fg='green'))
    
    preview = ImportService.preview(file)
    click.echo(f'\n待导入: {preview.total_records} 条, 冲突: {preview.total_conflicts} 条')
    
    if not dry_run and not click.confirm('确认导入?'):
        click.echo('已取消')
        return
    
    result = ImportService.import_data(file, ConflictStrategy(conflict), dry_run)
    
    click.echo('=' * 50)
    
    if result.success:
        click.echo(click.style('\n✅ 导入成功!', fg='green', bold=True))
        click.echo(f'导入: {result.total_imported}, 跳过: {result.total_skipped}')
    else:
        click.echo(click.style('\n❌ 导入失败!', fg='red'))
        for error in result.errors:
            click.echo(f'   - {error}')
    click.echo()


@migrate_cli.command('status')
def status_command():
    """查看数据库状态"""
    click.echo('\n📊 数据库状态\n')
    stats = ExportService.get_export_stats_detail()
    click.echo('-' * 40)
    for module in stats['modules']:
        click.echo(f"  {module['display_name']:15} {module['count']:>8} 条")
    click.echo('-' * 40)
    click.echo(f"  {'总计':15} {stats['total_records']:>8} 条")
    click.echo()


@migrate_cli.command('help')
def help_command():
    """显示帮助"""
    click.echo('''
📦 督学系统数据迁移工具
========================

导出: flask migrate export [--format json|excel] [-o 文件路径]
导入: flask migrate import 文件路径 [--conflict skip|overwrite|error]
状态: flask migrate status
''')


def init_app(app):
    """注册CLI命令"""
    app.cli.add_command(migrate_cli)
