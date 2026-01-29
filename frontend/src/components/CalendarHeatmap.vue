<script setup>
import { computed } from 'vue'
import { useDarkMode } from '@/composables/useDarkMode'

const { isDark } = useDarkMode()

const props = defineProps({
  // Array of { date: string, value: number } objects
  data: {
    type: Array,
    required: true,
    validator: (value) => value.every(item => 'date' in item && 'value' in item)
  },
  // Main color for the heatmap (hex or CSS color)
  color: {
    type: String,
    default: '#22c55e' // green-500
  },
  // Size of each square in pixels
  squareSize: {
    type: Number,
    default: 12
  },
  // Gap between squares in pixels
  gap: {
    type: Number,
    default: 3
  },
  // Border radius of squares in pixels
  borderRadius: {
    type: Number,
    default: 2
  },
  // Show tooltips on hover
  showTooltips: {
    type: Boolean,
    default: true
  }
})

// Weekday names (short)
const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

// Calculate the max value for intensity scaling
const maxValue = computed(() => {
  if (props.data.length === 0) return 1
  const max = Math.max(...props.data.map(d => d.value))
  return max > 0 ? max : 1
})

// Determine layout mode based on data length
const layoutMode = computed(() => {
  const length = props.data.length
  if (length <= 7) return 'row'       // Single row for week or less
  return 'calendar'                    // GitHub-style calendar layout
})

// Calculate number of columns based on layout
const columns = computed(() => {
  const length = props.data.length
  if (layoutMode.value === 'row') return length
  // Calendar mode: 7 rows (days of week), columns = weeks
  return Math.ceil(length / 7)
})

// Generate column headers based on layout mode
const columnHeaders = computed(() => {
  if (props.data.length === 0) return []

  if (layoutMode.value === 'row') {
    // For single row: show weekday names for each date
    return props.data.map(item => {
      const date = new Date(item.date)
      const dayIndex = date.getDay()
      // Convert Sunday (0) to index 6, Monday (1) to index 0, etc.
      const adjustedIndex = dayIndex === 0 ? 6 : dayIndex - 1
      return weekDays[adjustedIndex]
    })
  } else {
    // For calendar mode: show week start dates
    const headers = []
    const numCols = columns.value

    for (let col = 0; col < numCols; col++) {
      const index = col * 7
      if (index < props.data.length) {
        const date = new Date(props.data[index].date)
        // Format as "Jan 1" or similar
        const formatted = date.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric'
        })
        headers.push(formatted)
      }
    }

    return headers
  }
})

// Row labels for calendar mode (weekday names on the left)
const rowLabels = computed(() => {
  if (layoutMode.value !== 'calendar') return []
  return weekDays
})

// Organize data for calendar layout (column-major order for GitHub-style)
const organizedData = computed(() => {
  if (layoutMode.value !== 'calendar') {
    return props.data
  }

  // For calendar layout, we need to arrange data in column-major order
  // Each column represents a week, rows represent days of week
  const result = []
  const numCols = columns.value

  for (let col = 0; col < numCols; col++) {
    for (let row = 0; row < 7; row++) {
      const index = col * 7 + row
      if (index < props.data.length) {
        result.push({
          ...props.data[index],
          gridColumn: col + 1,
          gridRow: row + 1
        })
      }
    }
  }

  return result
})

// Get color with opacity based on value intensity
const getSquareColor = (value) => {
  if (value === 0) {
    return isDark.value ? '#27272a' : '#e5e5e5' // zinc-800 / neutral-200
  }

  const intensity = value / maxValue.value
  // Map intensity to opacity levels (0.2 to 1.0)
  const opacity = 0.2 + (intensity * 0.8)

  return hexToRgba(props.color, opacity)
}

// Convert hex color to rgba
const hexToRgba = (hex, alpha) => {
  // Remove # if present
  hex = hex.replace('#', '')

  // Handle shorthand hex
  if (hex.length === 3) {
    hex = hex.split('').map(c => c + c).join('')
  }

  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// Format date for tooltip
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Header container style
const headerStyle = computed(() => {
  const cellWidth = props.squareSize + props.gap
  return {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns.value}, ${cellWidth}px)`,
    marginBottom: '4px',
    marginLeft: layoutMode.value === 'calendar' ? '28px' : '0'
  }
})

// Grid styles
const gridStyle = computed(() => {
  const style = {
    display: 'grid',
    gap: `${props.gap}px`,
    width: 'fit-content'
  }

  if (layoutMode.value === 'calendar') {
    // For calendar layout, use explicit grid placement
    style.gridTemplateColumns = `repeat(${columns.value}, ${props.squareSize}px)`
    style.gridTemplateRows = `repeat(7, ${props.squareSize}px)`
    style.gridAutoFlow = 'column'
  } else {
    // Single row
    style.gridTemplateColumns = `repeat(${columns.value}, ${props.squareSize}px)`
    style.gridTemplateRows = `${props.squareSize}px`
  }

  return style
})

// Square styles
const getSquareStyle = (item) => {
  return {
    width: `${props.squareSize}px`,
    height: `${props.squareSize}px`,
    backgroundColor: getSquareColor(item.value),
    borderRadius: `${props.borderRadius}px`
  }
}
</script>

<template>
  <div class="calendar-heatmap pl-2">
    <!-- Column Headers (inclined) -->
    <div :style="headerStyle" class="column-headers">
      <div v-for="(header, index) in columnHeaders" :key="index" class="header-cell">
        <span class="header-text text-xs font-semibold text-neutral-500 dark:text-neutral-400">
          {{ header }}
        </span>
      </div>
    </div>

    <!-- Main grid with optional row labels -->
    <div class="grid-container" :class="{ 'with-row-labels': layoutMode === 'calendar' }">
      <!-- Row labels for calendar mode -->
      <div v-if="layoutMode === 'calendar'" class="row-labels">
        <div v-for="(label, index) in rowLabels" :key="index"
          class="row-label text-xs font-semibold text-neutral-500 dark:text-neutral-400"
          :style="{ height: `${squareSize}px`, marginBottom: `${gap}px` }">
          {{ label }}
        </div>
      </div>

      <!-- Heatmap grid -->
      <div :style="gridStyle" class="heatmap-grid">
        <div v-for="(item, index) in organizedData" :key="item.date || index" :style="getSquareStyle(item)"
          class="heatmap-square transition-all duration-150 hover:ring-2 hover:ring-offset-1 hover:ring-neutral-400 dark:hover:ring-neutral-500 cursor-default"
          :title="showTooltips ? `${formatDate(item.date)}: ${item.value}` : undefined" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.calendar-heatmap {
  display: inline-block;
}

.column-headers {
  height: 32px;
}

.header-cell {
  position: relative;
  height: 32px;
}

.header-text {
  position: absolute;
  bottom: 0;
  left: 0;
  transform-origin: bottom left;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.grid-container {
  display: flex;
  align-items: flex-start;
}

.grid-container.with-row-labels {
  gap: 6px;
}

.row-labels {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-right: 2px;
}

.row-label {
  display: flex;
  align-items: center;
  line-height: 1;
}

.heatmap-grid {
  line-height: 0;
}

.heatmap-square {
  display: inline-block;
}
</style>
