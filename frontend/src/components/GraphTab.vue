<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import api from '@/services/api'
import { useDarkMode } from '@/composables/useDarkMode'
import { useLanguage } from '@/composables/useLanguage'
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'

// Register Chart.js components
Chart.register(...registerables)

const { isDark } = useDarkMode()
const { t } = useLanguage()

// Graph state
const graphStartDate = ref('')
const graphEndDate = ref('')
const chartInstances = ref({
  boolean: null,
  counter: null,
  value: null,
  rating: null
})
const graphData = ref({
  boolean: [],
  counter: [],
  value: [],
  rating: []
})

// Computed property for dynamic years
const quickSelectYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [
    currentYear,
    currentYear - 1,
    currentYear - 2
  ]
})

// Helper function to fill missing dates with 0 values
const fillMissingDates = (data) => {
  if (!data || data.length === 0) return data
  // Fill missing dates for each habit
  return data.map(habitData => {
    if (!habitData.data || habitData.data.length === 0) {
      return habitData
    }

    // Find the min and max dates where this habit has actual data
    const dates = habitData.data.map(point => point.date).sort()
    const minDataDate = dates[0]
    const maxDataDate = dates[dates.length - 1]

    // Create a map of existing data points
    const dataMap = new Map()
    habitData.data.forEach(point => {
      dataMap.set(point.date, point.value)
    })

    // Generate dates only between min and max data dates
    const filledData = []
    const current = new Date(minDataDate)
    const end = new Date(maxDataDate)

    while (current <= end) {
      const dateStr = current.toISOString().split('T')[0]
      filledData.push({
        date: dateStr,
        value: dataMap.get(dateStr) || 0
      })
      current.setDate(current.getDate() + 1)
    }

    return {
      ...habitData,
      data: filledData
    }
  })
}

// Initialize date range for graphs (default: current month)
const initializeDateRange = () => {
  const now = new Date()
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  graphStartDate.value = startOfMonth.toISOString().split('T')[0]
  graphEndDate.value = now.toISOString().split('T')[0]
}

// Set date range to entire year
const setYearRange = (year) => {
  graphStartDate.value = `${year}-01-01`
  graphEndDate.value = `${year}-12-31`
}

// Set date range to all available data
const setAllDataRange = async () => {
  try {
    const response = await api.get('habits/date_range/')
    if (response.data.start_date && response.data.end_date) {
      graphStartDate.value = response.data.start_date
      graphEndDate.value = response.data.end_date
    } else {
      // Fallback if no data available
      graphStartDate.value = new Date().toISOString().split('T')[0]
      graphEndDate.value = new Date().toISOString().split('T')[0]
    }
  } catch (err) {
    console.error('Failed to fetch date range:', err)
    // Fallback on error
    graphStartDate.value = '2020-01-01'
    graphEndDate.value = new Date().toISOString().split('T')[0]
  }
}

// Fetch graph data from API
const fetchGraphData = async () => {
  if (!graphStartDate.value || !graphEndDate.value) return

  try {
    const response = await api.get('habits/graph_data/', {
      params: {
        start_date: graphStartDate.value,
        end_date: graphEndDate.value
      }
    })

    // Fill missing dates with 0 for each habit type
    graphData.value = {
      boolean: fillMissingDates(response.data.boolean || []),
      counter: fillMissingDates(response.data.counter || []),
      value: fillMissingDates(response.data.value || []),
      rating: fillMissingDates(response.data.rating || [])
    }

    await renderCharts()
  } catch (err) {
    console.error('Failed to fetch graph data:', err)
  }
}

// Render all charts
const renderCharts = async () => {
  // Ensure DOM is fully updated before accessing canvas elements
  await nextTick()

  const habitTypes = ['boolean', 'counter', 'value', 'rating']

  habitTypes.forEach(type => {
    const canvasId = `chart-${type}`
    const canvas = document.getElementById(canvasId)

    if (!canvas) {
      console.warn(`Canvas element #${canvasId} not found in DOM`)
      return
    }

    const ctx = canvas.getContext('2d')
    if (!ctx) {
      console.warn(`Could not get 2D context from canvas #${canvasId}`)
      return
    }

    // Destroy existing chart
    if (chartInstances.value[type]) {
      chartInstances.value[type].destroy()
    }

    const data = graphData.value[type] || []

    if (data.length === 0) return

    // Prepare datasets - one per habit
    const datasets = data.map(habitData => ({
      label: habitData.habit_name,
      data: habitData.data.map(d => ({ x: d.date, y: d.value })),
      borderColor: habitData.color,
      backgroundColor: habitData.color + '20',
      tension: 0.3,
      fill: type === 'boolean' ? false : true,
      pointRadius: 4,
      pointHoverRadius: 6,
      spanGaps: false
    }))

    chartInstances.value[type] = new Chart(ctx, {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: isDark.value ? '#a8a29e' : '#57534e',
              font: {
                family: 'system-ui',
                weight: 'bold'
              },
              padding: 15,
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: isDark.value ? '#292524' : '#ffffff',
            titleColor: isDark.value ? '#fafaf9' : '#1c1917',
            bodyColor: isDark.value ? '#a8a29e' : '#57534e',
            borderColor: isDark.value ? '#44403c' : '#d6d3d1',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                if (context.parsed.y !== null) {
                  label += context.parsed.y;
                }
                return label;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day',
              displayFormats: {
                day: 'MMM d'
              }
            },
            grid: {
              color: isDark.value ? '#44403c' : '#d6d3d1'
            },
            ticks: {
              color: isDark.value ? '#a8a29e' : '#57534e',
              font: {
                weight: '600'
              }
            }
          },
          y: {
            beginAtZero: true,
            grace: '5%',
            grid: {
              color: isDark.value ? '#44403c' : '#d6d3d1'
            },
            ticks: {
              color: isDark.value ? '#a8a29e' : '#57534e',
              font: {
                weight: '600'
              }
            }
          }
        }
      }
    })
  })
}

