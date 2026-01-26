<script setup>
import { ref, onMounted, computed, nextTick, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import authService from '@/services/auth'
import { useDarkMode } from '@/composables/useDarkMode'
import { useLanguage } from '@/composables/useLanguage'
import { useHabits } from '@/composables/useHabits'
import { useCategories } from '@/composables/useCategories'
import * as LucideIcons from 'lucide-vue-next'
import { Plus, X, ChevronDown, RefreshCw, Moon, Sun, BarChart3, FileText, Download, Calendar, Settings, Languages, Check, User, LogOut } from 'lucide-vue-next'
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'
import IconPicker from '@/components/IconPicker.vue'
import TrackingTab from '@/components/TrackingTab.vue'
import ProfileTab from '@/components/ProfileTab.vue'

// Register Chart.js components
Chart.register(...registerables)

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()
const { currentLanguage, setLanguage, languages, currentLanguageInfo, t } = useLanguage()
const { addHabit: addHabitApi } = useHabits()
const { categories } = useCategories()

// Language dropdown state
const isLanguageDropdownOpen = ref(false)

// --- STATE ---
const isModalOpen = ref(false)
const activeTab = ref('tracking')

// Form Refs for New Habit
const newHabitName = ref('')
const newHabitType = ref('boolean')
const newHabitIcon = ref('calendar')
const newHabitColor = ref('#1F85DE')
const newHabitCategoryId = ref(null)
const newHabitMaxValue = ref(5)

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

// Summary state
const summaryData = ref({
  boolean: [],
  counter: [],
  value: [],
  rating: []
})
const isFetchingSummary = ref(false)
const summaryDays = ref(30)


// Computed property for dynamic years
const quickSelectYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [
    currentYear,
    currentYear - 1,
    currentYear - 2
  ]
})


// --- LOGIC ---
// --- LOGIC ---

const handleLogout = () => {
  authService.logout()
  router.push('/login')
}

const goToAdminSettings = () => {
  router.push('/admin-settings')
}

const goToExport = () => {
  router.push('/export')
}

// Handle new habit form submission
const addHabit = async () => {
  try {
    await addHabitApi({
      name: newHabitName.value,
      habit_type: newHabitType.value,
      icon: newHabitIcon.value,
      color: newHabitColor.value,
      category: newHabitCategoryId.value,
      max_value: newHabitType.value === 'rating' ? newHabitMaxValue.value : null
    })
    // Reset form and close modal
    newHabitName.value = ''
    newHabitType.value = 'boolean'
    newHabitIcon.value = 'calendar'
    newHabitColor.value = '#1F85DE'
    newHabitCategoryId.value = null
    newHabitMaxValue.value = 5
    isModalOpen.value = false
  } catch (err) {
    console.error('Failed to add habit:', err)
  }
}

const selectLanguage = (langCode) => {
  setLanguage(langCode)
  isLanguageDropdownOpen.value = false
}

// Close dropdown when clicking outside
const closeLanguageDropdown = (event) => {
  if (!event.target.closest('.language-dropdown-container')) {
    isLanguageDropdownOpen.value = false
  }
}

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

// Fetch summary data from API (last 30 days)
const fetchSummaryData = async () => {
  isFetchingSummary.value = true
  try {
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - 30)

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

// Get icon component from name
const getIcon = (iconName) => {
  if (!iconName) return LucideIcons.Calendar
  const pascalCase = iconName
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('')
  return LucideIcons[pascalCase] || LucideIcons.Calendar
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
              color: isDark.value ? '#cbd5e1' : '#334155',
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
            backgroundColor: isDark.value ? '#1e293b' : '#ffffff',
            titleColor: isDark.value ? '#f1f5f9' : '#0f172a',
            bodyColor: isDark.value ? '#cbd5e1' : '#475569',
            borderColor: isDark.value ? '#334155' : '#e2e8f0',
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
              color: isDark.value ? '#334155' : '#e2e8f0'
            },
            ticks: {
              color: isDark.value ? '#94a3b8' : '#64748b',
              font: {
                weight: '600'
              }
            }
          },
          y: {
            beginAtZero: true,
            grace: '5%',
            grid: {
              color: isDark.value ? '#334155' : '#e2e8f0'
            },
            ticks: {
              color: isDark.value ? '#94a3b8' : '#64748b',
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
  if (activeTab.value === 'graph') {
    fetchGraphData()
  }
})

