<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import * as LucideIcons from 'lucide-vue-next'
import { Plus, X, ChevronDown, CheckCircle2, RefreshCw, Save } from 'lucide-vue-next'

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

// --- LOGIC ---
const fetchCategories = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/categories/')
    categories.value = res.data
  } catch (err) {
    console.error("Failed to fetch categories:", err)
  }
}

const fetchHabits = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/habits/')
    // Initialize local UI state for each habit so inputs are reactive
    habits.value = res.data.map(h => ({
      ...h,
      // Sync temp_value with the today_value from Django
      temp_value: h.today_value || 0,
      selected_category_id: h.category?.id || null,
      // Boolean check to see if it's been touched today
      is_completed_today: h.today_value > 0,
      is_saving: false
    }))
  } catch (err) {
    console.error("Failed to fetch habits:", err)
  }
}

const addHabit = async () => {
  if (!newHabitName.value) return

  // Format Icon Name to PascalCase (e.g., 'beer' -> 'Beer')
  const formattedIcon = newHabitIcon.value.charAt(0).toUpperCase() + newHabitIcon.value.slice(1).toLowerCase()

  try {
    const payload = {
      name: newHabitName.value,
      habit_type: newHabitType.value,
      icon: formattedIcon,
      color: newHabitColor.value
    }

    // Only add category_id if one was selected
    if (newHabitCategoryId.value) {
      payload.category_id = newHabitCategoryId.value
    }

    const res = await axios.post('http://127.0.0.1:8000/api/habits/', payload)

    // Add to list with necessary UI helper properties
    habits.value.push({
      ...res.data,
      temp_value: 0,
      selected_category_id: res.data.category?.id || null,
      is_completed_today: false,
      is_saving: false
    })

    // Reset and Close
    newHabitName.value = ''
    newHabitType.value = 'boolean'
    newHabitIcon.value = 'calendar'
    newHabitColor.value = '#1F85DE'
    newHabitCategoryId.value = null
    isModalOpen.value = false
  } catch (err) {
    console.error("Error creating habit:", err)
  }
}

