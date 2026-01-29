# 公考培训管理系统 - 配色系统规范

## 设计理念

- **主色调**: 蓝色系 - 传达专业、可信赖、教育行业特色
- **辅助色**: 橙色(行动)、绿色(成功)、紫色(高端)
- **风格**: 现代、清爽、专业

---

## 一、品牌色系 (Primary Blue)

| 等级 | 色值 | CSS 变量 | 用途 |
|------|------|----------|------|
| 50 | `#EFF6FF` | `--brand-50` | 最浅背景、hover状态 |
| 100 | `#DBEAFE` | `--brand-100` | 浅色背景、标签 |
| 200 | `#BFDBFE` | `--brand-200` | 边框、分隔线 |
| 300 | `#93C5FD` | `--brand-300` | 禁用状态 |
| 400 | `#60A5FA` | `--brand-400` | 图标、次要元素 |
| **500** | `#3B82F6` | `--brand-500` | 标准品牌色 |
| **600** | `#2563EB` | `--primary` | ⭐ 主色 - 按钮、链接 |
| 700 | `#1D4ED8` | `--primary-hover` | 悬停状态 |
| 800 | `#1E40AF` | `--primary-active` | 点击状态 |
| 900 | `#1E3A8A` | `--primary-dark` | 深色文字 |

### 使用示例
```css
/* 主按钮 */
.btn-primary {
    background: var(--primary);
    color: var(--text-inverse);
}
.btn-primary:hover {
    background: var(--primary-hover);
}

/* 链接 */
a { color: var(--primary); }
a:hover { color: var(--primary-hover); }

/* 浅色背景标签 */
.tag-primary {
    background: var(--brand-100);
    color: var(--primary-dark);
}
```

---

## 二、语义化颜色

### 2.1 成功 (Success - Green)

| 等级 | 色值 | CSS 变量 | 用途 |
|------|------|----------|------|
| 50 | `#F0FDF4` | `--success-50` | 成功提示背景 |
| 100 | `#DCFCE7` | `--success-100` | 徽章背景 |
| 500 | `#22C55E` | `--success-500` | 图标 |
| **600** | `#10B981` | `--success` | ⭐ 成功状态 |
| 文字 | `#065F46` | `--success-text` | 成功文字 |

**适用场景**: 完成提示、在线状态、正向趋势、通过验证

### 2.2 警告 (Warning - Amber)

| 等级 | 色值 | CSS 变量 | 用途 |
|------|------|----------|------|
| 50 | `#FFFBEB` | `--warning-50` | 警告提示背景 |
| 100 | `#FEF3C7` | `--warning-light` | 徽章背景 |
| 500 | `#F59E0B` | `--warning` | ⭐ 警告状态 |
| 文字 | `#92400E` | `--warning-text` | 警告文字 |

**适用场景**: 待处理、需注意、超期提醒、重点关注

### 2.3 危险 (Danger - Red)

| 等级 | 色值 | CSS 变量 | 用途 |
|------|------|----------|------|
| 50 | `#FEF2F2` | `--danger-50` | 错误提示背景 |
| 100 | `#FEE2E2` | `--danger-light` | 徽章背景 |
| 500 | `#EF4444` | `--danger` | ⭐ 危险状态 |
| 文字 | `#991B1B` | `--danger-text` | 危险文字 |

**适用场景**: 错误提示、删除操作、负向趋势、紧急事项

### 2.4 信息 (Info - Cyan)

| 等级 | 色值 | CSS 变量 | 用途 |
|------|------|----------|------|
| 50 | `#ECFEFF` | `--info-50` | 信息提示背景 |
| 100 | `#CFFAFE` | `--info-light` | 徽章背景 |
| 500 | `#06B6D4` | `--info` | ⭐ 信息状态 |
| 文字 | `#0E7490` | `--info-text` | 信息文字 |

**适用场景**: 提示信息、帮助说明、中性状态

---

## 三、功能色

### 3.1 强调色 (Accent - Orange)

| 色值 | CSS 变量 | 用途 |
|------|----------|------|
| `#FFF7ED` | `--accent-light` | 背景 |
| `#F97316` | `--accent` / `--cta` | ⭐ 行动号召按钮 |
| `#EA580C` | `--accent-hover` | 悬停状态 |