// Watch for dark mode changes to update charts
watch(isDark, async () => {
  if (activeTab.value === 'graph') {
    await renderCharts()
  }
})

// Watch for tab changes
watch(activeTab, (newTab) => {
  if (newTab === 'graph') {
    if (!graphStartDate.value || !graphEndDate.value) {
      initializeDateRange()
    }
    fetchGraphData()
  } else if (newTab === 'summary') {
    fetchSummaryData()
    fetchInsightsData()
  }
})

onMounted(() => {
  initializeDateRange()
  document.addEventListener('click', closeLanguageDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeLanguageDropdown)
})

// Insights state
const insightsData = ref([])
const isFetchingInsights = ref(false)

// Fetch insights data
const fetchInsightsData = async () => {
  isFetchingInsights.value = true
  try {
    // NEW ENDPOINT: /api/correlations/ instead of /api/habits/insights/
    const response = await api.get('correlations/', {
      params: {
        limit: 5,
        min_correlation: 0.5
      }
    })
    insightsData.value = response.data.insights
  } catch (err) {
    console.error('Failed to fetch insights:', err)
  } finally {
    isFetchingInsights.value = false
  }
}

// Helper function to get correlation badge color
const getCorrelationBadgeColor = (strength) => {
  const colors = {
    'very_strong': 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300',
    'strong': 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    'moderate': 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
    'weak': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300',
    'very_weak': 'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300'
  }
  return colors[strength] || colors['moderate']
}

// Helper function to get strength label
const getStrengthLabel = (strength) => {
  const labels = {
    'very_strong': 'Very Strong',
    'strong': 'Strong',
    'moderate': 'Moderate',
    'weak': 'Weak',
    'very_weak': 'Very Weak'
  }
  return labels[strength] || 'Moderate'
}
</script>

