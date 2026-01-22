<script setup>
import { ref, onMounted, computed, nextTick, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import authService from '../services/auth'
import { useDarkMode } from '../composables/useDarkMode'
import { useLanguage } from '../composables/useLanguage'
import * as LucideIcons from 'lucide-vue-next'
import { Plus, X, ChevronDown, CheckCircle2, RefreshCw, Save, Star, Moon, Sun, GripVertical, BarChart3, FileText, Download, Calendar, Settings, Languages, Check, User, ArrowLeft, Trash2, Mail, Lock, Database } from 'lucide-vue-next'
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'
import IconPicker from '../components/IconPicker.vue'

// Register Chart.js components
Chart.register(...registerables)

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()
const { currentLanguage, setLanguage, languages, currentLanguageInfo, t } = useLanguage()

// Language dropdown state
const isLanguageDropdownOpen = ref(false)

// --- STATE ---
const habits = ref([])
const categories = ref([])
const isModalOpen = ref(false)
const draggedCategoryId = ref(null)
const dragOverCategoryId = ref(null)
const categoryOrder = ref([]) // Array of category IDs in order
const activeTab = ref('tracking') // New: active tab state

// Date navigation for tracking
const currentTrackingDate = ref(new Date())
const isLoadingHabits = ref(false)
const isCardView = ref(true) // Toggle between card and row view

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

// Profile state
const userInfo = ref({
  username: '',
  email: '',
  is_staff: false,
  is_superuser: false
})
const profileData = ref({
  email: '',
  current_password: ''
})
const newPassword = ref('')
const confirmPassword = ref('')
const isSavingCategory = ref(false)
const isDeletingCategory = ref(null)
const isSavingProfile = ref(false)
const profileSaved = ref(false)
const passwordUpdateSuccess = ref(false)
const newCategoryName = ref('')
const editingCategory = ref(null)
const editingHabit = ref(null)
const editingHabitData = ref({
  name: '',
  icon: '',
  color: '',
  habit_type: '',
  max_value: 5,
  unit: ''
})
const isSavingHabit = ref(false)

// Computed property for dynamic years
const quickSelectYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [
    currentYear,
    currentYear - 1,
    currentYear - 2
  ]
})

// Computed property for formatted tracking date
const formattedTrackingDate = computed(() => {
  const date = currentTrackingDate.value
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const trackingDay = new Date(date)
  trackingDay.setHours(0, 0, 0, 0)

  if (trackingDay.getTime() === today.getTime()) {
    return t('today')
  }

  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  if (trackingDay.getTime() === yesterday.getTime()) {
    return 'Yesterday'
  }

  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  if (trackingDay.getTime() === tomorrow.getTime()) {
    return 'Tomorrow'
  }

  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

// Check if we can navigate to next day (can't go into future)
const canGoToNextDay = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const trackingDay = new Date(currentTrackingDate.value)
  trackingDay.setHours(0, 0, 0, 0)
  return trackingDay.getTime() < today.getTime()
})

// Get tracking date in YYYY-MM-DD format
const trackingDateString = computed(() => {
  const date = currentTrackingDate.value
  return date.toISOString().split('T')[0]
})

// --- COMPUTED ---
const groupedHabits = computed(() => {
  console.log('🔍 Computing groupedHabits...')
  console.log('  - Habits:', habits.value.length)
  console.log('  - Categories:', categories.value.length)
  console.log('  - Category Order:', categoryOrder.value)

  const groups = []

  // If no habits at all, return empty
  if (habits.value.length === 0) {
    console.log('  ❌ No habits, returning empty')
    return groups
  }

  // Create a map of categories by ID for quick lookup
  const categoryMap = new Map()
  categories.value.forEach(cat => {
    categoryMap.set(cat.id, cat)
  })

  console.log('  - Category Map:', Array.from(categoryMap.keys()))

  // Check if uncategorized habits exist
  const uncategorized = habits.value.filter(h => !h.category || h.category === null)
  const hasUncategorized = uncategorized.length > 0

  console.log('  - Uncategorized habits:', uncategorized.length)

  // Build ordered list based on categoryOrder
  let orderedCategoryIds

  if (categoryOrder.value && categoryOrder.value.length > 0) {
    // Use existing order
    orderedCategoryIds = [...categoryOrder.value]
    console.log('  - Using saved order:', orderedCategoryIds)
  } else {
    // Create default order: uncategorized first (if exists), then categories
    orderedCategoryIds = hasUncategorized
      ? ['uncategorized', ...categories.value.map(c => c.id)]
      : categories.value.map(c => c.id)
    console.log('  - Creating default order:', orderedCategoryIds)
  }

  // Add groups in order (including uncategorized)
  orderedCategoryIds.forEach(id => {
    if (id === 'uncategorized') {
      if (hasUncategorized) {
        groups.push({
          id: 'uncategorized',
          name: t('uncategorized'),
          habits: uncategorized
        })
        console.log('  ✓ Added uncategorized group with', uncategorized.length, 'habits')
      }
    } else {
      const cat = categoryMap.get(id)
      if (cat) {
        const categoryHabits = habits.value.filter(h => h.category && h.category.id === cat.id)
        if (categoryHabits.length > 0) {
          groups.push({
            id: cat.id,
            name: cat.name,
            habits: categoryHabits
          })
          console.log('  ✓ Added category', cat.name, 'with', categoryHabits.length, 'habits')
        } else {
          console.log('  ⚠️ Category', cat.name, 'has no habits')
        }
      } else {
        console.log('  ⚠️ Category ID', id, 'not found in categoryMap')
      }
    }
  })

  console.log('  ✅ Final groups:', groups.length)
  console.log('  Groups:', groups.map(g => ({ name: g.name, count: g.habits.length })))

  return groups
})

