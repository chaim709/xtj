<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

const props = defineProps<{
  path?: string
  height?: string
}>()

const loading = ref(true)
const error = ref(false)
const tikuUrl = computed(() => {
  const baseUrl = 'http://localhost:5003'
  return props.path ? `${baseUrl}${props.path}` : baseUrl
})

const frameHeight = computed(() => props.height || 'calc(100vh - 120px)')

const onLoad = () => {
  loading.value = false
}

const onError = () => {
  loading.value = false
  error.value = true
}

const retry = () => {
  error.value = false
  loading.value = true
}
</script>

<template>
  <div class="tiku-frame-container">
    <!-- 加载状态 -->
    <div v-if="loading && !error" class="tiku-loading">
      <div class="tiku-loading-spinner"></div>
      <span>正在加载题库系统...</span>
    </div>
    
    <!-- 错误状态 -->
    <div v-if="error" class="tiku-error">
      <div class="tiku-error-icon">😕</div>
      <div class="tiku-error-message">
        无法连接到题库系统，请确保题库系统已启动
      </div>
      <div style="margin-bottom: 12px; color: var(--vp-c-text-3); font-size: 14px;">
        启动命令: <code>cd gongkao-tiku-system && python run.py</code>
      </div>
      <button class="tiku-error-btn" @click="retry">重试</button>
      <a :href="tikuUrl" target="_blank" class="tiku-error-btn" style="margin-left: 12px; background: var(--vp-c-bg-soft); color: var(--vp-c-text-1);">
        在新窗口打开
      </a>
    </div>
    
    <!-- iframe -->
    <iframe 
      v-show="!loading && !error"
      :src="tikuUrl"
      class="tiku-frame"
      :style="{ height: frameHeight }"
      @load="onLoad"
      @error="onError"
      frameborder="0"
      allow="clipboard-write"
    ></iframe>
  </div>
</template>

<style scoped>
.tiku-frame-container {
  width: 100%;
  min-height: 500px;
}

.tiku-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--vp-c-text-2);
}

.tiku-loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--vp-c-divider);
  border-top-color: var(--vp-c-brand-1);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.tiku-error {
  text-align: center;
  padding: 40px;
  background: var(--vp-c-bg-soft);
  border-radius: 8px;
}

.tiku-error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.tiku-error-message {
  color: var(--vp-c-text-2);
  margin-bottom: 8px;
}

.tiku-error-btn {
  display: inline-block;
  padding: 8px 24px;
  background: var(--vp-c-brand-1);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  text-decoration: none;
  font-size: 14px;
}

.tiku-error-btn:hover {
  opacity: 0.9;
}

.tiku-frame {
  width: 100%;
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
</style>