**适用场景**: CTA按钮、重要操作、促销标签

### 3.2 紫色 (Purple - VIP/高级)

| 色值 | CSS 变量 | 用途 |
|------|----------|------|
| `#FAF5FF` | `--purple-50` | 背景 |
| `#EDE9FE` | `--purple-light` | 徽章背景 |
| `#8B5CF6` | `--purple` | ⭐ VIP/协议班标识 |
| `#5B21B6` | `--purple-text` | 文字 |

**适用场景**: 协议班学员、VIP服务、高级功能

---

## 四、中性色 (Slate)

| 等级 | 色值 | CSS 变量 | 用途 |
|------|------|----------|------|
| 50 | `#F8FAFC` | `--slate-50` | 页面背景 |
| 100 | `#F1F5F9` | `--slate-100` | 卡片背景备用 |
| 200 | `#E2E8F0` | `--slate-200` | 边框 |
| 300 | `#CBD5E1` | `--slate-300` | 禁用边框 |
| 400 | `#94A3B8` | `--slate-400` | 辅助文字 |
| 500 | `#64748B` | `--slate-500` | 次要文字 |
| 600 | `#475569` | `--slate-600` | 正文文字 |
| 700 | `#334155` | `--slate-700` | 标题文字 |
| 800 | `#1E293B` | `--slate-800` | 重点文字 |
| 900 | `#0F172A` | `--slate-900` | 最深色 |

---

## 五、背景与文字

### 5.1 背景色

| CSS 变量 | 色值 | 用途 |
|----------|------|------|
| `--background` | `#F8FAFC` | 页面主背景 |
| `--background-alt` | `#F1F5F9` | 备用背景 |
| `--background-muted` | `#E2E8F0` | 静音区域背景 |
| `--card-bg` | `#FFFFFF` | 卡片背景 |
| `--card-bg-hover` | `#F8FAFC` | 卡片悬停 |

### 5.2 文字色

| CSS 变量 | 色值 | 对比度 | 用途 |
|----------|------|--------|------|
| `--text-primary` | `#0F172A` | 15.8:1 | 标题、重要文字 |
| `--text-secondary` | `#475569` | 7.5:1 | 正文内容 |
| `--text-muted` | `#94A3B8` | 3.5:1 | 辅助说明 |
| `--text-disabled` | `#CBD5E1` | 2.0:1 | 禁用状态 |
| `--text-inverse` | `#FFFFFF` | - | 深色背景上的文字 |
| `--text-link` | `#2563EB` | 4.6:1 | 链接文字 |

### 5.3 边框色

| CSS 变量 | 色值 | 用途 |
|----------|------|------|
| `--border-light` | `#F1F5F9` | 轻边框、分隔 |
| `--border-default` | `#E2E8F0` | 默认边框 |
| `--border-strong` | `#CBD5E1` | 强调边框 |
| `--border-focus` | `#2563EB` | 焦点边框 |

---

## 六、渐变色

| CSS 变量 | 渐变 | 用途 |
|----------|------|------|
| `--gradient-primary` | `#3B82F6 → #1D4ED8` | 主渐变 |
| `--gradient-welcome` | `#3B82F6 → #2563EB → #1D4ED8` | 欢迎横幅 |
| `--gradient-purple` | `#A855F7 → #7C3AED` | VIP/高级 |
| `--gradient-green` | `#22C55E → #16A34A` | 成功渐变 |
| `--gradient-orange` | `#F97316 → #EA580C` | CTA渐变 |
| `--gradient-cyan` | `#06B6D4 → #0891B2` | 信息渐变 |
| `--gradient-dark` | `#334155 → #0F172A` | 深色渐变 |
| `--sidebar-bg` | `#1E3A5F → #0F172A` | 侧边栏 |

---

## 七、组件配色指南

### 7.1 按钮