// --- LOGIC ---
const fetchCategories = async () => {
  try {
    const res = await api.get('categories/')
    categories.value = res.data

    // Sort by order, use ID as tiebreaker
    categories.value.sort((a, b) => {
      if (a.order === b.order) {
        return a.id - b.id
      }
      return (a.order || 0) - (b.order || 0)
    })

    // Create default order
    categoryOrder.value = categories.value.map(c => c.id)
    categoryOrder.value.push('uncategorized')

  } catch (err) {
    console.error("Failed to fetch categories:", err)
  }
}

const fetchHabits = async (date = null) => {
  isLoadingHabits.value = true
  try {
    const dateParam = date || trackingDateString.value
    const res = await api.get('habits/', {
      params: { date: dateParam }
    })
    habits.value = res.data.map(h => ({
      ...h,
      temp_value: h.today_value || 0,
      is_completed_today: h.today_value > 0,
      is_saving: false
    }))
  } catch (err) {
    console.error("Failed to fetch habits:", err)
  } finally {
    isLoadingHabits.value = false
  }
}

const saveLayoutToServer = async () => {
  try {
    // Save the full order to localStorage (including uncategorized)
    localStorage.setItem('categoryOrder', JSON.stringify(categoryOrder.value))

    // Filter out 'uncategorized' and only send real category IDs to server
    const layoutData = categoryOrder.value
      .filter(id => id !== 'uncategorized')
      .map((id, index) => ({
        id,
        order: index
      }))

    await api.post('categories/update_layout/', { layout: layoutData })
    console.log('Layout saved to server')
  } catch (err) {
    console.error('Failed to save layout:', err)
  }
}

const addHabit = async () => {
  if (!newHabitName.value) return

  const formattedIcon = newHabitIcon.value.charAt(0).toUpperCase() + newHabitIcon.value.slice(1).toLowerCase()

  try {
    const payload = {
      name: newHabitName.value,
      habit_type: newHabitType.value,
      icon: formattedIcon,
      color: newHabitColor.value
    }

    if (newHabitCategoryId.value) {
      payload.category_id = newHabitCategoryId.value
    }

    if (newHabitType.value === 'rating') {
      payload.max_value = newHabitMaxValue.value
    }

    const res = await api.post('habits/', payload)

    habits.value.push({
      ...res.data,
      temp_value: 0,
      is_completed_today: false,
      is_saving: false
    })

    newHabitName.value = ''
    newHabitType.value = 'boolean'
    newHabitIcon.value = 'calendar'
    newHabitColor.value = '#1F85DE'
    newHabitCategoryId.value = null
    newHabitMaxValue.value = 5
    isModalOpen.value = false
  } catch (err) {
    console.error("Error creating habit:", err)
  }
}

const saveCompletion = async (habit) => {
  habit.is_saving = true
  try {
    let valueToSave
    if (habit.habit_type === 'boolean') {
      valueToSave = habit.today_value > 0 ? 0 : 1
    } else {
      valueToSave = habit.temp_value
    }

    const payload = {
      value: valueToSave,
      date: trackingDateString.value
    }

    await api.post(`habits/${habit.id}/complete/`, payload)

    habit.today_value = valueToSave
    habit.is_completed_today = valueToSave > 0
  } catch (err) {
    console.error("Logging failed:", err)
  } finally {
    setTimeout(() => { habit.is_saving = false }, 500)
  }
}

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

// Fetch user info
const fetchUserInfo = async () => {
  try {
    const res = await api.get('auth/user/')
    userInfo.value = res.data
    profileData.value.email = res.data.email
  } catch (err) {
    console.error('Failed to fetch user info:', err)
  }
}

// Update profile
const updateProfile = async () => {
  isSavingProfile.value = true
  const startTime = Date.now()

  try {
    // Update email
    if (profileData.value.email !== userInfo.value.email) {
      await api.post('auth/user/', {
        email: profileData.value.email
      })
    }

    // Update password if provided
    if (newPassword.value && confirmPassword.value) {
      if (newPassword.value !== confirmPassword.value) {
        alert('Passwords do not match')
        isSavingProfile.value = false
        return
      }

      if (!profileData.value.current_password) {
        alert('Current password is required to change password')
        isSavingProfile.value = false
        return
      }

      await api.post('auth/password/change/', {
        old_password: profileData.value.current_password,
        new_password1: newPassword.value,
        new_password2: confirmPassword.value
      })

      newPassword.value = ''
      confirmPassword.value = ''
      profileData.value.current_password = ''
      passwordUpdateSuccess.value = true

      // Hide success message after 3 seconds
      setTimeout(() => {
        passwordUpdateSuccess.value = false
      }, 3000)
    }

    // Ensure spinner shows for at least 500ms for better UX
    const elapsedTime = Date.now() - startTime
    const remainingTime = Math.max(0, 500 - elapsedTime)

    await new Promise(resolve => setTimeout(resolve, remainingTime))

    // Set saved state to true
    profileSaved.value = true

    // Refresh user info
    await fetchUserInfo()

    // Hide saved message after 3 seconds
    setTimeout(() => {
      profileSaved.value = false
    }, 3000)
  } catch (err) {
    console.error('Failed to update profile:', err)
    if (err.response?.status === 400) {
      alert(`Error: ${Object.values(err.response.data).join(', ')}`)
    } else {
      alert('Failed to update profile. Please check console for details.')
    }
  } finally {
    isSavingProfile.value = false
  }
}

// Add new category
const addCategory = async () => {
  if (!newCategoryName.value.trim()) return

  isSavingCategory.value = true
  try {
    await api.post('categories/', {
      name: newCategoryName.value,
      order: categories.value.length
    })

    newCategoryName.value = ''
    await fetchCategories()
  } catch (err) {
    console.error('Failed to add category:', err)
    alert('Failed to add category')
  } finally {
    isSavingCategory.value = false
  }
}

// Delete category
const deleteCategory = async (categoryId) => {
  if (!confirm('Are you sure you want to delete this category? Habits in this category will become uncategorized.')) {
    return
  }

  isDeletingCategory.value = categoryId
  try {
    await api.delete(`categories/${categoryId}/`)
    await fetchCategories()
  } catch (err) {
    console.error('Failed to delete category:', err)
    alert('Failed to delete category')
  } finally {
    isDeletingCategory.value = null
  }
}

