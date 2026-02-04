# Cursor 技能使用指南

## 🎉 导入完成状态

**导入时间**: 2026-02-04 23:17

**导入结果**:
- ✅ 成功导入: 41 个新技能
- ⏭️ 跳过重复: 12 个已存在技能
- ❌ 导入失败: 0 个
- 📊 **总计可用技能**: 47 个

## 📚 技能分类与使用

### 1. Cursor 系统工具 (5个)

这些是 Cursor 专用的系统级技能：

- **create-rule** - 创建 Cursor 规则文件
- **create-skill** - 创建新的技能
- **create-subagent** - 创建子代理
- **migrate-to-skills** - 迁移到技能系统
- **update-cursor-settings** - 更新 Cursor 设置

**使用方法**: 直接在 Cursor 中提及技能名称，AI 会自动调用

### 2. 前端开发工具 (5个)

专业的前端开发辅助技能：

- **frontend-testing** - 前端测试框架
- **frontend-code-review** - 代码审查
- **component-refactoring** - 组件重构
- **frontend-design** - 前端设计实现
- **server-deployment** - 服务器部署

### 3. 设计工具 (4个)

设计相关的辅助工具：

- **figma-implement-design** - Figma 设计实现
- **ui-ux-pro-max** - UI/UX 专业工具
- **obsidian-bases** - Obsidian 基础工具
- **obsidian-canvas-creator** - Obsidian 画布创建器

### 4. 内容创作工具 (16个)

丰富的内容创作和处理工具：

#### 文档处理
- **docx** - Word 文档处理
- **pdf** - PDF 文档处理
- **xlsx** - Excel 表格处理
- **pptx** - PowerPoint 演示文稿处理

#### 写作工具
- **copywriting** - 文案写作
- **content-strategy** - 内容策略
- **writing-skills** - 写作技巧
- **writing-plans** - 写作计划
- **doc-coauthoring** - 文档协作
- **social-content** - 社交媒体内容

#### 抖音工具链
- **skill-1-douyin-video-fetcher** - 抖音视频获取
- **skill-2-video-audio-extractor** - 视频音频提取
- **skill-3-audio-transcriber** - 音频转录
- **skill-4-ai-learning-analyzer** - AI学习分析
- **skill-4-jiangsu-gwy-content-analyzer** - 江苏公务员内容分析
- **skill-5-video-metrics-calculator** - 视频指标计算
- **skill-6-feishu-table-writer** - 飞书表格写入
- **skill-7-douyin-tracker-scheduler** - 抖音追踪调度器

### 5. 生产力工具 (4个)

提升工作效率的工具：

- **position-selector** - 岗位选择器
- **question-ai-analyzer** - 问题AI分析
- **question-document-parser** - 问题文档解析
- **question-import-finalizer** - 问题导入终结器

### 6. 浏览器工具 (1个)

- **browser-use** - 浏览器自动化工具

### 7. 宝玉专用工具 (2个)

- **baoyu-slide-deck** - 宝玉幻灯片制作
- **baoyu-xhs-images** - 宝玉小红书图片工具

### 8. 技能管理工具 (4个)

- **skill-creator** - 技能创建器
- **skill-lookup** - 技能查找
- **skill-installer** - 技能安装器
- **find-skills** - 查找技能

### 9. 其他实用工具 (6个)

- **brainstorming** - 头脑风暴
- **marketing-psychology** - 营销心理学
- **systematic-debugging** - 系统化调试

## 🚀 如何使用技能

### 方法 1: 自然语言触发

在 Cursor 对话中直接提及任务，AI 会自动匹配并使用相关技能：

```
"帮我分析这个前端组件的性能问题"
→ 自动触发 frontend-code-review 或 component-refactoring

"将这个 Figma 设计转换为代码"
→ 自动触发 figma-implement-design

"帮我处理这个 Excel 文件"
→ 自动触发 xlsx
```

### 方法 2: 明确指定技能

如果需要明确使用某个技能：

```
"使用 frontend-testing 技能为这个组件编写测试"
"用 position-selector 帮我分析这些岗位"
```

### 方法 3: 组合使用多个技能

可以同时使用多个技能完成复杂任务：

```
"用 question-document-parser 解析这个文档，
然后用 question-ai-analyzer 分析问题，
最后用 question-import-finalizer 导入到系统"
```

## 📖 技能详细信息

每个技能都包含：
- 📋 **SKILL.md** - 技能说明和使用方法
- 🔧 **配置文件** - 技能的配置选项
- 📚 **示例** - 使用示例和最佳实践

查看技能详情：
```bash
# 查看某个技能的详细信息
cat ~/.cursor/skills-cursor/skill-name/SKILL.md
```

## 🔄 更新和维护

### 更新技能

技能是通过符号链接导入的，更新源技能会自动同步到 Cursor：

```bash
# 技能源目录
~/.codex/skills/
~/.agents/skills/
~/Clawdbot/unified-skills/

# Cursor 技能目录（符号链接）
~/.cursor/skills-cursor/
```

### 重新导入技能

如果需要重新导入所有技能：

```bash
cd /Users/chaim/CodeBuddy/公考项目
python3 scripts/import_all_skills_to_cursor.py
```

### 查看技能列表

```bash
# 查看所有已安装的技能
ls -la ~/.cursor/skills-cursor/

# 统计技能数量
ls ~/.cursor/skills-cursor/ | wc -l
```

## 🛠️ 故障排查

### 技能未被识别

1. **重启 Cursor**: 新导入的技能需要重启 Cursor 才能生效
2. **检查符号链接**: 确保技能目录的符号链接正确
3. **查看日志**: 检查 Cursor 的开发者工具控制台

### 技能冲突

如果发现同名技能：
- 系统会自动跳过重复的技能
- 可以查看 `docs/skills_import_report.md` 了解详情

### 删除技能

```bash
# 删除单个技能（只删除链接，不影响源文件）
rm ~/.cursor/skills-cursor/skill-name

# 清空所有技能
rm -rf ~/.cursor/skills-cursor/*
```

## 📊 技能统计

- **总技能数**: 53 个（去重后）
- **已导入**: 47 个
- **技能类别**: 10 个
- **技能来源**: 3 个目录

详细统计报告: `docs/skills_import_report.md`

## 🎯 推荐使用场景

### 日常开发
- 使用 `frontend-testing` 编写测试
- 使用 `component-refactoring` 重构代码
- 使用 `frontend-code-review` 审查代码

### 设计实现
- 使用 `figma-implement-design` 将设计转换为代码
- 使用 `ui-ux-pro-max` 优化用户体验

### 内容处理
- 使用 `docx/pdf/xlsx` 处理各类文档
- 使用 `copywriting` 创作文案

### 数据分析
- 使用 `question-ai-analyzer` 分析问题
- 使用 `position-selector` 分析岗位数据

## 💡 最佳实践

1. **明确任务**: 清晰描述你的需求，AI 会自动选择最合适的技能
2. **组合使用**: 复杂任务可以组合多个技能完成
3. **查看文档**: 遇到问题时查看技能的 SKILL.md 文档
4. **定期更新**: 保持技能源目录的更新

## 🔗 相关资源

- 技能导入脚本: `scripts/import_all_skills_to_cursor.py`
- 技能统计报告: `docs/skills_import_report.md`
- Cursor 技能目录: `~/.cursor/skills-cursor/`

---

**提示**: 重启 Cursor 后，所有技能将自动加载并可用！🎉
