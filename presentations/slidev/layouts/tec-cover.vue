<script setup>
import { computed } from 'vue'
import TecMedia from '../components/TecMedia.vue'

const props = defineProps({
  frontmatter: {
    type: Object,
    default: () => ({}),
  },
})

const frontmatter = computed(() => props.frontmatter ?? {})
const programLines = computed(() => frontmatter.value.program ?? [])
const presenters = computed(() => frontmatter.value.presenters ?? [])
</script>

<template>
  <div class="slidev-layout cover">
    <div class="tec-cover-frame" aria-label="Portada de presentación">
      <aside class="tec-cover-rail" aria-label="Franja institucional">
        <img src="/tec-cover-rail.png" alt="" />
        <span>{{ frontmatter.railText }}</span>
      </aside>

      <img class="tec-logo" src="/tec-posgrados.png" alt="Tecnológico de Monterrey Posgrados" />

      <div class="tec-program">
        <template v-for="(line, index) in programLines" :key="`${line}-${index}`">
          {{ line }}<br v-if="index < programLines.length - 1" />
        </template>
      </div>

      <TecMedia :media="frontmatter.coverMedia" placement="right" />

      <main class="tec-cover-title">
        <h1>{{ frontmatter.title }}</h1>
        <p>{{ frontmatter.organization }}</p>
      </main>

      <section class="tec-cover-meta" aria-label="Campos de portada">
        <div class="tec-meta-label">Presenta(n):</div>
        <ul class="tec-presenter-list">
          <li v-for="presenter in presenters" :key="presenter">{{ presenter }}</li>
        </ul>
        <div class="tec-meta-line">
          Asesor: <strong>{{ frontmatter.advisor }}</strong>
        </div>
        <div class="tec-meta-line">
          Patrocinador(es): <strong>{{ frontmatter.sponsor }}</strong>
        </div>
      </section>

      <div class="tec-date">{{ frontmatter.date }}</div>
    </div>
  </div>
</template>
