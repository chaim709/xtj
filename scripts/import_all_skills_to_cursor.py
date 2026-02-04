#!/usr/bin/env python3
"""
将电脑上所有的 skill 统一导入到 Cursor 中
"""

import os
import json
from pathlib import Path
from collections import defaultdict

# 定义技能源目录
SKILL_SOURCES = [
    Path.home() / ".codex/skills",
    Path.home() / ".agents/skills",
    Path.home() / "Clawdbot/unified-skills",
]

# Cursor 技能目标目录
CURSOR_SKILLS_DIR = Path.home() / ".cursor/skills-cursor"

def find_all_skills():
    """查找所有的 SKILL.md 文件"""
    all_skills = []
    seen_paths = set()  # 用于去重
    
    for source_dir in SKILL_SOURCES:
        if not source_dir.exists():
            print(f"⚠️  目录不存在，跳过: {source_dir}")
            continue
            
        print(f"\n🔍 扫描目录: {source_dir}")
        
        # 查找所有 SKILL.md 文件
        for skill_file in source_dir.rglob("SKILL.md"):
            # 解析真实路径（处理符号链接）
            real_path = skill_file.resolve()
            
            if real_path in seen_paths:
                continue
                
            seen_paths.add(real_path)
            
            # 获取技能目录名称
            skill_dir = skill_file.parent
            skill_name = skill_dir.name
            
            all_skills.append({
                'name': skill_name,
                'path': real_path,
                'dir': real_path.parent,
                'source': source_dir.name
            })
            
            print(f"  ✓ 找到技能: {skill_name} ({source_dir.name})")
    
    return all_skills

def categorize_skills(skills):
    """将技能按类别分组"""
    categories = defaultdict(list)
    
    for skill in skills:
        # 根据路径判断类别
        path_str = str(skill['dir'])
        
        if 'cursor-system' in path_str or 'skills-cursor' in path_str:
            category = 'cursor-system'
        elif 'development' in path_str:
            category = 'development'
        elif 'design' in path_str:
            category = 'design'
        elif 'productivity' in path_str:
            category = 'productivity'
        elif 'browser' in path_str:
            category = 'browser'
        elif 'skill-management' in path_str:
            category = 'skill-management'
        elif 'content' in path_str or 'writing' in path_str or 'copywriting' in path_str:
            category = 'content-creation'
        elif 'baoyu' in path_str:
            category = 'baoyu-tools'
        elif 'question' in path_str:
            category = 'question-tools'
        elif '.system' in path_str:
            category = 'system'
        else:
            category = 'other'
        
        categories[category].append(skill)
    
    return categories

def create_skill_links(skills, dry_run=False):
    """创建技能符号链接到 Cursor 目录"""
    if not CURSOR_SKILLS_DIR.exists():
        print(f"\n📁 创建 Cursor 技能目录: {CURSOR_SKILLS_DIR}")
        if not dry_run:
            CURSOR_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for skill in skills:
        target_dir = CURSOR_SKILLS_DIR / skill['name']
        source_dir = skill['dir']
        
        # 检查目标是否已存在
        if target_dir.exists():
            # 如果已经是正确的符号链接，跳过
            if target_dir.is_symlink() and target_dir.resolve() == source_dir:
                skip_count += 1
                continue
            else:
                print(f"  ⚠️  目标已存在: {skill['name']}")
                skip_count += 1
                continue
        
        # 创建符号链接
        try:
            if not dry_run:
                target_dir.symlink_to(source_dir)
            print(f"  ✓ 链接技能: {skill['name']}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ 链接失败: {skill['name']} - {e}")
            error_count += 1
    
    return success_count, skip_count, error_count

def generate_report(categories, all_skills):
    """生成技能报告"""
    report_path = Path("/Users/chaim/CodeBuddy/公考项目/docs/skills_import_report.md")
    
    content = ["# Cursor 技能导入报告\n"]
    content.append(f"**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    content.append(f"**总计技能数**: {len(all_skills)}\n")
    content.append(f"**技能类别数**: {len(categories)}\n\n")
    
    content.append("## 技能分类统计\n\n")
    for category, skills in sorted(categories.items()):
        content.append(f"### {category.upper().replace('-', ' ')} ({len(skills)} 个)\n\n")
        for skill in sorted(skills, key=lambda x: x['name']):
            content.append(f"- **{skill['name']}**\n")
            content.append(f"  - 路径: `{skill['dir']}`\n")
            content.append(f"  - 来源: {skill['source']}\n")
        content.append("\n")
    
    content.append("## 所有技能列表\n\n")
    for i, skill in enumerate(sorted(all_skills, key=lambda x: x['name']), 1):
        content.append(f"{i}. **{skill['name']}** - `{skill['dir']}`\n")
    
    report_path.write_text('\n'.join(content), encoding='utf-8')
    return report_path

def main():
    print("=" * 60)
    print("🚀 Cursor 技能统一导入工具")
    print("=" * 60)
    
    # 1. 查找所有技能
    print("\n📚 第一步: 查找所有技能...")
    all_skills = find_all_skills()
    print(f"\n✅ 共找到 {len(all_skills)} 个唯一技能")
    
    # 2. 分类技能
    print("\n📊 第二步: 技能分类...")
    categories = categorize_skills(all_skills)
    for category, skills in sorted(categories.items()):
        print(f"  • {category}: {len(skills)} 个")
    
    # 3. 生成报告
    print("\n📝 第三步: 生成报告...")
    report_path = generate_report(categories, all_skills)
    print(f"  ✓ 报告已生成: {report_path}")
    
    # 4. 询问是否创建链接
    print("\n🔗 第四步: 创建符号链接...")
    print(f"目标目录: {CURSOR_SKILLS_DIR}")
    
    choice = input("\n是否创建符号链接？(y/n/d=dry-run): ").strip().lower()
    
    if choice == 'y':
        success, skip, error = create_skill_links(all_skills, dry_run=False)
        print(f"\n✅ 导入完成!")
        print(f"  • 成功: {success} 个")
        print(f"  • 跳过: {skip} 个")
        print(f"  • 失败: {error} 个")
    elif choice == 'd':
        print("\n🔍 执行预演（不实际创建链接）...")
        success, skip, error = create_skill_links(all_skills, dry_run=True)
        print(f"\n预演结果:")
        print(f"  • 将创建: {success} 个")
        print(f"  • 将跳过: {skip} 个")
        print(f"  • 可能失败: {error} 个")
    else:
        print("\n❌ 取消操作")
    
    print("\n" + "=" * 60)
    print("✨ 完成！")
    print("=" * 60)
    
    # 显示下一步操作
    print("\n📖 下一步操作:")
    print(f"1. 查看报告: {report_path}")
    print(f"2. 检查链接: ls -la {CURSOR_SKILLS_DIR}")
    print("3. 重启 Cursor 以加载新技能")

if __name__ == "__main__":
    main()