// Update category name
const updateCategory = async (category) => {
  if (!category.name.trim()) return

  try {
    await api.patch(`categories/${category.id}/`, {
      name: category.name
    })
    editingCategory.value = null
  } catch (err) {
    console.error('Failed to update category:', err)
    alert('Failed to update category')
  }
}

// Delete habit
const deleteHabit = async (habitId) => {
  if (!confirm('Are you sure you want to delete this habit? All completion data will be permanently deleted.')) {
    return
  }

  try {
    await api.delete(`habits/${habitId}/`)
    habits.value = habits.value.filter(h => h.id !== habitId)
  } catch (err) {
    console.error('Failed to delete habit:', err)
    alert('Failed to delete habit')
  }
}

// Start editing a habit
const startEditHabit = (habit) => {
  editingHabit.value = habit.id
  editingHabitData.value = {
    name: habit.name,
    icon: habit.icon,
    color: habit.color,
    habit_type: habit.habit_type,
    max_value: habit.max_value || 5,
    unit: habit.unit || ''
  }
}

// Cancel editing habit
const cancelEditHabit = () => {
  editingHabit.value = null
  editingHabitData.value = {
    name: '',
    icon: '',
    color: '',
    habit_type: '',
    max_value: 5,
    unit: ''
  }
}

// Update habit
const updateHabit = async (habitId) => {
  if (!editingHabitData.value.name.trim()) return

  isSavingHabit.value = true
  try {
    const payload = {
      name: editingHabitData.value.name,
      icon: editingHabitData.value.icon,
      color: editingHabitData.value.color,
      habit_type: editingHabitData.value.habit_type,
      max_value: editingHabitData.value.max_value
    }

    if (editingHabitData.value.unit) {
      payload.unit = editingHabitData.value.unit
    }

    await api.patch(`habits/${habitId}/`, payload)

    // Update habit in local list
    const habitIndex = habits.value.findIndex(h => h.id === habitId)
    if (habitIndex !== -1) {
      habits.value[habitIndex] = {
        ...habits.value[habitIndex],
        ...payload
      }
    }

    editingHabit.value = null
  } catch (err) {
    console.error('Failed to update habit:', err)
    alert('Failed to update habit')
  } finally {
    isSavingHabit.value = false
  }
}

const selectLanguage = (langCode) => {
  setLanguage(langCode)
  isLanguageDropdownOpen.value = false
}

// Date navigation functions
const goToPreviousDay = () => {
  const newDate = new Date(currentTrackingDate.value)
  newDate.setDate(newDate.getDate() - 1)
  currentTrackingDate.value = newDate
  fetchHabits(trackingDateString.value)
}

const goToNextDay = () => {
  if (!canGoToNextDay.value) return
  const newDate = new Date(currentTrackingDate.value)
  newDate.setDate(newDate.getDate() + 1)
  currentTrackingDate.value = newDate
  fetchHabits(trackingDateString.value)
}

const goToToday = () => {
  currentTrackingDate.value = new Date()
  fetchHabits(trackingDateString.value)
}

// Close dropdown when clicking outside
const closeLanguageDropdown = (event) => {
  if (!event.target.closest('.language-dropdown-container')) {
    isLanguageDropdownOpen.value = false
  }
}

onMounted(() => {
  fetchCategories()
  fetchHabits()
  initializeDateRange()

  // Add click outside listener
  document.addEventListener('click', closeLanguageDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeLanguageDropdown)
})
const handleDragStart = (e, categoryId) => {
  draggedCategoryId.value = categoryId
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/html', e.target.innerHTML)
  e.target.style.opacity = '0.4'
}

const handleDragEnd = (e) => {
  e.target.style.opacity = '1'
  draggedCategoryId.value = null
  dragOverCategoryId.value = null
}

const handleDragOver = (e, categoryId) => {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
  dragOverCategoryId.value = categoryId
  return false
}

const handleDragEnter = (e, categoryId) => {
  e.preventDefault()
  dragOverCategoryId.value = categoryId
}

const handleDragLeave = (e) => {
  // Only set to null if we're leaving the category group itself
  // Check if we're moving to a non-category element
  if (e.target.classList && e.target.classList.contains('category-group')) {
    dragOverCategoryId.value = null
  }
}

const handleDrop = (e, targetCategoryId) => {
  e.stopPropagation()
  e.preventDefault()

  console.log('Drop detected:', { draggedCategoryId: draggedCategoryId.value, targetCategoryId })

  if (!draggedCategoryId.value) {
    dragOverCategoryId.value = null
    return
  }

  if (draggedCategoryId.value === targetCategoryId) {
    dragOverCategoryId.value = null
    return
  }

  const newOrder = [...categoryOrder.value]
  const draggedIndex = newOrder.indexOf(draggedCategoryId.value)
  const targetIndex = newOrder.indexOf(targetCategoryId)

  console.log('Indices:', { draggedIndex, targetIndex, newOrderLength: newOrder.length })

  if (draggedIndex !== -1 && targetIndex !== -1) {
    // Remove dragged item
    newOrder.splice(draggedIndex, 1)

    // Calculate insertion index based on direction
    let insertIndex
    if (draggedIndex < targetIndex) {
      // Dragging forward (from earlier to later)
      // After removal, target index shifts down by 1, but we want to insert AFTER it
      insertIndex = targetIndex
    } else {
      // Dragging backward (from later to earlier)
      // Target index doesn't shift, insert before it
      insertIndex = targetIndex
    }

    // Insert at calculated position
    newOrder.splice(insertIndex, 0, draggedCategoryId.value)

    console.log('New order:', newOrder)

    categoryOrder.value = newOrder
    saveLayoutToServer()
  }

  draggedCategoryId.value = null
  dragOverCategoryId.value = null
  return false
}

