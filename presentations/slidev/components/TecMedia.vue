<script setup>
import { computed } from 'vue'

const props = defineProps({
  media: {
    type: Object,
    default: () => ({}),
  },
  placement: {
    type: String,
    default: 'top',
  },
})

const mediaKindClass = {
  timeline: 'tec-timeline',
  'metric-strip': 'tec-kpi-strip',
  'status-band': 'tec-status-band',
  'alert-strip': 'tec-alert-strip',
  'repo-split': 'tec-repo-split',
  'cicd-flow': 'tec-cicd-flow',
  'dual-run-flow': 'tec-dual-run-flow',
  'notebook-handoff': 'tec-notebook-handoff',
  'code-abstraction': 'tec-code-abstraction',
  'pipeline-flow': 'tec-pipeline-flow',
  roadmap: 'tec-roadmap',
}

const mediaItems = computed(() => props.media.items ?? props.media.steps ?? [])

const rootClass = computed(() => {
  if (props.placement === 'right') {
    return ['tec-media-right', 'tec-media-right--filled']
  }

  if (props.media.kind === 'flow') {
    return ['tec-media-top', props.media.variant === 'ops' ? 'tec-ops-flow' : 'tec-evidence-flow']
  }

  return ['tec-media-top', mediaKindClass[props.media.kind]]
})

function itemValue(item) {
  return typeof item === 'object' ? item.value : item
}

function itemLabel(item) {
  return typeof item === 'object' ? item.label : item
}

function itemVariant(item) {
  return typeof item === 'object' ? item.variant : ''
}

function itemCode(item) {
  return typeof item === 'object' ? item.code : ''
}

function itemKey(item, index) {
  return `${itemValue(item) ?? itemLabel(item)}-${index}`
}

function statusClass(item) {
  const status = typeof item === 'object' ? item.status : ''
  return {
    green: 'tec-status-green',
    yellow: 'tec-status-yellow',
    red: 'tec-status-red',
  }[status] ?? ''
}

function alertClass(item) {
  const variant = itemVariant(item)
  return {
    red: 'is-red',
    yellow: 'is-yellow',
  }[variant] ?? ''
}

function dualNodeClass(item) {
  const variant = itemVariant(item)
  return {
    gate: 'tec-dual-node-gate',
    azure: 'tec-dual-node-azure',
  }[variant] ?? ''
}

function laneKey(lane, index) {
  return `${lane.label}-${index}`
}
</script>

<template>
  <figure :class="rootClass" :aria-label="media.ariaLabel || media.label || ''">
    <template v-if="media.kind === 'cover-cycle'">
      <div class="tec-cover-cycle">
        <span v-for="(item, index) in mediaItems" :key="itemKey(item, index)">
          {{ itemLabel(item) }}
        </span>
      </div>
      <strong>{{ media.title }}</strong>
    </template>

    <template v-else-if="media.kind === 'flow'">
      <template v-for="(item, index) in mediaItems" :key="itemKey(item, index)">
        <span>{{ itemLabel(item) }}</span>
        <i v-if="index < mediaItems.length - 1" />
      </template>
    </template>

    <template v-else-if="media.kind === 'cicd-flow'">
      <template v-for="(item, index) in mediaItems" :key="itemKey(item, index)">
        <div>
          <strong>{{ itemValue(item) }}</strong>
          <span>{{ itemLabel(item) }}</span>
        </div>
        <i v-if="index < mediaItems.length - 1" />
      </template>
    </template>

    <template v-else-if="media.kind === 'notebook-handoff'">
      <template v-for="(item, index) in mediaItems" :key="itemKey(item, index)">
        <div>
          <strong>{{ itemValue(item) }}</strong>
          <span>{{ itemLabel(item) }}</span>
        </div>
        <i v-if="index < mediaItems.length - 1" />
      </template>
    </template>

    <template v-else-if="media.kind === 'code-abstraction'">
      <div v-for="(item, index) in mediaItems" :key="itemKey(item, index)" class="tec-code-row">
        <div>
          <strong>{{ itemValue(item) }}</strong>
          <span>{{ itemLabel(item) }}</span>
        </div>
        <code>{{ itemCode(item) }}</code>
      </div>
    </template>

    <template v-else-if="media.kind === 'dual-run-flow'">
      <div class="tec-dual-source">
        <strong>{{ media.source?.value }}</strong>
        <span>{{ media.source?.label }}</span>
      </div>
      <div class="tec-dual-lanes">
        <div v-for="(lane, laneIndex) in media.lanes" :key="laneKey(lane, laneIndex)" class="tec-dual-lane">
          <b>{{ lane.label }}</b>
          <template v-for="(item, index) in lane.items" :key="itemKey(item, index)">
            <div :class="dualNodeClass(item)">
              <strong>{{ itemValue(item) }}</strong>
              <span>{{ itemLabel(item) }}</span>
            </div>
            <i v-if="index < lane.items.length - 1" />
          </template>
        </div>
      </div>
    </template>

    <template v-else-if="media.kind === 'status-band'">
      <div
        v-for="(item, index) in mediaItems"
        :key="itemKey(item, index)"
        class="tec-status"
        :class="statusClass(item)"
      >
        <span>{{ itemLabel(item) }}</span>
      </div>
    </template>

    <template v-else-if="media.kind === 'pipeline-flow' || media.kind === 'roadmap'">
      <span v-for="(item, index) in mediaItems" :key="itemKey(item, index)">
        {{ itemLabel(item) }}
      </span>
    </template>

    <template v-else>
      <div
        v-for="(item, index) in mediaItems"
        :key="itemKey(item, index)"
        :class="alertClass(item)"
      >
        <strong>{{ itemValue(item) }}</strong>
        <span>{{ itemLabel(item) }}</span>
      </div>
    </template>
  </figure>
</template>
