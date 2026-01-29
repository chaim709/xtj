# 技能使用指南 (Skill Usage Guide)

> **目的**: 帮助 AI 助手在开发过程中自动识别场景并调用合适的技能，提升开发效率和质量

---

## 一、技能自动触发规则

### 1.1 触发词映射表

| 场景关键词 | 自动触发技能 | 优先级 |
|-----------|-------------|--------|
| 设计、UI、界面、样式、配色、字体 | `ui-ux-pro-max` / `frontend-design` | HIGH |
| 调试、Bug、错误、失败、崩溃 | `systematic-debugging` | HIGH |
| Excel、表格、xlsx、csv | `xlsx` | HIGH |
| PDF、文档提取、表单填写 | `pdf-processing` | HIGH |
| 浏览器、网页、自动化、截图 | `browser-use` | HIGH |
| 完成、提交、通过、修复 | `verification-before-completion` | CRITICAL |
| 计划、规划、设计方案 | `writing-plans` / `brainstorming` | HIGH |
| GitHub、PR、Issue、CI | `github` | MEDIUM |
| n8n、工作流、自动化 | `n8n-*` 系列技能 | HIGH |

### 1.2 自动触发流程

```
用户请求 → 关键词识别 → 技能匹配 → 读取SKILL.md → 按指南执行
```

---

## 二、核心技能详解

### 2.1 UI/UX 设计类

#### ui-ux-pro-max (UI/UX 设计智能)
**触发场景**: 设计新页面、组件、配色方案、字体选择

**使用流程**:
```bash
# 1. 生成设计系统 (必须首先执行)
python3 skills/ui-ux-pro-max/scripts/search.py "<产品类型> <行业> <关键词>" --design-system -p "项目名"

# 2. 补充详细搜索 (按需)
python3 skills/ui-ux-pro-max/scripts/search.py "<关键词>" --domain <domain>

# 3. 获取技术栈指南
python3 skills/ui-ux-pro-max/scripts/search.py "<关键词>" --stack html-tailwind
```

**可用域**:
- `product` - 产品类型推荐
- `style` - UI 风格、颜色、效果
- `typography` - 字体配对
- `color` - 配色方案
- `landing` - 页面结构
- `chart` - 图表类型
- `ux` - 最佳实践

**关键规则**:
- ❌ 禁止使用 emoji 作为图标 → 使用 SVG (Heroicons, Lucide)
- ❌ 禁止通用字体 (Inter, Roboto, Arial)
- ✅ 所有可点击元素添加 `cursor-pointer`
- ✅ 悬停效果使用 150-300ms 过渡
- ✅ 检查亮/暗模式对比度

---

#### frontend-design (前端设计)
**触发场景**: 创建独特、生产级前端界面

**核心原则**:
- 选择**大胆**的美学方向 (极简、复古未来、有机自然、奢华精致等)
- 避免 "AI 美学" - 紫色渐变、通用布局
- 每个设计都要独特

**关注点**:
- **字体**: 独特选择，避免 Arial/Inter
- **颜色**: 主导色 + 锐利点缀
- **动效**: CSS 动画、页面加载编排
- **空间**: 不对称、重叠、打破网格
- **背景**: 渐变网格、噪点纹理、几何图案

---

### 2.2 调试与验证类

#### systematic-debugging (系统化调试)
**触发场景**: 遇到任何 Bug、测试失败、意外行为

**铁律**: 
```
没有根因调查，禁止提出修复方案
```

**四阶段流程**:

| 阶段 | 关键活动 | 成功标准 |
|------|---------|---------|
| 1. 根因调查 | 读错误信息、复现、检查变更、收集证据 | 理解 WHAT 和 WHY |
| 2. 模式分析 | 找工作示例、对比差异 | 识别差异 |
| 3. 假设测试 | 形成单一假设、最小化测试 | 确认或新假设 |
| 4. 实现修复 | 创建测试、修复、验证 | Bug 解决 |

**红旗 - 立即停止**:
- "快速修复一下，之后再调查"
- "试着改改 X 看看行不行"
- "应该是 X 的问题，让我修一下"
- 已尝试 3+ 次修复仍失败 → 质疑架构

---

#### verification-before-completion (完成前验证)
**触发场景**: 声称工作完成、修复成功、测试通过之前

**铁律**:
```
没有新鲜的验证证据，禁止声称完成
```