| 类型 | 背景 | 文字 | 悬停背景 |
|------|------|------|----------|
| 主要按钮 | `--primary` | `--text-inverse` | `--primary-hover` |
| 次要按钮 | `--slate-100` | `--text-secondary` | `--slate-200` |
| 成功按钮 | `--success` | `--text-inverse` | `--success-600` |
| 危险按钮 | `--danger` | `--text-inverse` | `--danger-600` |
| CTA按钮 | `--accent` | `--text-inverse` | `--accent-hover` |
| 幽灵按钮 | `transparent` | `--primary` | `--brand-50` |

### 7.2 徽章

| 类型 | 背景 | 文字 |
|------|------|------|
| 成功 | `--success-100` | `--success-text` |
| 警告 | `--warning-100` | `--warning-text` |
| 危险 | `--danger-100` | `--danger-text` |
| 信息 | `--info-100` | `--info-text` |
| 紫色 | `--purple-light` | `--purple-text` |
| 主色 | `--brand-100` | `--primary-dark` |

### 7.3 卡片

| 元素 | 颜色 |
|------|------|
| 背景 | `--card-bg` |
| 边框 | `--border-default` |
| 标题 | `--text-primary` |
| 内容 | `--text-secondary` |
| 说明 | `--text-muted` |
| 悬停背景 | `--card-bg-hover` |

### 7.4 表单

| 元素 | 默认 | 焦点 | 错误 |
|------|------|------|------|
| 边框 | `--border-default` | `--border-focus` | `--danger` |
| 背景 | `--card-bg` | `--card-bg` | `--danger-50` |
| 文字 | `--text-primary` | `--text-primary` | `--text-primary` |

---

## 八、业务场景配色

### 8.1 学员状态

| 状态 | 颜色 | CSS 变量 |
|------|------|----------|
| 在读 | 绿色 | `--success` |
| 待跟进 | 橙色 | `--warning` |
| 重点关注 | 红色 | `--danger` |
| 协议班 | 紫色 | `--purple` |
| 已结课 | 灰色 | `--slate-400` |

### 8.2 督学记录 - 学员情绪

| 情绪 | 背景 | 文字 |
|------|------|------|
| 积极 | `--success-100` | `--success-text` |
| 平稳 | `--info-100` | `--info-text` |
| 焦虑 | `--warning-100` | `--warning-text` |
| 消极 | `--danger-100` | `--danger-text` |

### 8.3 课程状态

| 状态 | 颜色 | CSS 变量 |
|------|------|----------|
| 招生中 | 橙色 | `--accent` |
| 进行中 | 绿色 | `--success` |
| 已结束 | 灰色 | `--slate-400` |
| 已取消 | 红色 | `--danger` |

### 8.4 热力图

| 等级 | 颜色 | 含义 |
|------|------|------|
| Level 0 | `#EBEDF0` | 无课程 |
| Level 1 | `#9BE9A8` | 少量课程 |
| Level 2 | `#40C463` | 中等课程 |
| Level 3 | `#30A14E` | 较多课程 |
| Level 4 | `#216E39` | 大量课程 |

---

## 九、可访问性检查

### 对比度要求 (WCAG 2.1)
- **正文文字**: 最低 4.5:1
- **大号文字**: 最低 3:1
- **非文本元素**: 最低 3:1

### 当前配色对比度

| 组合 | 对比度 | 状态 |
|------|--------|------|
| `--text-primary` on `--background` | 15.8:1 | ✅ AAA |
| `--text-secondary` on `--background` | 7.5:1 | ✅ AA |
| `--text-muted` on `--background` | 3.5:1 | ⚠️ 仅用于辅助文字 |
| `--text-inverse` on `--primary` | 8.5:1 | ✅ AAA |
| `--primary` on `--background` | 4.6:1 | ✅ AA |

---

## 十、暗色模式预留

```css
@media (prefers-color-scheme: dark) {
    :root {
        --background: #0F172A;
        --background-alt: #1E293B;
        --card-bg: #1E293B;
        --card-bg-hover: #334155;
        
        --text-primary: #F8FAFC;
        --text-secondary: #CBD5E1;
        --text-muted: #64748B;
        
        --border-light: #334155;
        --border-default: #475569;
    }
}
```

---

## 更新日期
2026-01-28
