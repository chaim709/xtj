---
layout: home

hero:
  name: "公考知识库"
  text: "行测申论备考指南"
  tagline: 无论你是初出茅庐的应届生，还是久经沙场的职场人士，本站始终为你的备考之旅保驾护航
  image:
    src: /hero-image.svg
    alt: 公考知识库
  actions:
    - theme: brand
      text: 📝 开始刷题
      link: /tiku/practice
    - theme: alt
      text: 📕 错题本
      link: /tiku/mistakes
    - theme: alt
      text: 📚 行测知识
      link: /xingce/ziliao/

features:
  - icon: 💡
    title: 精准定位，高效备考
    details: 内容融合了各大顶尖机构与考试领域专家的深度见解，保证信息的权威性、正确性。同时加入高效学习工具，让备考更加高效、有的放矢。
  - icon: 📦
    title: 全面覆盖，深度解析
    details: 网站以「查缺补漏、对症下药」为核心理念，涵盖行测、申论等考试全科目基础知识点，内容广泛全面、清晰易查、通俗易懂，告别碎片化学习。
  - icon: 🎉
    title: 刷题系统，智能分析
    details: 配套的刷题系统提供AI智能解析、错题本、薄弱项分析，让你精准定位问题，针对性提升。与知识库内容深度整合。
  - icon: 🔄
    title: 持续更新，紧跟考情
    details: 我们将持续关注考试动态，实时更新核心资料库与优化内容，确保能获取到最前沿、最实用的备考资源。
---

<style>
:root {
  --vp-home-hero-name-color: transparent;
  --vp-home-hero-name-background: -webkit-linear-gradient(120deg, #3eaf7c 30%, #42b983);
  --vp-home-hero-image-background-image: linear-gradient(-45deg, #3eaf7c 50%, #42b983 50%);
  --vp-home-hero-image-filter: blur(44px);
}

.VPHome {
  padding-bottom: 0 !important;
}
</style>

## 📚 学习模块

<div class="module-grid">

### 行测五大模块

| 模块 | 说明 | 链接 |
|------|------|------|
| 📊 资料分析 | 增长率、比重、平均数、倍数计算 | [开始学习](/xingce/ziliao/) |
| 📖 言语理解 | 片段阅读、逻辑填空、语句表达 | [开始学习](/xingce/yanyu/) |
| 📏 数量关系 | 数字推理、数学运算 | [开始学习](/xingce/shuliang/) |
| 🎨 判断推理 | 图形、定义、类比、逻辑判断 | [开始学习](/xingce/panduan/) |
| 🧠 常识判断 | 政治、法律、经济、历史、地理 | [开始学习](/changshi/) |

### 申论写作

| 题型 | 说明 | 链接 |
|------|------|------|
| 📝 概括归纳 | 提炼材料核心信息 | [开始学习](/shenlun/gaigui) |
| 🔍 综合分析 | 分析问题本质原因 | [开始学习](/shenlun/fenxi) |
| 💡 提出对策 | 针对问题提出解决方案 | [开始学习](/shenlun/duice) |
| 📄 公文写作 | 各类应用文写作 | [开始学习](/shenlun/gongwen) |
| ✍️ 大作文 | 议论文写作技巧 | [开始学习](/shenlun/zuowen) |

</div>

## 🔗 配套工具

<div class="tools-grid">

- 📝 [**刷题系统**](http://localhost:5003) - AI智能解析、错题本、薄弱项分析
- 🔍 **词语查询** - 快速查询易混词语辨析（开发中）
- 📊 **学习统计** - 查看学习进度和正确率分析
- 🎯 **专项突破** - 针对薄弱项进行专项练习

</div>

<style>
.module-grid {
  margin: 2rem 0;
}

.module-grid table {
  width: 100%;
  border-collapse: collapse;
}

.module-grid th, .module-grid td {
  padding: 12px 16px;
  border: 1px solid var(--vp-c-divider);
}

.module-grid th {
  background: var(--vp-c-bg-soft);
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin: 1rem 0;
}

.tools-grid ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tools-grid li {
  padding: 1rem;
  background: var(--vp-c-bg-soft);
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

@media (max-width: 640px) {
  .tools-grid {
    grid-template-columns: 1fr;
  }
}
</style>