const saveCompletion = async (habit) => {
  habit.is_saving = true
  try {
    const payload = {
      category_id: habit.selected_category_id,
      value: habit.habit_type === 'boolean' ? 1 : habit.temp_value
    }

    await axios.post(`http://127.0.0.1:8000/api/habits/${habit.id}/complete/`, payload)

    // This is the important part: update today_value to trigger the UI changes
    habit.today_value = payload.value
    habit.is_completed_today = true
  } catch (err) {
    console.error("Logging failed:", err)
  } finally {
    setTimeout(() => { habit.is_saving = false }, 500)
  }
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
  <div class="min-h-screen bg-[#f8fafc] p-6 md:p-12 font-sans text-slate-900">
    <div class="max-w-7xl mx-auto">

      <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-16">
        <div>
          <h1 class="text-4xl font-black tracking-tighter text-slate-900 uppercase italic">Continuum</h1>
          <p class="text-slate-400 font-medium">Daily evolution, quantified.</p>
        </div>
        <button @click="isModalOpen = true"
          class="bg-slate-900 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-indigo-600 transition-all shadow-2xl shadow-slate-200 active:scale-95">
          <Plus :size="20" stroke-width="3" /> New Habit
        </button>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div v-for="habit in habits" :key="habit.id" :class="[
          'relative group p-8 rounded-[3rem] transition-all duration-500 flex flex-col justify-between overflow-hidden border',
          habit.today_value > 0
            ? 'bg-white border-transparent shadow-[0_30px_60px_-15px_rgba(0,0,0,0.08)]'
            : 'bg-white border-slate-100 shadow-sm hover:shadow-xl hover:-translate-y-1'
        ]" :style="{ minHeight: '320px' }">

          <div class="absolute -right-8 -top-8 w-32 h-32 rounded-full blur-3xl opacity-10"
            :style="{ backgroundColor: habit.color }"></div>

          <div class="flex justify-between items-start relative z-10">
            <div class="flex flex-col">
              <span class="text-[10px] font-black uppercase tracking-[0.25em] mb-2 opacity-50"
                :style="{ color: habit.color }">
                {{ habit.habit_type }}
              </span>
              <h3 class="text-2xl font-black text-slate-800 leading-tight">{{ habit.name }}</h3>
              <p v-if="habit.category" class="text-xs font-semibold mt-1 text-slate-400">
                {{ habit.category.name }}
              </p>
              <p v-if="habit.today_value > 0" class="text-sm font-bold mt-1" :style="{ color: habit.color }">
                Today: {{ Number(habit.today_value).toFixed(0) }}
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

            <!-- Category Selector (optional) -->
            <div v-if="categories.length > 0" class="relative">
              <select v-model="habit.selected_category_id"
                class="w-full bg-slate-50 border border-slate-100 rounded-2xl px-5 py-3.5 text-sm font-bold text-slate-700 appearance-none outline-none focus:ring-2"
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
                class="flex-1 flex justify-between items-center bg-slate-50 rounded-2xl p-1.5 border border-slate-100">
                <button @click="habit.temp_value = Math.max(0, Number(habit.temp_value) - 1)"
                  class="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-white transition text-slate-400 font-bold">
                  -
                </button>

                <span class="font-black text-slate-800 text-lg">
                  {{ Number(habit.temp_value).toFixed(0) }}
                </span>

                <button @click="habit.temp_value = Number(habit.temp_value) + 1"
                  class="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-white transition text-slate-400 font-bold">
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
                  class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl font-bold outline-none focus:ring-2"
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

            <!-- Boolean Type -->
            <button v-else @click="saveCompletion(habit)"
              class="w-full py-4 rounded-2xl font-bold text-white transition-all flex items-center justify-center gap-2 active:scale-95"
              :style="{
                backgroundColor: habit.today_value > 0 ? '#10b981' : habit.color,
                boxShadow: habit.today_value > 0 ? '0 15px 30px -10px #10b98160' : `0 15px 30px -10px ${habit.color}40`
              }">
              <CheckCircle2 v-if="habit.today_value > 0" :size="20" />
              {{ habit.today_value > 0 ? 'Success' : 'Complete' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for New Habit -->
    <Transition name="fade">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-md" @click="isModalOpen = false"></div>
        <div class="relative bg-white w-full max-w-lg rounded-[3rem] p-12 shadow-2xl overflow-hidden">
          <div class="absolute top-0 left-0 w-full h-2 bg-indigo-500"></div>

          <div class="flex justify-between items-center mb-10">
            <h2 class="text-3xl font-black text-slate-900">New Habit</h2>
            <button @click="isModalOpen = false" class="text-slate-300 hover:text-slate-900 transition">
              <X :size="32" />
            </button>
          </div>

          <form @submit.prevent="addHabit" class="space-y-8">
            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Objective Name</label>
              <input v-model="newHabitName" type="text" placeholder="e.g. Daily Sprints" required
                class="w-full bg-slate-50 border-2 border-slate-50 rounded-3xl px-6 py-4 focus:bg-white focus:border-indigo-500 transition outline-none font-bold text-lg">
            </div>

            <div class="grid grid-cols-2 gap-6">
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Metric Type</label>
                <select v-model="newHabitType"
                  class="w-full bg-slate-50 border-2 border-slate-50 rounded-3xl px-6 py-4 font-bold outline-none appearance-none">
                  <option value="boolean">Boolean</option>
                  <option value="counter">Counter</option>
                  <option value="timer">Timer</option>
                  <option value="rating">Rating</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Visual Icon</label>
                <input v-model="newHabitIcon" placeholder="e.g. Beer, Flame"
                  class="w-full bg-slate-50 border-2 border-slate-50 rounded-3xl px-6 py-4 font-bold outline-none">
              </div>
            </div>

            <div v-if="categories.length > 0" class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Category
                (Optional)</label>
              <select v-model="newHabitCategoryId"
                class="w-full bg-slate-50 border-2 border-slate-50 rounded-3xl px-6 py-4 font-bold outline-none appearance-none">
                <option :value="null">No Category</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Identity Color</label>
              <div class="flex items-center gap-4 bg-slate-50 p-4 rounded-3xl">
                <input v-model="newHabitColor" type="color"
                  class="w-16 h-12 rounded-xl border-none bg-transparent cursor-pointer">
                <span class="font-mono font-bold text-slate-400">{{ newHabitColor }}</span>
              </div>
            </div>

            <button type="submit"
              class="w-full bg-slate-900 text-white py-6 rounded-4xl font-black text-xl hover:bg-indigo-600 transition-all shadow-xl shadow-indigo-100">
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