<template>
  <div
    class="min-h-screen bg-[#f8fafc] dark:bg-slate-900 p-6 md:p-12 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-300">
    <div class="max-w-7xl mx-auto">

      <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
        <div class="flex items-center gap-4">
          <img src="/logo.svg" alt="App Logo" class="h-14 w-14" />
          <div>
            <h1 class="text-4xl font-black tracking-tighter text-slate-900 dark:text-white uppercase italic">
              {{ t('appName') }}
            </h1>
            <p class="text-slate-400 dark:text-slate-500 font-medium">{{ t('tagline') }}</p>
          </div>
        </div>
        <div class="flex gap-4">
          <!-- Language Selector -->
          <div class="relative language-dropdown-container">
            <button @click="isLanguageDropdownOpen = !isLanguageDropdownOpen"
              class="bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 px-6 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-slate-300 dark:hover:bg-slate-600 transition-all shadow-md active:scale-95">
              <Languages :size="20" stroke-width="2.5" />
              <span class="text-xl">{{ currentLanguageInfo.flag }}</span>
              <ChevronDown :size="16" stroke-width="2.5" :class="{ 'rotate-180': isLanguageDropdownOpen }"
                class="transition-transform" />
            </button>

            <!-- Language Dropdown -->
            <Transition name="dropdown">
              <div v-if="isLanguageDropdownOpen"
                class="absolute top-full mt-2 right-0 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 py-2 min-w-50 z-50">
                <button v-for="lang in languages" :key="lang.code" @click="selectLanguage(lang.code)"
                  class="w-full px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors flex items-center gap-3 text-left">
                  <span class="text-xl">{{ lang.flag }}</span>
                  <span class="font-bold text-slate-900 dark:text-white">{{ lang.name }}</span>
                  <Check v-if="currentLanguage === lang.code" :size="16"
                    class="ml-auto text-indigo-600 dark:text-indigo-400" stroke-width="3" />
                </button>
              </div>
            </Transition>
          </div>

          <!-- Dark Mode Toggle -->
          <button @click="toggleDarkMode"
            class="bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-yellow-400 px-6 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-slate-300 dark:hover:bg-slate-600 transition-all shadow-md active:scale-95">
            <Moon v-if="!isDark" :size="20" stroke-width="2.5" />
            <Sun v-else :size="20" stroke-width="2.5" />
          </button>

          <button @click="isModalOpen = true"
            class="bg-indigo-500 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-indigo-600 transition-all shadow-md active:scale-95">
            <Plus :size="20" stroke-width="3" /> {{ t('newHabit') }}
          </button>

          <button @click="handleLogout"
            class="bg-red-600 text-white px-6 py-4 rounded-2xl font-bold hover:bg-red-700 transition-all shadow-md active:scale-95">
            <LogOut :size="20" stroke-width="2.5" />
          </button>
        </div>
      </header>

      <!-- Tabs Navigation -->
      <div class="mb-12">
        <div
          class="flex gap-2 p-2 bg-white dark:bg-slate-800 rounded-3xl shadow-md border border-slate-100 dark:border-slate-700">
          <button @click="activeTab = 'tracking'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'tracking'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
          ]">
            <Calendar :size="20" stroke-width="2.5" />
            <span>{{ t('tracking') }}</span>
          </button>

          <button @click="activeTab = 'summary'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'summary'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
          ]">
            <FileText :size="20" stroke-width="2.5" />
            <span>{{ t('summary') }}</span>
          </button>

          <button @click="activeTab = 'graph'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'graph'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
          ]">
            <BarChart3 :size="20" stroke-width="2.5" />
            <span>{{ t('graph') }}</span>
          </button>

          <button @click="activeTab = 'profile'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'profile'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
          ]">
            <User :size="20" stroke-width="2.5" />
            <span>{{ t('profile') }}</span>
          </button>
        </div>
      </div>

      <!-- Tab Content -->

      <!-- Tracking Tab -->
      <TrackingTab v-show="activeTab === 'tracking'" />

      <!-- Summary Tab -->
      <div v-show="activeTab === 'summary'" class="space-y-6">
        <!-- Header -->
        <div
          class="bg-linear-to-r from-indigo-500 to-purple-600 rounded-[3rem] p-12 shadow-xl flex justify-between items-center">
          <div>
            <h2 class="text-3xl font-black text-white mb-2">{{ t('summaryView') }}</h2>
            <p class="text-indigo-100 font-medium">{{ t('retrospectiveAnalysis') }}</p>
          </div>
          <div class="text-right">
            <p class="text-5xl font-black text-white">{{ summaryDays }}</p>
            <p class="text-indigo-100 font-bold uppercase tracking-wide">{{ t('days') }}</p>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isFetchingSummary" class="flex items-center justify-center py-20">
          <RefreshCw :size="40" class="animate-spin text-indigo-500" />
        </div>

        <!-- Summary Content -->
        <div v-else class="space-y-6">
          <!-- Boolean Habits -->
          <div v-if="summaryData.boolean.length > 0">
            <h3
              class="text-2xl font-black text-slate-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
              <div class="w-2 h-8 bg-blue-500 rounded-full"></div>
              {{ t('booleanHabits') }}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div v-for="habit in summaryData.boolean" :key="habit.habit_id"
                class="bg-white dark:bg-slate-800 rounded-4xl p-6 shadow-lg border border-slate-100 dark:border-slate-700 hover:shadow-xl transition-all">
                <div class="flex items-center gap-3 mb-4">
                  <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                    <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }"
                      stroke-width="2.5" />
                  </div>
                  <div class="flex-1">
                    <h4 class="font-black text-slate-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                    <p v-if="habit.category_name"
                      class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide">
                      {{ habit.category_name }}
                    </p>
                  </div>
                </div>

                <div class="space-y-3">
                  <div class="flex justify-between items-center">
                    <span class="text-slate-500 dark:text-slate-400 text-sm font-bold">Completion Rate</span>
                    <span class="text-2xl font-black" :style="{ color: habit.color }">
                      {{ habit.metrics.completion_rate }}%
                    </span>
                  </div>

                  <div class="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all" :style="{
                      width: habit.metrics.completion_rate + '%',
                      backgroundColor: habit.color
                    }"></div>
                  </div>

                  <div class="grid grid-cols-2 gap-3 pt-2">
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-2xl font-black text-slate-900 dark:text-white">
                        {{ habit.metrics.total_completions }}
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">{{ t('completed') }}</div>
                    </div>
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-2xl font-black text-slate-900 dark:text-white">
                        {{ habit.metrics.streak }}
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">Day Streak</div>
                    </div>
                  </div>

                  <div class="text-center text-xs text-slate-400 font-bold">
                    Last {{ habit.metrics.days_in_range }} days
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Counter Habits -->
          <div v-if="summaryData.counter.length > 0">
            <h3
              class="text-2xl font-black text-slate-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
              <div class="w-2 h-8 bg-green-500 rounded-full"></div>
              {{ t('counterHabits') }}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div v-for="habit in summaryData.counter" :key="habit.habit_id"
                class="bg-white dark:bg-slate-800 rounded-4xl p-6 shadow-lg border border-slate-100 dark:border-slate-700 hover:shadow-xl transition-all">
                <div class="flex items-center gap-3 mb-4">
                  <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                    <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }"
                      stroke-width="2.5" />
                  </div>
                  <div class="flex-1">
                    <h4 class="font-black text-slate-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                    <p v-if="habit.category_name"
                      class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide">
                      {{ habit.category_name }}
                    </p>
                  </div>
                </div>

                <div class="space-y-3">
                  <div class="text-center p-4 rounded-2xl" :style="{ backgroundColor: habit.color + '10' }">
                    <div class="text-4xl font-black" :style="{ color: habit.color }">
                      {{ habit.metrics.total }}
                    </div>
                    <div class="text-xs font-bold text-slate-400 uppercase tracking-wide mt-1">Total Count</div>
                  </div>

                  <div class="grid grid-cols-2 gap-3">
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-xl font-black text-slate-900 dark:text-white">
                        {{ habit.metrics.average }}
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">Avg/Day</div>
                    </div>
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-xl font-black text-slate-900 dark:text-white">
                        {{ habit.metrics.max }}
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">Best Day</div>
                    </div>
                  </div>

                  <div class="text-center text-xs text-slate-400 font-bold">
                    Tracked {{ habit.metrics.days_tracked }}/{{ habit.metrics.days_in_range }} days
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Value Habits -->
          <div v-if="summaryData.value.length > 0">
            <h3
              class="text-2xl font-black text-slate-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
              <div class="w-2 h-8 bg-orange-500 rounded-full"></div>
              {{ t('valueHabits') }}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div v-for="habit in summaryData.value" :key="habit.habit_id"
                class="bg-white dark:bg-slate-800 rounded-4xl p-6 shadow-lg border border-slate-100 dark:border-slate-700 hover:shadow-xl transition-all">
                <div class="flex items-center gap-3 mb-4">
                  <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                    <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }"
                      stroke-width="2.5" />
                  </div>
                  <div class="flex-1">
                    <h4 class="font-black text-slate-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                    <p v-if="habit.category_name"
                      class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide">
                      {{ habit.category_name }}
                    </p>
                  </div>
                </div>

                <div class="space-y-3">
                  <div class="text-center p-4 rounded-2xl" :style="{ backgroundColor: habit.color + '10' }">
                    <div class="text-4xl font-black" :style="{ color: habit.color }">
                      {{ habit.metrics.total }} {{ habit.metrics.unit || '' }}
                    </div>
                    <div class="text-xs font-bold text-slate-400 uppercase tracking-wide mt-1">Total</div>
                  </div>

                  <div class="grid grid-cols-2 gap-3">
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-xl font-black text-slate-900 dark:text-white">
                        {{ habit.metrics.average }} {{ habit.metrics.unit || '' }}
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">Avg/Day</div>
                    </div>
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-xl font-black text-slate-900 dark:text-white">
                        {{ habit.metrics.max_value }} {{ habit.metrics.unit || '' }}
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">Longest</div>
                    </div>
                  </div>

                  <div class="text-center text-xs text-slate-400 font-bold">
                    Tracked {{ habit.metrics.days_tracked }}/{{ habit.metrics.days_in_range }} days
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Rating Habits -->
          <div v-if="summaryData.rating.length > 0">
            <h3
              class="text-2xl font-black text-slate-900 dark:text-white mb-4 uppercase tracking-tight flex items-center gap-3">
              <div class="w-2 h-8 bg-yellow-500 rounded-full"></div>
              {{ t('ratingHabits') }}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div v-for="habit in summaryData.rating" :key="habit.habit_id"
                class="bg-white dark:bg-slate-800 rounded-4xl p-6 shadow-lg border border-slate-100 dark:border-slate-700 hover:shadow-xl transition-all">
                <div class="flex items-center gap-3 mb-4">
                  <div class="p-3 rounded-2xl" :style="{ backgroundColor: habit.color + '20' }">
                    <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }"
                      stroke-width="2.5" />
                  </div>
                  <div class="flex-1">
                    <h4 class="font-black text-slate-900 dark:text-white text-lg">{{ habit.habit_name }}</h4>
                    <p v-if="habit.category_name"
                      class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide">
                      {{ habit.category_name }}
                    </p>
                  </div>
                </div>

                <div class="space-y-3">
                  <div class="text-center p-4 rounded-2xl" :style="{ backgroundColor: habit.color + '10' }">
                    <div class="text-4xl font-black" :style="{ color: habit.color }">
                      {{ habit.metrics.average }}/{{ habit.metrics.max_value }}
                    </div>
                    <div class="text-xs font-bold text-slate-400 uppercase tracking-wide mt-1">Average Rating</div>
                  </div>

                  <div class="grid grid-cols-2 gap-3">
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-xl font-black text-green-600 dark:text-green-400">
                        {{ habit.metrics.max }}★
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">Best</div>
                    </div>
                    <div class="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                      <div class="text-xl font-black text-red-600 dark:text-red-400">
                        {{ habit.metrics.min }}★
                      </div>
                      <div class="text-xs font-bold text-slate-400 uppercase tracking-wide">Lowest</div>
                    </div>
                  </div>

                  <div class="text-center text-xs text-slate-400 font-bold">
                    Tracked {{ habit.metrics.days_tracked }}/{{ habit.metrics.days_in_range }} days
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Insights Section -->
          <div
            v-if="!isFetchingSummary && (summaryData.boolean.length > 0 || summaryData.counter.length > 0 || summaryData.value.length > 0 || summaryData.rating.length > 0)"
            class="mt-12">
            <!-- Insights Header -->
            <div class="bg-linear-to-r from-indigo-500 to-purple-600 rounded-[3rem] p-12 shadow-xl mb-6">
              <h2 class="text-3xl font-black text-white mb-2">{{ t('insights') }}</h2>
              <p class="text-indigo-100 font-medium">{{ t('discoverCorrelations') }}</p>
            </div>

            <!-- Loading State for Insights -->
            <div v-if="isFetchingInsights" class="flex items-center justify-center py-20">
              <div class="text-center">
                <RefreshCw :size="40" class="animate-spin text-indigo-500 mx-auto mb-4" />
                <p class="text-slate-600 dark:text-slate-400 font-bold">{{ t('loading') }}</p>
              </div>
            </div>

            <!-- Insights Content -->
            <div v-else-if="insightsData.length > 0" class="space-y-6">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div v-for="(insight, index) in insightsData" :key="index"
                  class="bg-white dark:bg-slate-800 rounded-4xl p-8 shadow-lg border border-slate-100 dark:border-slate-700 hover:shadow-xl transition-all">

                  <!-- Correlation Badge -->
                  <div class="flex items-center justify-between mb-6">
                    <span :class="getCorrelationBadgeColor(insight.strength)"
                      class="px-4 py-2 rounded-full text-xs font-black uppercase tracking-wider">
                      {{ getStrengthLabel(insight.strength) }}
                    </span>
                    <span class="text-3xl font-black text-indigo-600 dark:text-indigo-400">
                      {{ (insight.correlation * 100).toFixed(0) }}%
                    </span>
                  </div>

                  <!-- Habit Pair Display -->
                  <div class="space-y-4 mb-6">
                    <!-- Habit 1 -->
                    <div class="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
                      <div class="p-3 rounded-xl" :style="{ backgroundColor: insight.habit1.color + '20' }">
                        <component :is="getIcon(insight.habit1.icon)" :size="24"
                          :style="{ color: insight.habit1.color }" stroke-width="2.5" />
                      </div>
                      <div class="flex-1">
                        <h4 class="font-black text-slate-900 dark:text-white text-lg">
                          {{ insight.habit1.name }}
                        </h4>
                        <p v-if="insight.habit1.category"
                          class="text-xs font-bold text-slate-400 uppercase tracking-wide">
                          {{ insight.habit1.category }}
                        </p>
                      </div>
                    </div>

                    <!-- Connection Arrow -->
                    <div class="flex justify-center">
                      <div class="bg-linear-to-r from-indigo-500 to-purple-600 text-white p-3 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                          stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                          <line x1="12" y1="5" x2="12" y2="19"></line>
                          <polyline points="19 12 12 19 5 12"></polyline>
                        </svg>
                      </div>
                    </div>

                    <!-- Habit 2 -->
                    <div class="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
                      <div class="p-3 rounded-xl" :style="{ backgroundColor: insight.habit2.color + '20' }">
                        <component :is="getIcon(insight.habit2.icon)" :size="24"
                          :style="{ color: insight.habit2.color }" stroke-width="2.5" />
                      </div>
                      <div class="flex-1">
                        <h4 class="font-black text-slate-900 dark:text-white text-lg">
                          {{ insight.habit2.name }}
                        </h4>
                        <p v-if="insight.habit2.category"
                          class="text-xs font-bold text-slate-400 uppercase tracking-wide">
                          {{ insight.habit2.category }}
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Description -->
                  <div
                    class="p-4 bg-linear-to-r from-indigo-50 to-purple-50 dark:from-indigo-950 dark:to-purple-950 rounded-2xl">
                    <p class="text-sm font-bold text-slate-700 dark:text-slate-300 leading-relaxed">
                      {{ insight.description }}
                    </p>
                  </div>

                  <!-- Stats Footer -->
                  <div
                    class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700 flex justify-between items-center">
                    <span class="text-xs font-bold text-slate-400">
                      Based on {{ insight.sample_size }} days
                    </span>
                    <span class="text-xs font-bold text-slate-400">
                      {{ new Date(insight.start_date).toLocaleDateString() }} -
                      {{ new Date(insight.end_date).toLocaleDateString() }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- No Insights State -->
            <div v-else
              class="bg-white dark:bg-slate-800 rounded-[3rem] p-16 shadow-lg border border-slate-100 dark:border-slate-700 text-center">
              <div class="text-6xl mb-4">🔍</div>
              <h3 class="text-2xl font-black text-slate-900 dark:text-white mb-2">
                {{ t('noInsightsYet') }}
              </h3>
              <p class="text-slate-500 dark:text-slate-400">
                {{ t('computeCorrelations') }}
              </p>
            </div>
          </div>

          <!-- Empty State -->
          <div
            v-if="summaryData.boolean.length === 0 && summaryData.counter.length === 0 && summaryData.value.length === 0 && summaryData.rating.length === 0"
            class="bg-white dark:bg-slate-800 rounded-[3rem] p-16 shadow-lg border border-slate-100 dark:border-slate-700 text-center">
            <div class="text-6xl mb-4">📊</div>
            <h3 class="text-2xl font-black text-slate-900 dark:text-white mb-2">{{ t('noHabitsYet') }}</h3>
            <p class="text-slate-500 dark:text-slate-400">{{ t('startTracking') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Graph Tab -->
      <div v-show="activeTab === 'graph'" class="space-y-6">
        <!-- Date Range Selector -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <h2 class="text-2xl font-black text-slate-900 dark:text-white mb-6">{{ t('dateRange') }}</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div class="space-y-2">
              <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('startDate')
              }}</label>
              <input v-model="graphStartDate" type="date"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-slate-900 dark:text-white" />
            </div>
            <div class="space-y-2">
              <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('endDate') }}</label>
              <input v-model="graphEndDate" type="date"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-slate-900 dark:text-white" />
            </div>
          </div>

          <!-- Quick Select Buttons -->
          <div class="pt-4 border-t border-slate-100 dark:border-slate-700">
            <p class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-3">Quick Select</p>
            <div class="flex gap-3 flex-wrap">
              <button @click="setAllDataRange"
                class="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 transition-all shadow-sm active:scale-95">
                All
              </button>
              <button v-for="year in quickSelectYears" :key="year" @click="setYearRange(year)"
                class="px-6 py-2.5 bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white rounded-xl font-bold text-sm hover:bg-slate-200 dark:hover:bg-slate-600 transition-all shadow-sm active:scale-95">
                {{ year }}
              </button>
            </div>
          </div>
        </div>

        <!-- Boolean Habits Chart -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <h3 class="text-xl font-black text-slate-900 dark:text-white mb-6 uppercase tracking-tight">{{
            t('booleanHabits') }}
          </h3>
          <div class="h-80 flex items-center justify-center"
            v-if="!graphData.boolean || graphData.boolean.length === 0">
            <p class="text-slate-400 dark:text-slate-500 font-medium text-lg">{{ t('noData') }}</p>
          </div>
          <div class="h-80" v-else>
            <canvas id="chart-boolean"></canvas>
          </div>
        </div>

        <!-- Counter Habits Chart -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <h3 class="text-xl font-black text-slate-900 dark:text-white mb-6 uppercase tracking-tight">{{
            t('counterHabits') }}
          </h3>
          <div class="h-80 flex items-center justify-center"
            v-if="!graphData.counter || graphData.counter.length === 0">
            <p class="text-slate-400 dark:text-slate-500 font-medium text-lg">{{ t('noData') }}</p>
          </div>
          <div class="h-80" v-else>
            <canvas id="chart-counter"></canvas>
          </div>
        </div>

        <!-- Value Habits Chart -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <h3 class="text-xl font-black text-slate-900 dark:text-white mb-6 uppercase tracking-tight">{{
            t('valueHabits') }}</h3>
          <div class="h-80 flex items-center justify-center" v-if="!graphData.value || graphData.value.length === 0">
            <p class="text-slate-400 dark:text-slate-500 font-medium text-lg">{{ t('noData') }}</p>
          </div>
          <div class="h-80" v-else>
            <canvas id="chart-value"></canvas>
          </div>
        </div>

        <!-- Rating Habits Chart -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <h3 class="text-xl font-black text-slate-900 dark:text-white mb-6 uppercase tracking-tight">{{
            t('ratingHabits') }}</h3>
          <div class="h-80 flex items-center justify-center" v-if="!graphData.rating || graphData.rating.length === 0">
            <p class="text-slate-400 dark:text-slate-500 font-medium text-lg">{{ t('noData') }}</p>
          </div>
          <div class="h-80" v-else>
            <canvas id="chart-rating"></canvas>
          </div>
        </div>
      </div>

      <!-- Profile Tab -->
      <ProfileTab v-show="activeTab === 'profile'" />
    </div>

    <!-- Footer -->
    <footer class="max-w-7xl mx-auto mt-16 pt-8 pb-6 border-t border-slate-200 dark:border-slate-700">
      <div class="flex flex-col md:flex-row justify-between items-center gap-6">
        <!-- GitHub Link -->
        <div class="flex items-center gap-3">
          <a href="https://github.com/habitsfactory/habitsfactory-app" target="_blank" rel="noopener noreferrer"
            class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors font-medium flex items-center gap-2 group">
            <svg class="w-5 h-5 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
              <path fill-rule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                clip-rule="evenodd" />
            </svg>
            <span class="text-sm font-bold">{{ t('viewOnGithub') }}</span>
          </a>
        </div>

        <!-- Admin Settings Button -->
        <button @click="goToAdminSettings"
          class="flex items-center gap-2 px-6 py-3 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-200 dark:hover:bg-slate-600 transition-all shadow-sm active:scale-95">
          <Settings :size="18" stroke-width="2.5" />
          <span class="text-sm">{{ t('adminSettings') }}</span>
        </button>

        <!-- Export Button -->
        <button @click="goToExport"
          class="flex items-center gap-2 px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-bold transition-all shadow-sm active:scale-95">
          <Download :size="18" stroke-width="2.5" />
          <span class="text-sm">{{ t('export') }}</span>
        </button>
      </div>

      <!-- Copyright -->
      <div class="text-center mt-6">
        <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">
          © {{ new Date().getFullYear() }} {{ t('appName') }}. {{ t('allRightsReserved') }}
        </p>
      </div>
    </footer>

    <!-- Modal for New Habit -->
    <Transition name="fade">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-md" @click="isModalOpen = false"></div>
        <div
          class="relative bg-white dark:bg-slate-800 w-full max-w-lg rounded-[3rem] p-12 shadow-2xl overflow-visible">
          <div class="absolute top-0 left-0 right-0 h-2 bg-indigo-500 rounded-t-[3rem]"></div>

          <div class="flex justify-between items-center mb-10">
            <h2 class="text-3xl font-black text-slate-900 dark:text-white">{{ t('newHabit') }}</h2>
            <button @click="isModalOpen = false"
              class="text-slate-300 hover:text-slate-900 dark:hover:text-white transition">
              <X :size="32" />
            </button>
          </div>

          <form @submit.prevent="addHabit" class="space-y-8">
            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('objectiveName')
              }}</label>
              <input v-model="newHabitName" type="text" placeholder="e.g. Daily Sprints" required
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white">
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('metricType')
              }}</label>
              <select v-model="newHabitType"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 font-bold outline-none appearance-none text-slate-900 dark:text-white">
                <option value="boolean">{{ t('boolean') }}</option>
                <option value="counter">{{ t('counter') }}</option>
                <option value="value">{{ t('value') }}</option>
                <option value="rating">{{ t('rating') }}</option>
              </select>
            </div>

            <IconPicker v-model="newHabitIcon" :label="t('visualIcon')" />

            <!-- Max Value for Rating -->
            <div v-if="newHabitType === 'rating'" class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">
                {{ t('numberOfStars') }}
              </label>
              <input v-model.number="newHabitMaxValue" type="number" min="1" max="10" placeholder="5"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white">
              <p class="text-xs text-slate-400 ml-2">
                Between 1-10 stars
              </p>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('category')
              }}</label>
              <select v-model="newHabitCategoryId"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 font-bold outline-none appearance-none text-slate-900 dark:text-white">
                <option :value="null">{{ t('uncategorized') }}</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('identityColor')
              }}</label>
              <div class="flex items-center gap-4 bg-slate-50 dark:bg-slate-700 p-4 rounded-3xl">
                <input v-model="newHabitColor" type="color"
                  class="w-16 h-12 rounded-xl border-none bg-transparent cursor-pointer">
                <span class="font-mono font-bold text-slate-400">{{ newHabitColor }}</span>
              </div>
            </div>

            <button type="submit"
              class="w-full bg-indigo-600 text-white py-6 rounded-4xl font-black text-xl hover:bg-indigo-700 transition-all shadow-xl">
              {{ t('initiateHabit') }}
            </button>
          </form>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.dropdown-enter-active {
  transition: all 0.2s ease;
}

.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.category-group {
  user-select: none;
}
</style>