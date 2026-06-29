<script setup>
import { computed } from 'vue'
import InlineText from './InlineText.vue'

const props = defineProps({
  content: {
    type: Object,
    default: () => ({}),
  },
})

const rootClass = computed(() => {
  const kind = props.content.kind
  return [
    'tec-content-area',
    {
      'statement-stack': 'tec-two-col',
      'section-intro': 'tec-section-intro',
      'two-column': 'tec-two-col',
      'three-column': 'tec-three-col',
      'kpi-grid': 'tec-kpi-grid',
      'signal-table': 'tec-signal-table-wrap',
    }[kind],
  ]
})

function panelClass(column) {
  if (column.type === 'decision') {
    return 'tec-decision-card'
  }

  return ['tec-bullet-panel', column.variant === 'muted' ? 'tec-panel-muted' : '']
}

function itemKey(item, index) {
  if (typeof item === 'object') {
    return `${item.value ?? item.title ?? item.label ?? item.text}-${index}`
  }

  return `${item}-${index}`
}
</script>

<template>
  <main :class="rootClass">
    <template v-if="content.kind === 'statement-stack'">
      <section class="tec-statement">
        <p><InlineText :text="content.statement" /></p>
      </section>

      <section class="tec-decision-stack">
        <div v-for="(item, index) in content.stack" :key="itemKey(item, index)">
          <strong>{{ item.value }}</strong>
          <span><InlineText :text="item.label" /></span>
        </div>
      </section>
    </template>

    <template v-else-if="content.kind === 'section-intro'">
      <strong>{{ content.label }}</strong>
      <p><InlineText :text="content.text" /></p>
      <div class="tec-tag-row">
        <span v-for="(tag, index) in content.tags" :key="itemKey(tag, index)">
          {{ tag }}
        </span>
      </div>
    </template>

    <template v-else-if="content.kind === 'kpi-grid'">
      <div
        v-for="(item, index) in content.items"
        :key="itemKey(item, index)"
        class="tec-kpi-card"
        :class="{ 'tec-kpi-wide': item.wide }"
      >
        <strong>{{ item.value }}</strong>
        <span><InlineText :text="item.label" /></span>
      </div>
    </template>

    <template v-else-if="content.kind === 'signal-table'">
      <table class="tec-signal-table">
        <thead>
          <tr>
            <th>Señal</th>
            <th>Métrica</th>
            <th>Uso ejecutivo</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in content.rows" :key="itemKey(row, rowIndex)">
            <td>{{ row.signal }}</td>
            <td><InlineText :text="row.metric" /></td>
            <td><InlineText :text="row.use" /></td>
          </tr>
        </tbody>
      </table>
    </template>

    <template v-else-if="content.kind === 'two-column' || content.kind === 'three-column'">
      <section
        v-for="(column, index) in content.columns"
        :key="itemKey(column, index)"
        :class="panelClass(column)"
      >
        <template v-if="column.type === 'decision'">
          <span>{{ column.label }}</span>
          <strong><InlineText :text="column.body" /></strong>
        </template>

        <template v-else>
          <h2 v-if="column.title"><InlineText :text="column.title" /></h2>
          <ul v-if="column.bullets?.length">
            <li v-for="(bullet, bulletIndex) in column.bullets" :key="itemKey(bullet, bulletIndex)">
              <InlineText :text="bullet" />
            </li>
          </ul>
          <p v-if="column.text"><InlineText :text="column.text" /></p>
          <div v-if="column.examples?.length" class="tec-mini-code-list">
            <div v-for="(example, exampleIndex) in column.examples" :key="itemKey(example, exampleIndex)">
              <span>{{ example.label }}</span>
              <code>{{ example.code }}</code>
            </div>
          </div>
        </template>
      </section>
    </template>
  </main>
</template>
