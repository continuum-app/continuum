<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useLanguage } from '@/composables/useLanguage'
import * as LucideIcons from 'lucide-vue-next'
import { RefreshCw } from 'lucide-vue-next'

const { t } = useLanguage()

// Cookie helpers
const COOKIE_NAME = 'summaryDateRange'

const getCookie = (name) => {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? match[2] : null
}

const setCookie = (name, value, days = 365) => {
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  document.cookie = `${name}=${value}; expires=${expires}; path=/`
}

// Date range options
const dateRangeOptions = [
  { key: 'thisWeek', label: t('thisWeek'), tooltip: t('thisWeekTooltip') },
  { key: 'thisMonth', label: t('thisMonth'), tooltip: t('thisMonthTooltip') },
  { key: 'last7Days', label: t('last7Days'), tooltip: t('last7DaysTooltip') },
  { key: 'last30Days', label: t('last30Days'), tooltip: t('last30DaysTooltip') }
]

const validRangeKeys = dateRangeOptions.map(o => o.key)
const savedRange = getCookie(COOKIE_NAME)
const selectedRange = ref(validRangeKeys.includes(savedRange) ? savedRange : 'last30Days')

// Summary state
const summaryData = ref({
  boolean: [],
  counter: [],
  value: [],
  rating: []
})
const isFetchingSummary = ref(false)
const summaryDays = ref(30)

// Get icon component from name
const getIcon = (iconName) => {
  if (!iconName) return LucideIcons.Calendar
  const pascalCase = iconName
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('')
  return LucideIcons[pascalCase] || LucideIcons.Calendar
}

// Calculate date range based on selected option
const getDateRange = () => {
  const endDate = new Date()
  const startDate = new Date()

  switch (selectedRange.value) {
    case 'thisWeek': {
      // Start from Monday of current week
      const day = startDate.getDay()
      const diff = day === 0 ? 6 : day - 1 // Adjust for Sunday
      startDate.setDate(startDate.getDate() - diff)
      break
    }
    case 'thisMonth': {
      // Start from first day of current month
      startDate.setDate(1)
      break
    }
    case 'last7Days': {
      startDate.setDate(startDate.getDate() - 6) // -6 to include today
      break
    }
    case 'last30Days':
    default: {
      startDate.setDate(startDate.getDate() - 29) // -29 to include today
      break
    }
  }

  // Reset time to start of day for startDate
  startDate.setHours(0, 0, 0, 0)

  return { startDate, endDate }
}

// Fetch summary data from API
const fetchSummaryData = async () => {
  isFetchingSummary.value = true
  try {
    const { startDate, endDate } = getDateRange()

    // Calculate number of days in range
    summaryDays.value = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24))

    const response = await api.get('habits/summary/', {
      params: {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0]
      }
    })
    summaryData.value = {
      boolean: response.data.boolean || [],
      counter: response.data.counter || [],
      value: response.data.value || [],
      rating: response.data.rating || []
    }
  } catch (err) {
    console.error('Failed to fetch summary data:', err)
  } finally {
    isFetchingSummary.value = false
  }
}

// Handle date range change
const onRangeChange = (rangeKey) => {
  selectedRange.value = rangeKey
  setCookie(COOKIE_NAME, rangeKey)
  fetchSummaryData()
}

// Expose fetchSummaryData so parent can trigger it when tab becomes active
defineExpose({ fetchSummaryData })

