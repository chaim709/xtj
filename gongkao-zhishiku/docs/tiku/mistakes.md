---
layout: page
title: 错题本
---

<script setup>
import { ref } from 'vue'

const activeTab = ref('mistakes')

const tabs = [
  { id: 'home', label: '🏠 首页', path: '/' },
  { id: 'practice', label: '📝 专项练习', path: '/practice' },
  { id: 'mistakes', label: '📕 错题本', path: '/mistakes' },
  { id: 'stats', label: '📊 统计分析', path: '/stats' },
]
</script>

# 📕 错题本

自动收集错题，连续答对2次移出，支持添加笔记。

<div class="tiku-tabs">
  <a 
    v-for="tab in tabs" 
    :key="tab.id"
    :href="`/tiku/${tab.id === 'home' ? '' : tab.id}`"
    class="tiku-tab"
    :class="{ active: activeTab === tab.id }"
  >
    {{ tab.label }}
  </a>
</div>

<TikuFrame path="/mistakes" height="calc(100vh - 200px)" />

<style>
.tiku-tabs {
  display: flex;
  gap: 12px;
  margin: 16px 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--vp-c-divider);
  flex-wrap: wrap;
}

.tiku-tab {
  padding: 8px 16px;
  border-radius: 6px;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  font-size: 14px;
}

.tiku-tab:hover {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
}

.tiku-tab.active {
  background: var(--vp-c-brand-1);
  color: white;
}
</style>