// Watch for date changes
watch([graphStartDate, graphEndDate], () => {
  fetchGraphData()
})

// Watch for dark mode changes to update charts
watch(isDark, async () => {
  await renderCharts()
})

// Expose fetchGraphData so parent can trigger it when tab becomes active
defineExpose({ fetchGraphData })

onMounted(() => {
  initializeDateRange()
  fetchGraphData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Date Range Selector -->
    <div
      class="bg-white dark:bg-neutral-800 rounded-4xl p-8 shadow-lg border border-neutral-100 dark:border-neutral-700">
      <h2 class="text-2xl font-black text-neutral-900 dark:text-white mb-6">{{ t('dateRange') }}</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div class="space-y-2">
          <label class="text-xs font-black uppercase tracking-widest text-neutral-400 ml-2">{{ t('startDate')
            }}</label>
          <input v-model="graphStartDate" type="date"
            class="w-full bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-50 dark:border-neutral-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-neutral-600 focus:border-yellow-500 transition outline-none font-bold text-neutral-900 dark:text-white" />
        </div>
        <div class="space-y-2">
          <label class="text-xs font-black uppercase tracking-widest text-neutral-400 ml-2">{{ t('endDate')
            }}</label>
          <input v-model="graphEndDate" type="date"
            class="w-full bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-50 dark:border-neutral-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-neutral-600 focus:border-yellow-500 transition outline-none font-bold text-neutral-900 dark:text-white" />
        </div>
      </div>

      <!-- Quick Select Buttons -->
      <div class="pt-4 border-t border-neutral-100 dark:border-neutral-700">
        <p class="text-xs font-black uppercase tracking-widest text-neutral-400 ml-2 mb-3">Quick Select</p>
        <div class="flex gap-3 flex-wrap">
          <button @click="setAllDataRange"
            class="px-6 py-2.5 bg-yellow-600 text-white rounded-xl font-bold text-sm hover:bg-yellow-700 transition-all shadow-sm active:scale-95">
            All
          </button>
          <button v-for="year in quickSelectYears" :key="year" @click="setYearRange(year)"
            class="px-6 py-2.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-900 dark:text-white rounded-xl font-bold text-sm hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-all shadow-sm active:scale-95">
            {{ year }}
          </button>
        </div>
      </div>
    </div>

    <!-- Boolean Habits Chart -->
    <div
      class="bg-white dark:bg-neutral-800 rounded-4xl p-8 shadow-lg border border-neutral-100 dark:border-neutral-700">
      <h3 class="text-xl font-black text-neutral-900 dark:text-white mb-6 uppercase tracking-tight">{{
        t('booleanHabits') }}
      </h3>
      <div class="h-80 flex items-center justify-center"
        v-if="!graphData.boolean || graphData.boolean.length === 0">
        <p class="text-neutral-400 dark:text-neutral-500 font-medium text-lg">{{ t('noData') }}</p>
      </div>
      <div class="h-80" v-else>
        <canvas id="chart-boolean"></canvas>
      </div>
    </div>

    <!-- Counter Habits Chart -->
    <div
      class="bg-white dark:bg-neutral-800 rounded-4xl p-8 shadow-lg border border-neutral-100 dark:border-neutral-700">
      <h3 class="text-xl font-black text-neutral-900 dark:text-white mb-6 uppercase tracking-tight">{{
        t('counterHabits') }}
      </h3>
      <div class="h-80 flex items-center justify-center"
        v-if="!graphData.counter || graphData.counter.length === 0">
        <p class="text-neutral-400 dark:text-neutral-500 font-medium text-lg">{{ t('noData') }}</p>
      </div>
      <div class="h-80" v-else>
        <canvas id="chart-counter"></canvas>
      </div>
    </div>

    <!-- Value Habits Chart -->
    <div
      class="bg-white dark:bg-neutral-800 rounded-4xl p-8 shadow-lg border border-neutral-100 dark:border-neutral-700">
      <h3 class="text-xl font-black text-neutral-900 dark:text-white mb-6 uppercase tracking-tight">{{
        t('valueHabits') }}</h3>
      <div class="h-80 flex items-center justify-center" v-if="!graphData.value || graphData.value.length === 0">
        <p class="text-neutral-400 dark:text-neutral-500 font-medium text-lg">{{ t('noData') }}</p>
      </div>
      <div class="h-80" v-else>
        <canvas id="chart-value"></canvas>
      </div>
    </div>

    <!-- Rating Habits Chart -->
    <div
      class="bg-white dark:bg-neutral-800 rounded-4xl p-8 shadow-lg border border-neutral-100 dark:border-neutral-700">
      <h3 class="text-xl font-black text-neutral-900 dark:text-white mb-6 uppercase tracking-tight">{{
        t('ratingHabits') }}</h3>
      <div class="h-80 flex items-center justify-center" v-if="!graphData.rating || graphData.rating.length === 0">
        <p class="text-neutral-400 dark:text-neutral-500 font-medium text-lg">{{ t('noData') }}</p>
      </div>
      <div class="h-80" v-else>
        <canvas id="chart-rating"></canvas>
      </div>
    </div>
  </div>
</template>