const getIcon = (iconName) => {
  // Convert hyphen-separated names to camelCase
  // e.g., "arrow-right" becomes "arrowRight"
  const camelCaseName = iconName.replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());

  const searchName = camelCaseName.toLowerCase();
  const key = Object.keys(LucideIcons).find(
    (k) => k.toLowerCase() === searchName
  );
  return LucideIcons[key] || LucideIcons.Activity;
}

// Initialize date range
const initializeDateRange = () => {
  const today = new Date()
  const thirtyDaysAgo = new Date(today)
  thirtyDaysAgo.setDate(today.getDate() - 30)

  graphEndDate.value = today.toISOString().split('T')[0]
  graphStartDate.value = thirtyDaysAgo.toISOString().split('T')[0]
}

// Set date range for a specific year
const setYearRange = (year) => {
  graphStartDate.value = `${year}-01-01`
  graphEndDate.value = `${year}-12-31`
}

// Set date range for all available data
const setAllDataRange = async () => {
  try {
    const response = await api.get('habits/date_range/')
    if (response.data.start_date && response.data.end_date) {
      graphStartDate.value = response.data.start_date
      graphEndDate.value = response.data.end_date
    }
  } catch (err) {
    console.error('Failed to fetch date range:', err)
    // Fallback: set to a wide range
    graphStartDate.value = '2020-01-01'
    graphEndDate.value = new Date().toISOString().split('T')[0]
  }
}

// Fetch summary data for last 7 days
const fetchSummaryData = async () => {
  isFetchingSummary.value = true
  try {
    const today = new Date()
    const sevenDaysAgo = new Date(today)
    sevenDaysAgo.setDate(today.getDate() - 7)

    const response = await api.get('habits/summary/', {
      params: {
        start_date: sevenDaysAgo.toISOString().split('T')[0],
        end_date: today.toISOString().split('T')[0]
      }
    })

    summaryData.value = response.data
  } catch (err) {
    console.error('Failed to fetch summary data:', err)
  } finally {
    isFetchingSummary.value = false
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

    await nextTick()
    renderCharts()
  } catch (err) {
    console.error('Failed to fetch graph data:', err)
  }
}