onMounted(() => {
  fetchSummaryData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-linear-to-r from-yellow-600 to-neutral-950 rounded-4xl p-6 shadow-xl">
      <div class="flex justify-between items-center mb-4">
        <div>
          <h2 class="text-3xl font-black text-white mb-2">{{ t('summaryView') }}</h2>
          <p class="text-yellow-100 font-medium">{{ t('retrospectiveAnalysis') }}</p>
        </div>
        <div class="text-right">
          <p class="text-5xl font-black text-white">{{ summaryDays }}</p>
          <p class="text-yellow-100 font-bold uppercase tracking-wide">{{ t('days') }}</p>
        </div>
      </div>
      <!-- Date Range Selector -->
      <div class="flex flex-wrap gap-2">
        <button v-for="option in dateRangeOptions" :key="option.key" @click="onRangeChange(option.key)"
          :title="option.tooltip" :class="[
            'px-4 py-2 rounded-xl font-bold text-sm transition-all',
            selectedRange === option.key
              ? 'bg-white text-yellow-600 shadow-lg'
              : 'bg-yellow-700/50 text-yellow-100 hover:bg-yellow-700'
          ]">
          {{ option.label }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isFetchingSummary" class="flex items-center justify-center py-20">
      <RefreshCw :size="40" class="animate-spin text-primary-500" />
    </div>

    <!-- Summary Content -->
    <div v-else class="space-y-6">
      <!-- Boolean Habits -->
      <div v-if="summaryData.boolean.length > 0">
        <h3
          class="text-2xl font-black text-neutral-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
          <div class="w-2 h-8 bg-blue-500 rounded-full"></div>
          {{ t('booleanHabits') }}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="habit in summaryData.boolean" :key="habit.habit_id"
            class="bg-white dark:bg-neutral-800 rounded-4xl p-6 shadow-lg border border-neutral-100 dark:border-neutral-700 hover:shadow-xl transition-all">
            <div class="flex items-center gap-3 mb-4">
              <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }" stroke-width="2.5" />
              </div>
              <div class="flex-1">
                <h4 class="font-black text-neutral-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                <p v-if="habit.category_name"
                  class="text-xs font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide">
                  {{ habit.category_name }}
                </p>
              </div>
            </div>

            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-neutral-500 dark:text-neutral-400 text-sm font-bold">Completion Rate</span>
                <span class="text-2xl font-black" :style="{ color: habit.color }">
                  {{ habit.metrics.completion_rate }}%
                </span>
              </div>

              <div class="h-2 bg-neutral-100 dark:bg-neutral-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all" :style="{
                  width: habit.metrics.completion_rate + '%',
                  backgroundColor: habit.color
                }"></div>
              </div>

              <div class="grid grid-cols-2 gap-3 pt-2">
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-2xl font-black text-neutral-900 dark:text-white">
                    {{ habit.metrics.total_completions }}
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">{{ t('completed') }}</div>
                </div>
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-2xl font-black text-neutral-900 dark:text-white">
                    {{ habit.metrics.streak }}
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">Day Streak</div>
                </div>
              </div>

              <div class="text-center text-xs text-neutral-400 font-bold">
                Last {{ habit.metrics.days_in_range }} days
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Counter Habits -->
      <div v-if="summaryData.counter.length > 0">
        <h3
          class="text-2xl font-black text-neutral-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
          <div class="w-2 h-8 bg-green-500 rounded-full"></div>
          {{ t('counterHabits') }}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="habit in summaryData.counter" :key="habit.habit_id"
            class="bg-white dark:bg-neutral-800 rounded-4xl p-6 shadow-lg border border-neutral-100 dark:border-neutral-700 hover:shadow-xl transition-all">
            <div class="flex items-center gap-3 mb-4">
              <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }" stroke-width="2.5" />
              </div>
              <div class="flex-1">
                <h4 class="font-black text-neutral-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                <p v-if="habit.category_name"
                  class="text-xs font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide">
                  {{ habit.category_name }}
                </p>
              </div>
            </div>

            <div class="space-y-3">
              <div class="text-center p-4 rounded-2xl" :style="{ backgroundColor: habit.color + '10' }">
                <div class="text-4xl font-black" :style="{ color: habit.color }">
                  {{ habit.metrics.total }}
                </div>
                <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide mt-1">Total Count</div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-xl font-black text-neutral-900 dark:text-white">
                    {{ habit.metrics.average }}
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">Avg/Day</div>
                </div>
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-xl font-black text-neutral-900 dark:text-white">
                    {{ habit.metrics.max }}
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">Best Day</div>
                </div>
              </div>

              <div class="text-center text-xs text-neutral-400 font-bold">
                Tracked {{ habit.metrics.days_tracked }}/{{ habit.metrics.days_in_range }} days
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Value Habits -->
      <div v-if="summaryData.value.length > 0">
        <h3
          class="text-2xl font-black text-neutral-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
          <div class="w-2 h-8 bg-orange-500 rounded-full"></div>
          {{ t('valueHabits') }}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="habit in summaryData.value" :key="habit.habit_id"
            class="bg-white dark:bg-neutral-800 rounded-4xl p-6 shadow-lg border border-neutral-100 dark:border-neutral-700 hover:shadow-xl transition-all">
            <div class="flex items-center gap-3 mb-4">
              <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }" stroke-width="2.5" />
              </div>
              <div class="flex-1">
                <h4 class="font-black text-neutral-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                <p v-if="habit.category_name"
                  class="text-xs font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide">
                  {{ habit.category_name }}
                </p>
              </div>
            </div>

            <div class="space-y-3">
              <div class="text-center p-4 rounded-2xl" :style="{ backgroundColor: habit.color + '10' }">
                <div class="text-4xl font-black" :style="{ color: habit.color }">
                  {{ habit.metrics.total }} {{ habit.metrics.unit || '' }}
                </div>
                <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide mt-1">Total</div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-xl font-black text-neutral-900 dark:text-white">
                    {{ habit.metrics.average }} {{ habit.metrics.unit || '' }}
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">Avg/Day</div>
                </div>
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-xl font-black text-neutral-900 dark:text-white">
                    {{ habit.metrics.max_value }} {{ habit.metrics.unit || '' }}
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">Longest</div>
                </div>
              </div>

              <div class="text-center text-xs text-neutral-400 font-bold">
                Tracked {{ habit.metrics.days_tracked }}/{{ habit.metrics.days_in_range }} days
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Rating Habits -->
      <div v-if="summaryData.rating.length > 0">
        <h3
          class="text-2xl font-black text-neutral-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
          <div class="w-2 h-8 bg-yellow-500 rounded-full"></div>
          {{ t('ratingHabits') }}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="habit in summaryData.rating" :key="habit.habit_id"
            class="bg-white dark:bg-neutral-800 rounded-4xl p-6 shadow-lg border border-neutral-100 dark:border-neutral-700 hover:shadow-xl transition-all">
            <div class="flex items-center gap-3 mb-4">
              <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }" stroke-width="2.5" />
              </div>
              <div class="flex-1">
                <h4 class="font-black text-neutral-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                <p v-if="habit.category_name"
                  class="text-xs font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide">
                  {{ habit.category_name }}
                </p>
              </div>
            </div>

            <div class="space-y-3">
              <div class="text-center p-4 rounded-2xl" :style="{ backgroundColor: habit.color + '10' }">
                <div class="text-4xl font-black" :style="{ color: habit.color }">
                  {{ habit.metrics.average }}/{{ habit.metrics.max_value }}
                </div>
                <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide mt-1">Average Rating</div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-xl font-black text-green-600 dark:text-green-400">
                    {{ habit.metrics.max }}★
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">Best</div>
                </div>
                <div class="text-center p-3 bg-neutral-50 dark:bg-neutral-700 rounded-xl">
                  <div class="text-xl font-black text-red-600 dark:text-red-400">
                    {{ habit.metrics.min }}★
                  </div>
                  <div class="text-xs font-bold text-neutral-400 uppercase tracking-wide">Lowest</div>
                </div>
              </div>

              <div class="text-center text-xs text-neutral-400 font-bold">
                Tracked {{ habit.metrics.days_tracked }}/{{ habit.metrics.days_in_range }} days
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-if="summaryData.boolean.length === 0 && summaryData.counter.length === 0 && summaryData.value.length === 0 && summaryData.rating.length === 0"
        class="bg-white dark:bg-neutral-800 rounded-4xl p-16 shadow-lg border border-neutral-100 dark:border-neutral-700 text-center">
        <div class="text-6xl mb-4">📊</div>
        <h3 class="text-2xl font-black text-neutral-900 dark:text-white mb-2">{{ t('noHabitsYet') }}</h3>
        <p class="text-neutral-500 dark:text-neutral-400">{{ t('startTracking') }}
        </p>
      </div>
    </div>
  </div>
</template>