**门控函数**:
```
声称任何状态之前:
1. 识别: 什么命令能证明这个声明?
2. 运行: 执行完整命令 (新鲜、完整)
3. 阅读: 完整输出，检查退出码
4. 验证: 输出是否确认声明?
   - 否 → 陈述实际状态 + 证据
   - 是 → 陈述声明 + 证据
5. 然后才能: 做出声明
```

**禁止用语**:
- "应该可以了"
- "大概没问题"
- "看起来正确"
- 任何没有运行验证命令的成功暗示

---

### 2.3 文件处理类

#### xlsx (Excel 处理)
**触发场景**: 创建、编辑、分析 Excel 文件

**关键原则**:
```python
# ❌ 错误 - 硬编码计算值
total = df['Sales'].sum()
sheet['B10'] = total  # 硬编码 5000

# ✅ 正确 - 使用 Excel 公式
sheet['B10'] = '=SUM(B2:B9)'
```

**工作流程**:
1. 选择工具: pandas (数据分析) / openpyxl (公式/格式)
2. 创建/加载文件
3. 修改数据、公式、格式
4. 保存文件
5. **重新计算公式** (使用公式时必须):
   ```bash
   python recalc.py output.xlsx
   ```
6. 验证并修复错误

**颜色编码标准** (财务模型):
- 蓝色文本: 硬编码输入
- 黑色文本: 所有公式
- 绿色文本: 工作表内链接
- 红色文本: 外部链接
- 黄色背景: 需关注的假设

---

#### pdf-processing (PDF 处理)
**触发场景**: 提取 PDF 文本/表格、填写表单、合并/拆分 PDF

**快速开始**:
```python
import pdfplumber

# 提取文本
with pdfplumber.open("document.pdf") as pdf:
    text = pdf.pages[0].extract_text()

# 提取表格
with pdfplumber.open("report.pdf") as pdf:
    tables = pdf.pages[0].extract_tables()
```

**可用包**:
- `pdfplumber` - 文本和表格提取 (推荐)
- `pypdf` - PDF 操作、合并、拆分
- `pdf2image` - PDF 转图片
- `pytesseract` - OCR 扫描 PDF

---

### 2.4 浏览器自动化

#### browser-use (浏览器自动化)
**触发场景**: 网页导航、表单填写、截图、数据提取

**核心工作流**:
```bash
# 1. 导航
browser-use open https://example.com

# 2. 检查状态 (获取元素索引)
browser-use state

# 3. 交互 (使用索引)
browser-use click 5
browser-use input 3 "text"

# 4. 验证
browser-use screenshot output.png

# 5. 关闭 (完成后必须)
browser-use close
```

**浏览器模式**:
- `chromium` - 默认，无头 Chromium
- `--headed` - 可见浏览器窗口 (调试用)
- `--browser real` - 使用用户 Chrome (保留登录状态)

**重要提示**:
- 总是先运行 `browser-use state` 获取元素索引
- 使用 `--headed` 调试
- **完成后必须关闭浏览器**: `browser-use close`

---

### 2.5 规划与协作类

#### brainstorming (头脑风暴)
**触发场景**: 任何创意工作之前 - 创建功能、构建组件、修改行为

**流程**:
1. 理解项目上下文 (文件、文档、最近提交)
2. **一次一个问题**探索想法 (优先多选题)
3. 提出 2-3 种方案及权衡
4. **分段呈现设计** (200-300 词/段)，每段确认
5. 文档保存到 `docs/plans/YYYY-MM-DD-<topic>-design.md`

**关键原则**:
- 一次一个问题
- 优先多选题
- 无情地 YAGNI
- 增量验证

---

#### writing-plans (编写计划)
**触发场景**: 有规范或需求的多步骤任务，编码之前

**计划结构**:
```markdown
# [功能名] 实现计划

**目标:** [一句话描述]
**架构:** [2-3 句方法描述]
**技术栈:** [关键技术/库]

---

### 任务 N: [组件名]

**文件:**
- 创建: `exact/path/to/file.py`
- 修改: `exact/path/to/existing.py:123-145`
- 测试: `tests/exact/path/to/test.py`

**步骤 1: 编写失败测试**
[代码]

**步骤 2: 运行测试验证失败**
运行: `pytest tests/path/test.py::test_name -v`
预期: FAIL

**步骤 3: 编写最小实现**
[代码]

**步骤 4: 运行测试验证通过**
运行: `pytest tests/path/test.py::test_name -v`
预期: PASS

**步骤 5: 提交**
```

