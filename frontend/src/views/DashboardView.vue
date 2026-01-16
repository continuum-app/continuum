<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import authService from '../services/auth'
import { useDarkMode } from '../composables/useDarkMode'
import * as LucideIcons from 'lucide-vue-next'
import { Plus, X, ChevronDown, CheckCircle2, RefreshCw, Save, Star, Moon, Sun, GripVertical, BarChart3, FileText, Download, Calendar } from 'lucide-vue-next'

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()

// --- STATE ---
const habits = ref([])
const categories = ref([])
const isModalOpen = ref(false)
const draggedCategoryId = ref(null)
const dragOverCategoryId = ref(null)
const categoryOrder = ref([]) // Array of category IDs in order
const activeTab = ref('tracking') // New: active tab state

// Form Refs for New Habit
const newHabitName = ref('')
const newHabitType = ref('boolean')
const newHabitIcon = ref('calendar')
const newHabitColor = ref('#1F85DE')
const newHabitCategoryId = ref(null)
const newHabitMaxValue = ref(5)

// --- COMPUTED ---
const groupedHabits = computed(() => {
  const groups = []

  // Create a map of categories by ID for quick lookup
  const categoryMap = new Map()
  categories.value.forEach(cat => {
    categoryMap.set(cat.id, cat)
  })

  // Check if uncategorized habits exist
  const uncategorized = habits.value.filter(h => !h.category)
  const hasUncategorized = uncategorized.length > 0

  // Build ordered list based on categoryOrder
  let orderedCategoryIds
  if (categoryOrder.value.length > 0) {
    // Use existing order
    orderedCategoryIds = categoryOrder.value
  } else {
    // Create default order: uncategorized first (if exists), then categories
    orderedCategoryIds = hasUncategorized
      ? ['uncategorized', ...categories.value.map(c => c.id)]
      : categories.value.map(c => c.id)
  }

  // Add groups in order (including uncategorized)
  orderedCategoryIds.forEach(id => {
    if (id === 'uncategorized') {
      if (hasUncategorized) {
        groups.push({
          id: 'uncategorized',
          name: 'Uncategorized',
          habits: uncategorized
        })
      }
    } else {
      const cat = categoryMap.get(id)
      if (cat) {
        const categoryHabits = habits.value.filter(h => h.category?.id === cat.id)
        if (categoryHabits.length > 0) {
          groups.push({
            id: cat.id,
            name: cat.name,
            habits: categoryHabits
          })
        }
      }
    }
  })

  return groups
})

// --- LOGIC ---
const fetchCategories = async () => {
  try {
    const res = await api.get('categories/')
    categories.value = res.data

    // Sort by order field
    categories.value.sort((a, b) => (a.order || 0) - (b.order || 0))

    // Try to load saved order from localStorage
    const savedOrder = localStorage.getItem('categoryOrder')
    if (savedOrder) {
      try {
        categoryOrder.value = JSON.parse(savedOrder)
        return
      } catch (e) {
        console.error('Failed to parse saved order:', e)
      }
    }

    // No saved order, create default based on database order
    categoryOrder.value = categories.value.map(c => c.id)

    // Add uncategorized at the end if there are uncategorized habits
    // Note: We can't check habits.value here if habits aren't loaded yet
    // So we always add it and let groupedHabits computed filter it out if empty
    if (!categoryOrder.value.includes('uncategorized')) {
      categoryOrder.value.push('uncategorized')
    }
  } catch (err) {
    console.error("Failed to fetch categories:", err)
  }
}

