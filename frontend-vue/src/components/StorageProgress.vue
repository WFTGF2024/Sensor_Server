<template>
  <div class="storage-progress">
    <div class="progress">
      <div
        class="progress-bar"
        :class="progressClass"
        :style="{ width: percentage + '%' }"
      ></div>
    </div>
    <p class="text-muted">
      已使用 {{ formatBytes(used) }} / {{ formatBytes(limit) }}（{{ percentage }}%）
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  used: {
    type: Number,
    required: true
  },
  limit: {
    type: Number,
    required: true
  }
})

const percentage = computed(() => {
  if (props.limit === 0) return 0
  return Math.round((props.used / props.limit) * 100 * 100) / 100
})

const progressClass = computed(() => {
  if (percentage.value > 90) return 'progress-bar-danger'
  if (percentage.value > 70) return 'progress-bar-warning'
  return 'progress-bar-success'
})

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.storage-progress {
  margin-bottom: 1rem;
}

.progress {
  height: 20px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-bar {
  height: 100%;
  background-color: #3498db;
  transition: width 0.3s;
}

.progress-bar-success {
  background-color: #27ae60;
}

.progress-bar-warning {
  background-color: #f39c12;
}

.progress-bar-danger {
  background-color: #e74c3c;
}

.text-muted {
  color: #6c757d;
  margin: 0;
}
</style>
