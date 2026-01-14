<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import authService from '../services/auth'
import { useDarkMode } from '../composables/useDarkMode'
import * as LucideIcons from 'lucide-vue-next'
import { Plus, X, ChevronDown, CheckCircle2, RefreshCw, Save, Star, Moon, Sun } from 'lucide-vue-next'

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()

// --- STATE ---
const habits = ref([])
const categories = ref([])
const isModalOpen = ref(false)

// Form Refs for New Habit
const newHabitName = ref('')
const newHabitType = ref('boolean')
const newHabitIcon = ref('calendar')
const newHabitColor = ref('#1F85DE')
const newHabitCategoryId = ref(null)
const newHabitMaxValue = ref(5)

// --- LOGIC ---
const fetchCategories = async () => {
  try {
    const res = await api.get('categories/')
    categories.value = res.data
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
      selected_category_id: h.category?.id || null,
      is_completed_today: h.today_value > 0,
      is_saving: false
    }))
  } catch (err) {
    console.error("Failed to fetch habits:", err)
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
      selected_category_id: res.data.category?.id || null,
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
      category_id: habit.selected_category_id,
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

      <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-16">
        <div>
          <h1 class="text-4xl font-black tracking-tighter text-slate-900 dark:text-white uppercase italic">Continuum
          </h1>
          <p class="text-slate-400 dark:text-slate-500 font-medium">Daily evolution, quantified.</p>
        </div>
        <div class="flex gap-4">
          <!-- Dark Mode Toggle -->
          <button @click="toggleDarkMode"
            class="bg-indigo-600 dark:bg-slate-700 text-white px-6 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-indigo-700 dark:hover:bg-slate-600 transition-all shadow-lg active:scale-95">
            <Moon v-if="!isDark" :size="20" stroke-width="2.5" />
            <Sun v-else :size="20" stroke-width="2.5" />
          </button>

          <button @click="isModalOpen = true"
            class="bg-indigo-600 dark:bg-indigo-600 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-indigo-700 dark:hover:bg-indigo-500 transition-all shadow-lg active:scale-95">
            <Plus :size="20" stroke-width="3" /> New Habit
          </button>
          <button @click="handleLogout"
            class="bg-red-600 dark:bg-red-600 text-white px-8 py-4 rounded-2xl font-bold hover:bg-red-700 dark:hover:bg-red-500 transition-all shadow-lg active:scale-95">
            Logout
          </button>
        </div>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div v-for="habit in habits" :key="habit.id" :class="[
          'relative group p-8 rounded-[3rem] transition-all duration-500 flex flex-col justify-between overflow-hidden border',
          habit.today_value > 0
            ? 'bg-white dark:bg-slate-800 border-transparent shadow-[0_30px_60px_-15px_rgba(0,0,0,0.08)] dark:shadow-[0_30px_60px_-15px_rgba(0,0,0,0.3)]'
            : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-xl dark:hover:shadow-slate-950/50 hover:-translate-y-1'
        ]" :style="{ minHeight: '320px' }">

          <div class="absolute -right-8 -top-8 w-32 h-32 rounded-full blur-3xl opacity-10 dark:opacity-20"
            :style="{ backgroundColor: habit.color }"></div>

          <div class="flex justify-between items-start relative z-10">
            <div class="flex flex-col">
              <span class="text-[10px] font-black uppercase tracking-[0.25em] mb-2 opacity-50"
                :style="{ color: habit.color }">
                {{ habit.habit_type }}
              </span>
              <h3 class="text-2xl font-black text-slate-800 dark:text-white leading-tight">{{ habit.name }}</h3>
              <p v-if="habit.category" class="text-xs font-semibold mt-1 text-slate-400 dark:text-slate-500">
                {{ habit.category.name }}
              </p>
            </div>
            <div class="p-4 rounded-3xl transition-all duration-500" :style="{
              backgroundColor: habit.today_value > 0 ? habit.color : `${habit.color}15`,
              color: habit.today_value > 0 ? 'white' : habit.color
            }">
              <component :is="getIcon(habit.icon)" :size="26" stroke-width="2.5" />
            </div>
          </div>

          <div class="relative z-10 space-y-4">

            <!-- Category Selector -->
            <div v-if="categories.length > 0" class="relative">
              <select v-model="habit.selected_category_id"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-100 dark:border-slate-600 rounded-2xl px-5 py-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 appearance-none outline-none focus:ring-2"
                :style="{ '--tw-ring-color': habit.color }">
                <option :value="null">No Category</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
              <ChevronDown class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                :size="16" />
            </div>

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
                {{ habit.today_value > 0 ? 'Update' : 'Log' }}
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
                {{ habit.today_value > 0 ? 'Update' : 'Log' }}
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
                    :fill="star <= habit.temp_value ? habit.color : 'none'" :stroke="habit.color" stroke-width="2" />
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

            <div v-if="categories.length > 0" class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Category
                (Optional)</label>
              <select v-model="newHabitCategoryId"
                class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 font-bold outline-none appearance-none text-slate-900 dark:text-white">
                <option :value="null">No Category</option>
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
              class="w-full bg-slate-900 dark:bg-indigo-600 text-white py-6 rounded-4xl font-black text-xl hover:bg-indigo-600 dark:hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-100 dark:shadow-none">
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
</style>