const fetchHabits = async () => {
  try {
    const res = await api.get('habits/')
    habits.value = res.data.map(h => ({
      ...h,
      temp_value: h.today_value || 0,
      is_completed_today: h.today_value > 0,
      is_saving: false
    }))
  } catch (err) {
    console.error("Failed to fetch habits:", err)
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
      value: valueToSave
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

// Drag handlers
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
  dragOverCategoryId.value = null
}

const handleDrop = (e, targetCategoryId) => {
  e.stopPropagation()
  e.preventDefault()

  if (!draggedCategoryId.value || draggedCategoryId.value === targetCategoryId) {
    dragOverCategoryId.value = null
    return
  }

  const newOrder = [...categoryOrder.value]
  const draggedIndex = newOrder.indexOf(draggedCategoryId.value)
  const targetIndex = newOrder.indexOf(targetCategoryId)

  if (draggedIndex !== -1 && targetIndex !== -1) {
    // Special case: only 2 groups and dragging last onto first
    if (newOrder.length === 2 && draggedIndex === 1 && targetIndex === 0) {
      // Swap them - dragged goes first
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(0, 0, draggedCategoryId.value)
    } else {
      // Normal case: always insert AFTER the target
      // Remove dragged item
      newOrder.splice(draggedIndex, 1)

      // Calculate adjusted target index after removal
      let adjustedTargetIndex = targetIndex
      if (draggedIndex < targetIndex) {
        adjustedTargetIndex = targetIndex - 1
      }

      // Always insert AFTER the target
      const insertIndex = adjustedTargetIndex + 1

      // Insert at calculated position
      newOrder.splice(insertIndex, 0, draggedCategoryId.value)
    }

    categoryOrder.value = newOrder
    saveLayoutToServer()
  }

  dragOverCategoryId.value = null
  return false
}

const getIcon = (iconName) => {
  const searchName = iconName.toLowerCase();
  const key = Object.keys(LucideIcons).find(
    (k) => k.toLowerCase() === searchName
  );
  return LucideIcons[key] || LucideIcons.Activity;
}

onMounted(() => {
  fetchCategories()
  fetchHabits()
})
</script>

<template>
  <div
    class="min-h-screen bg-[#f8fafc] dark:bg-slate-900 p-6 md:p-12 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-300">
    <div class="max-w-7xl mx-auto">

      <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
        <div>
          <h1 class="text-4xl font-black tracking-tighter text-slate-900 dark:text-white uppercase italic">Continuum
          </h1>
          <p class="text-slate-400 dark:text-slate-500 font-medium">Daily evolution, quantified.</p>
        </div>
        <div class="flex gap-4">
          <!-- Dark Mode Toggle -->
          <button @click="toggleDarkMode"
            class="bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-yellow-400 px-6 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-slate-300 dark:hover:bg-slate-600 transition-all shadow-md active:scale-95">
            <Moon v-if="!isDark" :size="20" stroke-width="2.5" />
            <Sun v-else :size="20" stroke-width="2.5" />
          </button>

          <button @click="isModalOpen = true"
            class="bg-indigo-500 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-indigo-600 transition-all shadow-md active:scale-95">
            <Plus :size="20" stroke-width="3" /> New Habit
          </button>

          <button @click="handleLogout"
            class="bg-red-600 text-white px-8 py-4 rounded-2xl font-bold hover:bg-red-700 transition-all shadow-md active:scale-95">
            Logout
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
            <span>Tracking</span>
          </button>

          <button @click="activeTab = 'summary'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'summary'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
          ]">
            <FileText :size="20" stroke-width="2.5" />
            <span>Summary</span>
          </button>

          <button @click="activeTab = 'graph'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'graph'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
          ]">
            <BarChart3 :size="20" stroke-width="2.5" />
            <span>Graph</span>
          </button>

          <button @click="activeTab = 'export'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'export'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
          ]">
            <Download :size="20" stroke-width="2.5" />
            <span>Export</span>
          </button>
        </div>
      </div>

      <!-- Tab Content -->

      <!-- Tracking Tab -->
      <div v-show="activeTab === 'tracking'" class="space-y-12">
        <div v-for="group in groupedHabits" :key="group.id" :draggable=true
          @dragstart="(e) => handleDragStart(e, group.id)" @dragend="handleDragEnd"
          @dragover="(e) => handleDragOver(e, group.id)" @dragenter="(e) => handleDragEnter(e, group.id)"
          @dragleave="handleDragLeave" @drop="(e) => handleDrop(e, group.id)" :class="[
            'category-group transition-all duration-200',
            dragOverCategoryId === group.id ? 'border-4 border-indigo-500 border-dashed rounded-3xl p-4' : ''
          ]">
          <!-- Category Header -->
          <div class="flex items-center gap-3 mb-6 cursor-move select-none">
            <GripVertical class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
              :size="24" />
            <h2 class="text-2xl font-black text-slate-800 dark:text-white uppercase tracking-tight">
              {{ group.name }}
            </h2>
            <div class="flex-1 h-1 bg-linear-to-r from-slate-200 dark:from-slate-700 to-transparent rounded-full">
            </div>
            <span class="text-sm font-bold text-slate-400 dark:text-slate-500">
              {{ group.habits.length }} {{ group.habits.length === 1 ? 'habit' : 'habits' }}
            </span>
          </div>

          <!-- Habits Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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

                <!-- Timer Type -->
                <div v-else-if="habit.habit_type === 'timer'" class="flex gap-3">
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
                      class="transition-all hover:scale-110 active:scale-95 shrink-0"
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
                  {{ habit.today_value > 0 ? 'Completed' : 'Mark Complete' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary Tab -->
      <div v-show="activeTab === 'summary'" class="space-y-6">
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-12 shadow-lg border border-slate-100 dark:border-slate-700">
          <h2 class="text-3xl font-black text-slate-900 dark:text-white mb-4">Summary View</h2>
          <p class="text-slate-500 dark:text-slate-400">Retrospective analysis of your habits will appear here.</p>
        </div>
      </div>

      <!-- Graph Tab -->
      <div v-show="activeTab === 'graph'" class="space-y-6">
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-12 shadow-lg border border-slate-100 dark:border-slate-700">
          <h2 class="text-3xl font-black text-slate-900 dark:text-white mb-4">Graph View</h2>
          <p class="text-slate-500 dark:text-slate-400">Visual charts and graphs will appear here.</p>
        </div>
      </div>

      <!-- Export Tab -->
      <div v-show="activeTab === 'export'" class="space-y-6">
        <div
          class="bg-white dark:bg-slate-800 rounded-[3rem] p-12 shadow-lg border border-slate-100 dark:border-slate-700">
          <h2 class="text-3xl font-black text-slate-900 dark:text-white mb-4">Export Data</h2>
          <p class="text-slate-500 dark:text-slate-400">Export options will appear here.</p>
        </div>
      </div>
    </div>

    <!-- Modal for New Habit -->
    <Transition name="fade">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-md" @click="isModalOpen = false"></div>
        <div class="relative bg-white dark:bg-slate-800 w-full max-w-lg rounded-[3rem] p-12 shadow-2xl overflow-hidden">
          <div class="absolute top-0 left-0 w-full h-2 bg-indigo-500"></div>

          <div class="flex justify-between items-center mb-10">
            <h2 class="text-3xl font-black text-slate-900 dark:text-white">New Habit</h2>
            <button @click="isModalOpen = false"
              class="text-slate-300 hover:text-slate-900 dark:hover:text-white transition">
              <X :size="32" />
            </button>
          </div>

          <form @submit.prevent="addHabit" class="space-y-8">
            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Objective Name</label>
              <input v-model="newHabitName" type="text" placeholder="e.g. Daily Sprints" required
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white">
            </div>

            <div class="grid grid-cols-2 gap-6">
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Metric Type</label>
                <select v-model="newHabitType"
                  class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 font-bold outline-none appearance-none text-slate-900 dark:text-white">
                  <option value="boolean">Boolean</option>
                  <option value="counter">Counter</option>
                  <option value="timer">Timer</option>
                  <option value="rating">Rating</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Visual Icon</label>
                <input v-model="newHabitIcon" placeholder="e.g. Beer, Flame"
                  class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 font-bold outline-none text-slate-900 dark:text-white">
              </div>
            </div>

            <!-- Max Value for Rating -->
            <div v-if="newHabitType === 'rating'" class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">
                Number of Stars
              </label>
              <input v-model.number="newHabitMaxValue" type="number" min="1" max="10" placeholder="5"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white">
              <p class="text-xs text-slate-400 ml-2">
                Between 1-10 stars
              </p>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Category</label>
              <select v-model="newHabitCategoryId"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 font-bold outline-none appearance-none text-slate-900 dark:text-white">
                <option :value="null">Uncategorized</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Identity Color</label>
              <div class="flex items-center gap-4 bg-slate-50 dark:bg-slate-700 p-4 rounded-3xl">
                <input v-model="newHabitColor" type="color"
                  class="w-16 h-12 rounded-xl border-none bg-transparent cursor-pointer">
                <span class="font-mono font-bold text-slate-400">{{ newHabitColor }}</span>
              </div>
            </div>

            <button type="submit"
              class="w-full bg-indigo-600 text-white py-6 rounded-4xl font-black text-xl hover:bg-indigo-700 transition-all shadow-xl">
              Initiate Habit
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

input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.category-group {
  user-select: none;
}
</style>