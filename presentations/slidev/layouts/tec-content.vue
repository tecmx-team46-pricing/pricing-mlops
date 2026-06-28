<script setup>
import { computed } from 'vue'
import TecContentBlocks from '../components/TecContentBlocks.vue'
import TecMedia from '../components/TecMedia.vue'

const props = defineProps({
  frontmatter: {
    type: Object,
    default: () => ({}),
  },
})

const frontmatter = computed(() => props.frontmatter ?? {})
</script>

<template>
  <div class="slidev-layout default">
    <div class="tec-content-frame" :aria-label="frontmatter.ariaLabel || frontmatter.title">
      <header class="tec-top-band" aria-label="Franja superior institucional">
        <img src="/tec-slide-top-band.png" alt="" />
        <div class="tec-section-mark">{{ frontmatter.sectionMark || 'MNA' }}</div>
        <div class="tec-project-name">{{ frontmatter.projectName }}</div>
      </header>

      <h1>{{ frontmatter.title }}</h1>
      <TecMedia :media="frontmatter.media" placement="top" />
      <TecContentBlocks :content="frontmatter.content" />
      <slot />
    </div>
  </div>
</template>