**原则**: DRY、YAGNI、TDD、频繁提交

---

### 2.6 GitHub 操作

#### github (GitHub CLI)
**触发场景**: 与 GitHub 交互 - Issues, PRs, CI

**常用命令**:
```bash
# 检查 PR CI 状态
gh pr checks 55 --repo owner/repo

# 列出最近工作流运行
gh run list --repo owner/repo --limit 10

# 查看运行详情
gh run view <run-id> --repo owner/repo

# 查看失败步骤日志
gh run view <run-id> --repo owner/repo --log-failed

# API 查询
gh api repos/owner/repo/pulls/55 --jq '.title, .state'

# JSON 输出
gh issue list --repo owner/repo --json number,title
```

---

### 2.7 n8n 工作流类

#### n8n 技能矩阵

| 技能 | 用途 |
|------|------|
| `n8n-code-javascript` | Code 节点 JavaScript 编写 |
| `n8n-code-python` | Code 节点 Python 编写 |
| `n8n-expression-syntax` | 表达式语法验证 |
| `n8n-mcp-tools-expert` | MCP 工具使用 |
| `n8n-node-configuration` | 节点配置 |
| `n8n-validation-expert` | 验证错误解释 |
| `n8n-workflow-patterns` | 工作流架构模式 |

**触发场景**: 任何 n8n 相关开发

---

## 三、技能组合使用模式

### 3.1 新功能开发流程

```
1. brainstorming          → 理解需求、探索方案
2. writing-plans          → 创建详细实现计划
3. ui-ux-pro-max         → 生成设计系统 (如有 UI)
4. frontend-design       → 实现界面
5. systematic-debugging  → 遇到问题时使用
6. verification-before-completion → 完成前验证
7. github                → 提交 PR
```

### 3.2 Bug 修复流程

```
1. systematic-debugging   → 四阶段调查
2. verification-before-completion → 验证修复
3. github                 → 提交修复
```

### 3.3 数据处理流程

```
1. xlsx / pdf-processing  → 处理文件
2. browser-use           → 网页数据抓取 (如需)
3. verification-before-completion → 验证结果
```

---

## 四、禁止事项清单

### 4.1 全局禁止

| 禁止行为 | 替代方案 |
|---------|---------|
| 未调查就提出修复 | 使用 `systematic-debugging` |
| 未验证就声称完成 | 使用 `verification-before-completion` |
| 使用 emoji 作图标 | 使用 SVG 图标库 |
| 使用通用字体 | 使用独特字体配对 |
| 硬编码 Excel 计算值 | 使用 Excel 公式 |
| 不关闭浏览器 | 完成后 `browser-use close` |

### 4.2 代码风格禁止

- ❌ 冗长变量名
- ❌ 不必要的注释
- ❌ 多余的 print 语句
- ❌ 未经验证的"应该可以"

---

## 五、技能路径速查

```
/Users/chaim/.claude/skills/
├── ui-ux-pro-max-skill-2.2.1/
├── frontend-design/
├── systematic-debugging/
├── verification-before-completion/
├── browser-use/
├── xlsx/
├── pdf-processing/
├── brainstorming/
├── writing-plans/
├── github/
├── n8n-*/
└── ...

/Users/chaim/.cursor/skills-cursor/
├── create-rule/
├── create-skill/
├── update-cursor-settings/
└── ...
```

---

## 六、快速参考卡片

### 设计一个新页面
```
1. 读取 ui-ux-pro-max SKILL.md
2. python3 search.py "关键词" --design-system -p "项目"
3. 实现时参考 frontend-design 原则
4. 完成后 verification-before-completion
```

### 修复一个 Bug
```
1. 读取 systematic-debugging SKILL.md
2. 阶段1: 根因调查 (禁止跳过)
3. 阶段2-4: 分析、假设、实现
4. verification-before-completion 验证
```

### 处理 Excel 数据
```
1. 读取 xlsx SKILL.md
2. 使用公式，不硬编码
3. python recalc.py 重新计算
4. 验证无公式错误
```

### 浏览器自动化
```
1. browser-use open URL
2. browser-use state (获取索引)
3. browser-use click/input/...
4. browser-use close (必须!)
```

---

> **更新日期**: 2026-01-28
> **版本**: 1.0