// Render all charts
const renderCharts = () => {
  const habitTypes = ['boolean', 'counter', 'value', 'rating']

  habitTypes.forEach(type => {
    const canvasId = `chart-${type}`
    const canvas = document.getElementById(canvasId)

    if (!canvas) return

    // Destroy existing chart
    if (chartInstances.value[type]) {
      chartInstances.value[type].destroy()
    }

    const ctx = canvas.getContext('2d')
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
watch(isDark, () => {
  if (activeTab.value === 'graph') {
    renderCharts()
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
  } else if (newTab === 'profile') {
    fetchUserInfo()
  }
})

// Watch for changes to profile to reset saved state
watch(profileData, () => {
  profileSaved.value = false
}, { deep: true })

onMounted(() => {
  fetchCategories()
  fetchHabits()
  initializeDateRange()
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
            class="bg-red-600 text-white px-8 py-4 rounded-2xl font-bold hover:bg-red-700 transition-all shadow-md active:scale-95">
            {{ t('logout') }}
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
      <div v-show="activeTab === 'tracking'" class="space-y-8">

        <div class="fixed top-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-2xl z-50 max-w-xs" hidden="">
          <h3 class="font-black mb-2">🔍 DEBUG INFO</h3>
          <div class="space-y-1 text-xs">
            <div>✓ Tracking tab is VISIBLE</div>
            <div>Active Tab: <strong>{{ activeTab }}</strong></div>
            <div>Loading: <strong>{{ isLoadingHabits }}</strong></div>
            <div>Habits Count: <strong>{{ habits.length }}</strong></div>
            <div>Categories: <strong>{{ categories.length }}</strong></div>
            <div>Groups: <strong>{{ groupedHabits.length }}</strong></div>
            <div class="pt-2 border-t border-white/30 mt-2">
              <div v-if="habits.length > 0">
                First habit: {{ habits[0].name }}
              </div>
              <div v-else class="text-yellow-300">
                ⚠️ Habits array is empty
              </div>
            </div>
          </div>
        </div>

        <!-- Date Navigation -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-6 shadow-lg border border-slate-100 dark:border-slate-700">
          <!-- Navigation and Date Row -->
          <div class="flex items-center justify-between gap-3">
            <!-- Previous Day Button -->
            <button @click="goToPreviousDay"
              class="shrink-0 p-3 rounded-2xl bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-all active:scale-95 self-center">
              <ChevronDown :size="20" class="rotate-90 text-slate-700 dark:text-slate-300" stroke-width="2.5" />
            </button>

            <!-- Date and View Toggle Combined Cell -->
            <div class="flex-1 flex flex-col items-center gap-3">
              <!-- Current Date Display -->
              <div class="text-center">
                <div class="text-lg md:text-2xl font-black text-slate-900 dark:text-white truncate">
                  {{ formattedTrackingDate }}
                </div>
                <div class="text-xs text-slate-400 dark:text-slate-500 font-bold truncate">
                  {{ trackingDateString }}
                </div>
              </div>

              <!-- View Toggle -->
              <div class="flex gap-1 p-1 bg-slate-100 dark:bg-slate-700 rounded-lg">
                <button @click="isCardView = true" :class="[
                  'px-3 py-1.5 rounded-md font-bold transition-all text-xs',
                  isCardView
                    ? 'bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                ]">
                  {{ t('cardView') }}
                </button>
                <button @click="isCardView = false" :class="[
                  'px-3 py-1.5 rounded-md font-bold transition-all text-xs',
                  !isCardView
                    ? 'bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                ]">
                  {{ t('rowView') }}
                </button>
              </div>
            </div>

            <!-- Next Day Button -->
            <button @click="goToNextDay" :disabled="!canGoToNextDay" :class="[
              'shrink-0 p-3 rounded-2xl transition-all active:scale-95 self-center',
              canGoToNextDay
                ? 'bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600'
                : 'bg-slate-50 dark:bg-slate-800 opacity-30 cursor-not-allowed'
            ]">
              <ChevronDown :size="20" class="-rotate-90"
                :class="canGoToNextDay ? 'text-slate-700 dark:text-slate-300' : 'text-slate-400'" stroke-width="2.5" />
            </button>

            <!-- Today Button (only show if not on today) -->
            <button v-if="formattedTrackingDate !== t('today')" @click="goToToday"
              class="shrink-0 px-3 py-2 bg-indigo-600 text-white rounded-xl font-bold text-xs md:text-sm hover:bg-indigo-700 transition-all active:scale-95 whitespace-nowrap self-center">
              {{ t('today') }}
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoadingHabits" class="flex items-center justify-center py-20">
          <RefreshCw :size="40" class="animate-spin text-indigo-500" />
        </div>

        <!-- Habit Groups -->
        <div v-else v-for="group in groupedHabits" :key="group.id" @dragover="(e) => handleDragOver(e, group.id)"
          @dragenter="(e) => handleDragEnter(e, group.id)" @dragleave="handleDragLeave"
          @drop="(e) => handleDrop(e, group.id)" :class="[
            'category-group transition-all duration-200',
            dragOverCategoryId === group.id ? 'border-4 border-indigo-500 border-dashed rounded-3xl p-4' : ''
          ]">
          <!-- Category Header -->
          <div :draggable=true @dragstart="(e) => handleDragStart(e, group.id)" @dragend="handleDragEnd"
            class="flex items-center gap-3 mb-6 cursor-move select-none">
            <GripVertical class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
              :size="24" />
            <h2 class="text-2xl font-black text-slate-800 dark:text-white uppercase tracking-tight">
              {{ group.name }}
            </h2>
            <div class="flex-1 h-1 bg-linear-to-r from-slate-200 dark:from-slate-700 to-transparent rounded-full">
            </div>
            <span class="text-sm font-bold text-slate-400 dark:text-slate-500">
              {{ group.habits.length }} {{ group.habits.length === 1 ? t('habit') : t('habits') }}
            </span>
          </div>

          <!-- Habits Grid - Card View -->
          <div v-if="isCardView" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="habit in group.habits" :key="habit.id" :class="[
              'relative p-8 rounded-[3rem] transition-all duration-300 flex flex-col justify-between overflow-hidden border',
              habit.today_value > 0
                ? 'bg-white dark:bg-slate-800 border-transparent shadow-[0_20px_40px_-10px_rgba(0,0,0,0.08)] dark:shadow-[0_20px_40px_-10px_rgba(0,0,0,0.3)]'
                : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-lg dark:hover:shadow-slate-950/50 hover:-translate-y-1'
            ]" :style="{ minHeight: '280px' }">

              <div class="absolute -right-8 -top-8 w-32 h-32 rounded-full blur-3xl opacity-10 dark:opacity-20"
                :style="{ backgroundColor: habit.color }"></div>

              <div class="flex justify-between items-start relative z-10">
                <div class="flex flex-col">
                  <span class="text-[10px] font-black uppercase tracking-[0.25em] mb-2 opacity-50"
                    :style="{ color: habit.color }">
                    {{ habit.habit_type }}
                  </span>
                  <h3 class="text-2xl font-black text-slate-800 dark:text-white leading-tight">{{ habit.name }}</h3>
                </div>
                <div class="p-4 rounded-3xl transition-all duration-300" :style="{
                  backgroundColor: habit.today_value > 0 ? habit.color : `${habit.color}15`,
                  color: habit.today_value > 0 ? 'white' : habit.color
                }">
                  <component :is="getIcon(habit.icon)" :size="26" stroke-width="2.5" />
                </div>
              </div>

              <div class="relative z-10 space-y-4">

                <!-- Counter Type -->
                <div v-if="habit.habit_type === 'counter'" class="flex items-center gap-3">
                  <div
                    class="flex-1 flex justify-between items-center bg-slate-50 dark:bg-slate-700 rounded-2xl p-1.5 border border-slate-100 dark:border-slate-600">
                    <button @click="habit.temp_value = Math.max(0, Number(habit.temp_value) - 1)"
                      class="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-white dark:hover:bg-slate-600 transition text-slate-400 dark:text-slate-300 font-bold">
                      -
                    </button>

                    <span class="font-black text-slate-800 dark:text-white text-lg">
                      {{ Number(habit.temp_value).toFixed(0) }}
                    </span>

                    <button @click="habit.temp_value = Number(habit.temp_value) + 1"
                      class="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-white dark:hover:bg-slate-600 transition text-slate-400 dark:text-slate-300 font-bold">
                      +
                    </button>
                  </div>

                  <button @click="saveCompletion(habit)"
                    class="px-6 py-4 rounded-2xl font-bold text-white transition-all active:scale-95 flex items-center gap-2"
                    :style="{ backgroundColor: habit.color, boxShadow: `0 10px 20px -5px ${habit.color}40` }">
                    <RefreshCw v-if="habit.is_saving" :size="18" class="animate-spin" />
                    <Save v-else :size="18" />
                  </button>
                </div>

                <!-- Value Type -->
                <div v-else-if="habit.habit_type === 'value'" class="flex gap-3">
                  <div class="relative flex-1">
                    <input type="number" v-model="habit.temp_value" placeholder="0.0" step="0.1" min="0"
                      class="w-full p-4 bg-slate-50 dark:bg-slate-700 border border-slate-100 dark:border-slate-600 rounded-2xl font-bold outline-none focus:ring-2 text-slate-900 dark:text-white"
                      :style="{ '--tw-ring-color': habit.color }">
                  </div>

                  <button @click="saveCompletion(habit)"
                    class="px-6 py-4 rounded-2xl font-bold text-white transition-all active:scale-95 flex items-center gap-2"
                    :style="{ backgroundColor: habit.color, boxShadow: `0 10px 20px -5px ${habit.color}40` }">
                    <RefreshCw v-if="habit.is_saving" :size="18" class="animate-spin" />
                    <Save v-else :size="18" />
                  </button>
                </div>

                <!-- Rating Type -->
                <div v-else-if="habit.habit_type === 'rating'" class="space-y-3">
                  <div
                    class="flex justify-center items-center gap-0.5 bg-slate-50 dark:bg-slate-700 rounded-2xl p-3 border border-slate-100 dark:border-slate-600">
                    <button v-for="star in (habit.max_value || 5)" :key="star"
                      @click="habit.temp_value = star; saveCompletion(habit)"
                      class="transition-all hover:scale-120 active:scale-95 shrink-0"
                      :class="star <= habit.temp_value ? '' : 'opacity-30'" style="padding: 0 !important;">
                      <Star
                        :size="(habit.max_value || 5) <= 5 ? 28 : (habit.max_value || 5) <= 6 ? 24 : (habit.max_value || 5) <= 8 ? 20 : 16"
                        :fill="star <= habit.temp_value ? habit.color : 'none'" :stroke="habit.color"
                        stroke-width="2" />
                    </button>
                  </div>
                </div>

                <!-- Boolean Type -->
                <button v-else @click="saveCompletion(habit)"
                  class="w-full py-4 rounded-2xl font-bold text-white transition-all flex items-center justify-center gap-2 active:scale-95"
                  :style="{
                    backgroundColor: habit.today_value > 0 ? '#10b981' : habit.color,
                    boxShadow: habit.today_value > 0 ? '0 15px 30px -10px #10b98160' : `0 15px 30px -10px ${habit.color}40`
                  }">
                  <CheckCircle2 v-if="habit.today_value > 0" :size="20" />
                  {{ habit.today_value > 0 ? t('completed') : t('markComplete') }}
                </button>
              </div>
            </div>
          </div>

          <!-- Habits List - Row View -->
          <div v-else class="space-y-2">
            <div v-for="habit in group.habits" :key="habit.id" :class="[
              'flex items-center justify-between p-4 rounded-2xl transition-all border',
              habit.today_value > 0
                ? 'bg-slate-50 dark:bg-slate-700/50 border-slate-100 dark:border-slate-600'
                : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700 hover:shadow-md'
            ]">
              <!-- Left: Icon and Info -->
              <div class="flex items-center gap-4 flex-1 min-w-0">
                <div class="p-3 rounded-2xl shrink-0 transition-all" :style="{
                  backgroundColor: habit.today_value > 0 ? habit.color : `${habit.color}15`,
                  color: habit.today_value > 0 ? 'white' : habit.color
                }">
                  <component :is="getIcon(habit.icon)" :size="20" stroke-width="2.5" />
                </div>
                <div class="min-w-0 flex-1">
                  <h3 class="font-bold text-slate-900 dark:text-white truncate">{{ habit.name }}</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide">{{ habit.habit_type }}
                  </p>
                </div>
              </div>

              <!-- Right: Actions -->
              <div class="flex items-center gap-2 ml-4 shrink-0">
                <!-- Counter Input -->
                <div v-if="habit.habit_type === 'counter'" class="flex items-center gap-2">
                  <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-700 rounded-lg p-1">
                    <button @click="habit.temp_value = Math.max(0, Number(habit.temp_value) - 1)"
                      class="w-8 h-8 flex items-center justify-center rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 transition">
                      <span class="font-bold text-slate-600 dark:text-slate-300">-</span>
                    </button>
                    <input v-model.number="habit.temp_value" type="number" min="0"
                      class="w-12 text-center bg-transparent font-bold text-slate-900 dark:text-white outline-none text-sm" />
                    <button @click="habit.temp_value = Number(habit.temp_value) + 1"
                      class="w-8 h-8 flex items-center justify-center rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 transition">
                      <span class="font-bold text-slate-600 dark:text-slate-300">+</span>
                    </button>
                  </div>
                  <button @click="saveCompletion(habit)"
                    class="px-3 py-2 rounded-lg font-bold text-white transition-all active:scale-95 flex items-center gap-1 shrink-0"
                    :style="{ backgroundColor: habit.color }">
                    <RefreshCw v-if="habit.is_saving" :size="16" class="animate-spin" />
                    <Save v-else :size="16" />
                  </button>
                </div>

                <!-- Value Input -->
                <div v-else-if="habit.habit_type === 'value'" class="flex items-center gap-2">
                  <input v-model.number="habit.temp_value" type="number" min="0"
                    class="w-16 px-2 py-1 bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg font-bold text-center text-slate-900 dark:text-white outline-none text-sm" />
                  <span v-if="habit.unit" class="text-xs font-bold text-slate-500 dark:text-slate-400">{{ habit.unit
                  }}</span>
                  <button @click="saveCompletion(habit)"
                    class="px-3 py-2 rounded-lg font-bold text-white transition-all active:scale-95 flex items-center gap-1 shrink-0"
                    :style="{ backgroundColor: habit.color }">
                    <RefreshCw v-if="habit.is_saving" :size="16" class="animate-spin" />
                    <Save v-else :size="16" />
                  </button>
                </div>

                <!-- Rating Stars -->
                <div v-else-if="habit.habit_type === 'rating'" class="flex items-center gap-1">
                  <button v-for="star in (habit.max_value || 5)" :key="star"
                    @click="habit.temp_value = star; saveCompletion(habit)"
                    class="transition-all hover:scale-120 active:scale-95"
                    :class="star <= habit.temp_value ? '' : 'opacity-30'">
                    <Star :size="26" :fill="star <= habit.temp_value ? habit.color : 'none'" :stroke="habit.color"
                      stroke-width="2" />
                  </button>
                </div>

                <!-- Boolean Button -->
                <button v-else @click="saveCompletion(habit)" :class="[
                  'px-4 py-1.5 rounded-lg font-bold text-white text-sm transition-all active:scale-95 shrink-0',
                  habit.today_value > 0
                    ? 'bg-green-500 hover:bg-green-600'
                    : 'hover:opacity-80'
                ]" :style="!habit.today_value ? { backgroundColor: habit.color } : {}">
                  {{ habit.today_value > 0 ? t('completed') : t('save') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary Tab -->
      <div v-show="activeTab === 'summary'" class="space-y-6">
        <!-- Header -->
        <div class="bg-linear-to-r from-indigo-500 to-purple-600 rounded-[3rem] p-12 shadow-xl">
          <h2 class="text-3xl font-black text-white mb-2">{{ t('summaryView') }}</h2>
          <p class="text-indigo-100 font-medium">{{ t('retrospectiveAnalysis') }}</p>
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
      <div v-show="activeTab === 'profile'" class="space-y-6">
        <!-- Account Information -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-3 bg-indigo-100 dark:bg-indigo-900/30 rounded-2xl">
              <User :size="24" class="text-indigo-600 dark:text-indigo-400" stroke-width="2.5" />
            </div>
            <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('accountInformation') }}</h2>
          </div>

          <div class="space-y-4">
            <div class="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
              <User :size="20" class="text-slate-400" />
              <div>
                <p class="text-xs font-black uppercase tracking-widest text-slate-400">{{ t('username') }}</p>
                <p class="font-bold text-slate-900 dark:text-white">{{ userInfo.username || 'Loading...'
                }}</p>
              </div>
            </div>

            <div class="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
              <Mail :size="20" class="text-slate-400" />
              <div>
                <p class="text-xs font-black uppercase tracking-widest text-slate-400">{{ t('email') }}</p>
                <input v-model="profileData.email" type="email"
                  class="font-bold text-slate-900 dark:text-white bg-transparent border-b-2 border-indigo-500 focus:outline-none w-full" />
              </div>
            </div>
          </div>
        </div>

        <!-- Password Management -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-2xl">
              <Lock :size="24" class="text-orange-600 dark:text-orange-400" stroke-width="2.5" />
            </div>
            <h2 class="text-2xl font-black text-slate-900 dark:text-white">Change Password</h2>
          </div>

          <div class="space-y-4">
            <div>
              <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-2 block">
                {{ t('currentPassword') }}
              </label>
              <input v-model="profileData.current_password" type="password" placeholder="Enter current password"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-orange-500 transition outline-none font-bold text-slate-900 dark:text-white" />
            </div>

            <div>
              <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-2 block">
                {{ t('newPassword') }}
              </label>
              <input v-model="newPassword" type="password" placeholder="Enter new password"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-orange-500 transition outline-none font-bold text-slate-900 dark:text-white" />
            </div>

            <div>
              <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-2 block">
                {{ t('confirmNewPassword') }}
              </label>
              <input v-model="confirmPassword" type="password" placeholder="Confirm new password"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-orange-500 transition outline-none font-bold text-slate-900 dark:text-white" />
            </div>
          </div>
        </div>

        <!-- Save Button -->
        <button @click="updateProfile" :disabled="isSavingProfile || profileSaved" :class="[
          'w-full px-8 py-4 rounded-2xl font-bold transition-all shadow-md active:scale-95 disabled:cursor-not-allowed flex items-center justify-center gap-2',
          profileSaved
            ? 'bg-green-600 text-white'
            : 'bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50'
        ]">
          <RefreshCw v-if="isSavingProfile" :size="20" class="animate-spin" />
          <CheckCircle2 v-else-if="profileSaved" :size="20" stroke-width="2.5" />
          <Save v-else :size="20" stroke-width="2.5" />
          {{ isSavingProfile ? t('saving') : profileSaved ? t('profileUpdated') : t('updateProfile') }}
        </button>

        <!-- Category Management -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-2xl">
              <Database :size="24" class="text-purple-600 dark:text-purple-400" stroke-width="2.5" />
            </div>
            <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('categoryManagement') }}</h2>
          </div>

          <!-- Add New Category -->
          <div class="mb-6">
            <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-2 block">
              {{ t('addCategory') }}
            </label>
            <div class="flex gap-3">
              <input v-model="newCategoryName" @keyup.enter="addCategory" type="text" :placeholder="t('categoryName')"
                class="flex-1 bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-slate-900 dark:text-white" />
              <button @click="addCategory" :disabled="isSavingCategory || !newCategoryName.trim()"
                class="px-8 py-4 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-md active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
                <Plus :size="20" stroke-width="2.5" />
                {{ t('addCategory') }}
              </button>
            </div>
          </div>

          <!-- Existing Categories -->
          <div class="space-y-3">
            <p class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-3">
              Existing Categories ({{ categories.length }})
            </p>

            <div v-if="categories.length === 0" class="text-center py-8 text-slate-400 dark:text-slate-500">
              No categories yet. Add your first category above.
            </div>

            <div v-for="category in categories" :key="category.id"
              class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl hover:shadow-md transition-all">
              <div class="flex-1" v-if="editingCategory !== category.id">
                <p class="font-bold text-slate-900 dark:text-white">{{ category.name }}</p>
              </div>

              <input v-else v-model="category.name" @keyup.enter="updateCategory(category)"
                @keyup.esc="editingCategory = null" type="text"
                class="flex-1 bg-white dark:bg-slate-600 border-2 border-indigo-500 rounded-xl px-4 py-2 font-bold outline-none text-slate-900 dark:text-white"
                autofocus />

              <div class="flex gap-2 ml-4">
                <button v-if="editingCategory !== category.id" @click="editingCategory = category.id"
                  class="px-4 py-2 bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-300 dark:hover:bg-slate-500 transition-all text-sm">
                  {{ t('editCategory') }}
                </button>

                <button v-else @click="updateCategory(category)"
                  class="px-4 py-2 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 transition-all text-sm flex items-center gap-1">
                  <Save :size="16" />
                  {{ t('save') }}
                </button>

                <button v-if="editingCategory === category.id" @click="editingCategory = null"
                  class="px-4 py-2 bg-slate-300 dark:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-400 dark:hover:bg-slate-500 transition-all text-sm">
                  Cancel
                </button>

                <button @click="deleteCategory(category.id)" :disabled="isDeletingCategory === category.id"
                  class="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-xl font-bold hover:bg-red-200 dark:hover:bg-red-900/50 transition-all text-sm flex items-center gap-1 disabled:opacity-50">
                  <Trash2 :size="16" />
                  {{ isDeletingCategory === category.id ? t('deleting') : t('deleteCategory') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Manage Habits -->
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-2xl">
              <CheckCircle2 :size="24" class="text-blue-600 dark:text-blue-400" stroke-width="2.5" />
            </div>
            <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('editHabit') }}</h2>
          </div>

          <!-- Existing Habits -->
          <div class="space-y-3">
            <p class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-3">
              Your Habits ({{ habits.length }})
            </p>

            <div v-if="habits.length === 0" class="text-center py-8 text-slate-400 dark:text-slate-500">
              No habits yet. Create your first habit using the "+ Add Habit" button at the top.
            </div>

            <div v-for="habit in habits" :key="habit.id"
              class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl hover:shadow-md transition-all">
              <div class="flex items-center gap-4 flex-1">
                <div class="shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
                  :style="{ backgroundColor: habit.color + '20' }">
                  <component :is="getIcon(habit.icon)" :size="20" :style="{ color: habit.color }" stroke-width="2.5" />
                </div>
                <div class="flex-1">
                  <p class="font-bold text-slate-900 dark:text-white">{{ habit.name }}</p>
                  <div class="flex gap-2 mt-1">
                    <span
                      class="text-xs px-2 py-1 rounded-full bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300 font-bold">
                      {{ habit.habit_type }}
                    </span>
                    <span v-if="habit.category"
                      class="text-xs px-2 py-1 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 font-bold">
                      {{ habit.category.name }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="flex gap-2 ml-4">
                <button @click="startEditHabit(habit)"
                  class="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-all active:scale-95">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                </button>
                <button @click="deleteHabit(habit.id)"
                  class="p-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-xl hover:bg-red-200 dark:hover:bg-red-900/50 transition-all active:scale-95">
                  <Trash2 :size="18" stroke-width="2.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="max-w-7xl mx-auto mt-16 pt-8 pb-6 border-t border-slate-200 dark:border-slate-700">
      <div class="flex flex-col md:flex-row justify-between items-center gap-6">
        <!-- GitHub Link -->
        <div class="flex items-center gap-3">
          <a href="https://github.com/continuum-app/continuum" target="_blank" rel="noopener noreferrer"
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

    <!-- Modal for Edit Habit -->
    <Transition name="fade">
      <div v-if="editingHabit" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-md" @click="cancelEditHabit"></div>
        <div
          class="relative bg-white dark:bg-slate-800 w-full max-w-lg rounded-[3rem] p-12 shadow-2xl overflow-visible">
          <div class="absolute top-0 left-0 right-0 h-2 bg-blue-500 rounded-t-[3rem]"></div>

          <div class="flex justify-between items-center mb-10">
            <h2 class="text-3xl font-black text-slate-900 dark:text-white">{{ t('editHabit') }}</h2>
            <button @click="cancelEditHabit"
              class="text-slate-300 hover:text-slate-900 dark:hover:text-white transition">
              <X :size="32" />
            </button>
          </div>

          <form @submit.prevent="updateHabit(editingHabit)" class="space-y-8">
            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Habit Name</label>
              <input v-model="editingHabitData.name" type="text" placeholder="Enter habit name" required
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white" />
            </div>

            <IconPicker v-model="editingHabitData.icon" label="Icon" />

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Type</label>
              <select v-model="editingHabitData.habit_type" disabled
                class="w-full bg-slate-100 dark:bg-slate-700 border-2 border-slate-100 dark:border-slate-700 rounded-2xl px-4 py-3 font-bold text-slate-600 dark:text-slate-400 cursor-not-allowed">
                <option value="boolean">Yes/No</option>
                <option value="counter">Counter</option>
                <option value="value">Decimal Value</option>
                <option value="rating">Rating</option>
              </select>
              <p class="text-xs text-slate-400 ml-2 mt-1">Type cannot be changed</p>
            </div>

            <!-- Unit for Value type -->
            <div v-if="editingHabitData.habit_type === 'value'" class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('habitUnit') }}
                (Optional)</label>
              <input v-model="editingHabitData.unit" type="text" :placeholder="t('unitPlaceholder')"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-slate-900 dark:text-white" />
              <p class="text-xs text-slate-400 ml-2">Leave empty to use default unit</p>
            </div>

            <!-- Max Value for Rating -->
            <div v-if="editingHabitData.habit_type === 'rating'" class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">
                {{ t('maxValue') }}
              </label>
              <input v-model.number="editingHabitData.max_value" type="number" min="1" max="10"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white" />
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Color</label>
              <div class="flex items-center gap-4 bg-slate-50 dark:bg-slate-700 p-4 rounded-3xl">
                <input v-model="editingHabitData.color" type="color"
                  class="w-16 h-10 rounded-2xl cursor-pointer border-none" />
                <span class="font-mono text-sm text-slate-600 dark:text-slate-400">{{ editingHabitData.color }}</span>
              </div>
            </div>

            <div class="flex gap-3">
              <button type="submit" :disabled="isSavingHabit"
                class="flex-1 bg-blue-600 text-white py-4 rounded-3xl font-black hover:bg-blue-700 transition-all shadow-xl disabled:opacity-50 flex items-center justify-center gap-2">
                <RefreshCw v-if="isSavingHabit" :size="20" class="animate-spin" />
                <Save v-else :size="20" stroke-width="2.5" />
                {{ isSavingHabit ? t('saving') : t('save') }}
              </button>
              <button type="button" @click="cancelEditHabit"
                class="flex-1 bg-slate-300 dark:bg-slate-600 text-slate-700 dark:text-slate-300 py-4 rounded-3xl font-black hover:bg-slate-400 dark:hover:bg-slate-500 transition-all">
                Cancel
              </button>
            </div>
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