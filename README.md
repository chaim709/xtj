# 公考培训机构管理系统

一套完整的公务员考试培训机构管理解决方案，包含培训管理、错题收集、知识库等多个子系统。

## 系统架构

```
├── gongkao-system/         # 公考培训管理系统（主系统）
│   ├── 学员管理
│   ├── 课程管理
│   ├── 智能选岗
│   └── 学习计划
│
├── cuoti-system/           # 错题收集系统
│   ├── 错题录入
│   ├── 智能分析
│   └── 个性化推荐
│
├── gongkao-zhishiku/       # 知识库系统
│   ├── 行测知识点
│   ├── 申论技巧
│   └── 常识积累
│
└── docs/                   # 开发文档
    ├── 需求文档
    ├── 设计文档
    └── 测试报告
```

## 技术栈

- **后端**: Python 3.11 + Flask
- **前端**: HTML + Tailwind CSS + Alpine.js
- **数据库**: SQLite (开发) / MySQL (生产)
- **文档**: VitePress

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+ (知识库系统)
- Git

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/YOUR_USERNAME/gongkao-project.git
cd gongkao-project
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

3. **安装依赖并运行**

```bash
# 公考管理系统
cd gongkao-system
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

4. **访问系统**

- 公考管理系统: http://localhost:5000
- 错题系统: http://localhost:5001

## 项目文档

- [部署指南](./DEPLOYMENT.md)
- [开发文档](./docs/)

## 数据目录

题库文件和数据库采用分离存储架构，不包含在代码仓库中。详见 [部署指南](./DEPLOYMENT.md)。

## License

Private - 仅供内部使用
