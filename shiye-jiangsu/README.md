# 安徽事业单位智能选岗系统

**Anhui Public Institution Position Selection System**

一个专为安徽省事业单位考生打造的智能化岗位选择系统，基于3,443个真实岗位数据和AI算法，帮助考生科学选岗、提高上岸概率。

---

## 🎯 项目特色

### 核心功能
- 🤖 **智能推荐**: AI驱动的个性化岗位推荐
- 📊 **数据可视化**: 多维度数据图表和地图展示
- 🎲 **概率预测**: 科学的上岸概率计算模型
- 🔍 **智能搜索**: 强大的岗位搜索和筛选引擎
- 📈 **竞争力测评**: 5维度个人竞争力评估
- 🗺️ **地区对比**: 16地市全方位对比分析

### 数据基础
- **岗位数量**: 3,443个
- **招聘人数**: 4,221人
- **覆盖范围**: 省直 + 16个地级市
- **数据准确率**: 98.90%

---

## 🏗️ 项目结构

```
shiye-system/
├── backend/                 # 后端应用
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # 路由控制器
│   │   ├── services/       # 业务逻辑
│   │   ├── templates/      # HTML模板
│   │   └── static/         # 静态资源
│   ├── config.py           # 配置文件
│   ├── run.py              # 启动文件
│   └── requirements.txt    # 依赖包
│
├── data/                    # 数据文件
│   ├── raw/                # 原始数据
│   ├── processed/          # 处理后数据
│   └── database/           # 数据库文件
│
├── scripts/                 # 工具脚本
│   ├── import_data.py      # 数据导入
│   ├── analyze_data.py     # 数据分析
│   └── backup.sh           # 备份脚本
│
├── docs/                    # 文档
│   ├── ALIGNMENT_*.md      # 对齐文档
│   ├── DESIGN_*.md         # 设计文档
│   ├── TASK_*.md           # 任务文档
│   └── API.md              # API文档
│
└── README.md               # 项目说明
```

---

## 🚀 快速开始

### 环境要求
- Python 3.9+
- SQLite 3
- 现代浏览器 (Chrome / Firefox / Safari)

### 方式一：一键启动（推荐）

```bash
cd /Users/chaim/CodeBuddy/公考项目/shiye-system
./启动系统.sh
```

### 方式二：手动启动

```bash
# 1. 进入后端目录
cd /Users/chaim/CodeBuddy/公考项目/shiye-system/backend

# 2. 激活虚拟环境（已创建）
source venv/bin/activate

# 3. 启动服务
python3 run.py
```

### 方式三：首次完整安装

```bash
# 1. 进入后端目录
cd /Users/chaim/CodeBuddy/公考项目/shiye-system/backend

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 导入数据
cd ..
python3 scripts/import_positions_simple.py

# 6. 优化数据库
python3 scripts/optimize_database.py

# 7. 启动服务
cd backend
python3 run.py
```

### 访问系统

**浏览器打开**: http://localhost:5002

**状态检查**: 
- ✅ 看到首页表示启动成功
- ✅ 数据显示"3,344个岗位"表示数据导入成功

---

## 💻 技术栈

### 后端
- **框架**: Flask 2.3+
- **ORM**: SQLAlchemy
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **算法**: NumPy, Pandas, Scikit-learn

### 前端
- **UI框架**: Tailwind CSS
- **交互**: Alpine.js
- **图表**: ECharts
- **地图**: 高德地图 API

---

## 📊 核心算法

### 智能推荐算法
```python
综合评分 = 上岸概率(30%) + 待遇水平(25%) + 发展空间(20%) 
          + 生活质量(15%) + 综合评价(10%)
```

### 上岸概率模型
```python
上岸概率 = 基础概率 × 学历系数 × 专业系数 × 分数系数 × 地域系数
```

---

## 📖 使用指南

### 1. 智能选岗向导
1. 填写个人信息（学历、专业、分数预估）
2. 设置地域偏好和期望条件
3. 系统自动匹配并推荐岗位
4. 查看冲刺型/稳妥型/保底型岗位

### 2. 岗位搜索
- 按单位名称、地区、专业搜索
- 高级筛选（学历、系统、竞争度）
- 结果排序和导出

### 3. 竞争力测评
- 5维度能力评估
- 生成个性化报告
- 获取提升建议

### 4. 数据分析
- 地市分布地图
- 专业需求分析
- 竞争态势预测

---

## 🎯 版本规划

### V1.0 (当前)
- ✅ 核心选岗功能
- ✅ 数据搜索和筛选
- ✅ 基础可视化
- ✅ 上岸概率计算

### V1.1 (计划中)
- 历年数据对比
- 用户反馈系统
- 性能优化

### V2.0 (未来)
- AI智能问答
- 社区交流
- 移动端适配

---

## 📝 License

Private - 仅供内部使用

---

## 📧 联系方式

如有问题或建议，请联系项目维护团队。

---

**最后更新**: 2026-02-05
