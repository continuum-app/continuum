<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { useDarkMode } from '../composables/useDarkMode'
import { useLanguage } from '../composables/useLanguage'
import { Download, ArrowLeft, Moon, Sun } from 'lucide-vue-next'

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()
const { t } = useLanguage()

// Export state
const exportStartDate = ref('')
const exportEndDate = ref('')
const isExporting = ref(false)

// Computed property for dynamic years
const quickSelectYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [
    currentYear,
    currentYear - 1,
    currentYear - 2
  ]
})

// Initialize date range
const initializeDateRange = () => {
  const today = new Date()
  const thirtyDaysAgo = new Date(today)
  thirtyDaysAgo.setDate(today.getDate() - 30)

  exportEndDate.value = today.toISOString().split('T')[0]
  exportStartDate.value = thirtyDaysAgo.toISOString().split('T')[0]
}

// Set export date range for a specific year
const setExportYearRange = (year) => {
  exportStartDate.value = `${year}-01-01`
  exportEndDate.value = `${year}-12-31`
}

// Set export date range for all available data
const setAllExportDataRange = async () => {
  try {
    const response = await api.get('habits/date_range/')
    if (response.data.start_date && response.data.end_date) {
      exportStartDate.value = response.data.start_date
      exportEndDate.value = response.data.end_date
    }
  } catch (err) {
    console.error('Failed to fetch date range:', err)
    // Fallback: set to a wide range
    exportStartDate.value = '2020-01-01'
    exportEndDate.value = new Date().toISOString().split('T')[0]
  }
}

// Export data to CSV
const exportToCSV = async () => {
  if (!exportStartDate.value || !exportEndDate.value) {
    alert('Please select a valid date range')
    return
  }

  isExporting.value = true

  try {
    const response = await api.get('habits/export_csv/', {
      params: {
        start_date: exportStartDate.value,
        end_date: exportEndDate.value
      }
    })

    // Create CSV content
    const csvContent = response.data.csv_content

    // Create a blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    link.setAttribute('href', url)
    link.setAttribute('download', `habit_data_${exportStartDate.value}_to_${exportEndDate.value}.csv`)
    link.style.visibility = 'hidden'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (err) {
    console.error('Failed to export data:', err)
    alert('Failed to export data. Please try again.')
  } finally {
    isExporting.value = false
  }
}

const goBack = () => {
  router.push('/dashboard')
}

onMounted(() => {
  initializeDateRange()
})
</script>

<template>
  <div class="min-h-screen bg-[#f8fafc] dark:bg-slate-900 p-6 md:p-12 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-300">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <header class="flex items-center justify-between mb-12">
        <div class="flex items-center gap-4">
          <button @click="goBack" class="flex items-center justify-center w-12 h-12 rounded-full bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700">
            <ArrowLeft :size="20" />
          </button>
          <div>
            <h1 class="text-3xl font-black tracking-tighter text-slate-900 dark:text-white uppercase italic">
              Export Data
            </h1>
            <p class="text-slate-400 dark:text-slate-500 font-medium">Export your habit data to CSV</p>
          </div>
        </div>
        <button @click="toggleDarkMode" class="flex items-center justify-center w-12 h-12 rounded-full bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700">
          <Sun v-if="isDark" :size="20" />
          <Moon v-else :size="20" />
        </button>
      </header>

      <!-- Main Content -->
      <div class="space-y-6">
        <!-- Date Range Selector -->
        <div class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <h2 class="text-2xl font-black text-slate-900 dark:text-white mb-6">Date Range</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Start Date</label>
              <input v-model="exportStartDate" type="date" class="w-full px-4 py-3 rounded-2xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">End Date</label>
              <input v-model="exportEndDate" type="date" class="w-full px-4 py-3 rounded-2xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>

          <!-- Quick Select Buttons -->
          <div class="pt-4 border-t border-slate-100 dark:border-slate-700">
            <p class="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">Quick Select</p>
            <div class="flex flex-wrap gap-2">
              <button v-for="year in quickSelectYears" :key="year" @click="setExportYearRange(year)" class="px-4 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-indigo-500 hover:text-white dark:hover:bg-indigo-600 rounded-full text-sm font-bold transition-colors">
                {{ year }}
              </button>
              <button @click="setAllExportDataRange" class="px-4 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-indigo-500 hover:text-white dark:hover:bg-indigo-600 rounded-full text-sm font-bold transition-colors">
                All Data
              </button>
            </div>
          </div>
        </div>

        <!-- Export Button -->
        <div class="bg-linear-to-r from-indigo-500 to-purple-600 rounded-[3rem] p-8 shadow-lg">
          <div class="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 class="text-xl font-black text-white mb-1">Ready to Export?</h3>
              <p class="text-indigo-100 font-medium">Download your habit data as a CSV file</p>
            </div>
            <button @click="exportToCSV" :disabled="isExporting" class="flex items-center gap-2 px-8 py-4 bg-white text-indigo-600 rounded-2xl font-black hover:bg-indigo-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              <Download :size="20" />
              {{ isExporting ? 'Exporting...' : 'Export CSV' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Add any component-specific styles here */
</style>
