<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: {
    type: [String, Number],
    default: '',
  },
})

const parts = computed(() => {
  const value = String(props.text ?? '')
  return value
    .split(/(`[^`]+`)/g)
    .filter(Boolean)
    .map((part) => {
      const isCode = part.startsWith('`') && part.endsWith('`')
      return {
        code: isCode,
        text: isCode ? part.slice(1, -1) : part,
      }
    })
})
</script>

<template>
  <template v-for="(part, index) in parts" :key="`${part.text}-${index}`">
    <code v-if="part.code">{{ part.text }}</code>
    <template v-else>{{ part.text }}</template>
  </template>
</template>
