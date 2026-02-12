<template>
  <div class="stat-card">
    <div class="stat-value" :style="{ color: color }">{{ formattedValue }}</div>
    <div class="stat-label">{{ label }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: [Number, String],
    required: true
  },
  label: {
    type: String,
    required: true
  },
  color: {
    type: String,
    default: '#3498db'
  },
  suffix: {
    type: String,
    default: ''
  }
})

const formattedValue = computed(() => {
  return `${props.value}${props.suffix}`
})
</script>

<style scoped>
.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #3498db;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #6c757d;
  font-size: 0.875rem;
  text-transform: uppercase;
}
</style>
