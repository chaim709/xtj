# PDF报告生成指南

## 📄 待转换文件

1. **完整版报告**（约230页）
   - 路径：`docs/2026年安徽省事业单位招聘超详细分析报告_最终完整版.md`
   - 大小：约1800行
   - 适合：全面学习和深入研究

2. **执行摘要**（约8页）
   - 路径：`docs/2026年安徽省事业单位招聘分析报告_执行摘要.md`
   - 大小：约150行
   - 适合：快速了解核心信息

---

## 🎯 推荐方法：VS Code插件（最简单）

### 步骤

1. **打开VS Code**

2. **安装Markdown PDF插件**
   - 按 `Cmd+Shift+X` 打开扩展商店
   - 搜索 `Markdown PDF`
   - 安装 `yzane.markdown-pdf`（300万+下载）

3. **打开Markdown文件**
   - 打开要转换的.md文件

4. **导出PDF**
   - 右键点击编辑器
   - 选择 `Markdown PDF: Export (pdf)`
   - 或按 `Cmd+Shift+P`，输入 `Markdown PDF: Export (pdf)`

5. **完成**
   - PDF自动生成在同目录下
   - 文件名：`原文件名.pdf`

### 优点
- ✅ 操作简单（3步完成）
- ✅ 支持中文
- ✅ 保留格式（表格、代码块等）
- ✅ 自动目录生成
- ✅ 免费使用

---

## 🔧 备选方法

### 方法2：Pandoc（专业用户）

```bash
# 安装Pandoc
brew install pandoc basictex

# 等待安装完成（约5-10分钟）

# 转换PDF
cd docs
pandoc "2026年安徽省事业单位招聘超详细分析报告_最终完整版.md" \
    -o "2026年安徽省事业单位招聘超详细分析报告.pdf" \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=3 \
    -V CJKmainfont="PingFang SC" \
    -V geometry:margin=2.5cm \
    --highlight-style=tango
```

**优点**：
- ✅ 专业级PDF质量
- ✅ 高度可定制
- ✅ 批量处理

**缺点**：
- ❌ 需要安装（约500MB）
- ❌ 命令行操作
- ❌ 学习成本高

### 方法3：在线工具

1. 打开 https://www.markdowntopdf.com/
2. 上传Markdown文件
3. 等待转换
4. 下载PDF

**优点**：
- ✅ 无需安装
- ✅ 操作简单

**缺点**：
- ❌ 需要上传文件（约1MB）
- ❌ 网络依赖
- ❌ 格式可能不完美

---

## 📋 PDF生成脚本（已提供）

如果选择Pandoc方法，可以直接运行：

```bash
# 已为您创建好的脚本
./scripts/generate_pdf.sh
```

---

## 🎨 PDF样式配置

### VS Code插件配置

创建或编辑 `.vscode/settings.json`：

```json
{
  "markdown-pdf.executablePath": "",
  "markdown-pdf.styles": [],
  "markdown-pdf.includeDefaultStyles": true,
  "markdown-pdf.highlightStyle": "github",
  "markdown-pdf.breaks": true,
  "markdown-pdf.emoji": true,
  "markdown-pdf.displayHeaderFooter": true,
  "markdown-pdf.headerTemplate": "<div style='font-size:9px; text-align:center; width:100%;'>2026年安徽省事业单位招聘分析报告</div>",
  "markdown-pdf.footerTemplate": "<div style='font-size:9px; text-align:center; width:100%;'>第 <span class='pageNumber'></span> 页</div>",
  "markdown-pdf.format": "A4",
  "markdown-pdf.margin": {
    "top": "2cm",
    "bottom": "2cm",
    "left": "2cm",
    "right": "2cm"
  }
}
```

---

## ✅ 建议使用流程

1. **VS Code插件转换** → 快速生成预览版PDF
2. **确认效果满意** → 使用该PDF即可
3. **如需专业排版** → 考虑使用Pandoc
4. **如需在线转换** → 使用在线工具

---

**推荐**：直接使用VS Code插件，简单快捷！✨
