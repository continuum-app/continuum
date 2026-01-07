<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import * as LucideIcons from 'lucide-vue-next'
import { Plus } from 'lucide-vue-next'

const habits = ref([])

// Fetch all habits from Django
const fetchHabits = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/habits/')
  habits.value = res.data
}

// Logic to increment a streak
const completeHabit = async (habit) => {
  try {
    const updatedStreak = habit.streak + 1
    await axios.patch(`http://127.0.0.1:8000/api/habits/${habit.id}/`, {
      streak: updatedStreak
    })
    habit.streak = updatedStreak // Update UI immediately
  } catch (err) {
    console.error("Update failed", err)
  }
}

const isModalOpen = ref(false)
const newHabitName = ref('')
const newHabitIcon = ref('Activity')
const newHabitColor = ref('#6366f1')

const addHabit = async () => {
  if (!newHabitName.value) return
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/habits/', {
      name: newHabitName.value,
      icon: newHabitIcon.value,
      color: newHabitColor.value
    })
    
    habits.value.push(response.data)
    
    // Reset form and close
    newHabitName.value = ''
    newHabitIcon.value = 'Activity'
    isModalOpen.value = false
  } catch (error) {
    console.error("Could not save habit", error)
  }
}

const getIcon = (iconName) => {
  const searchName = iconName.toLowerCase();
  const key = Object.keys(LucideIcons).find(
    (k) => k.toLowerCase() === searchName
  );
  return LucideIcons[key] || LucideIcons.Activity;
}

const toggleHabit = async (habit) => {
  try {
    if (habit.is_completed_today) {
      // Logic to 'uncheck' if you want, or just return
      return
    }

    // Call an endpoint to register today's completion
    await axios.post(`http://127.0.0.1:8000/api/habits/${habit.id}/complete/`)
    habit.is_completed_today = true
  } catch (error) {
    console.error("Action failed", error)
  }
}

onMounted(fetchHabits)
</script>

<template>
  <div class="min-h-screen bg-slate-50 p-8">
    <div class="max-w-6xl mx-auto">

      <div class="flex justify-between items-center mb-12">
        <h1 class="text-3xl font-black text-slate-900 tracking-tighter">CONTINUUM</h1>
        <button @click="isModalOpen = true"
          class="bg-indigo-600 text-white px-6 py-3 rounded-2xl font-bold flex items-center gap-2 hover:bg-indigo-700 transition shadow-lg shadow-indigo-100">
          <Plus :size="20" /> New Habit
        </button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="habit in habits" :key="habit.id" @click="toggleHabit(habit)" :class="[
          'group relative p-8 rounded-[2.5rem] transition-all duration-500 cursor-pointer border-2',
          habit.is_completed_today
            ? 'bg-white border-transparent shadow-xl scale-[0.98]'
            : 'bg-slate-100/50 border-slate-200 opacity-60 hover:opacity-100 hover:bg-white'
        ]">

          <div class="flex flex-col items-center text-center">
            <div class="mb-4 p-5 rounded-3xl transition-all duration-500" :style="{
              backgroundColor: habit.is_completed_today ? habit.color : '#cbd5e1',
              color: habit.is_completed_today ? 'white' : '#64748b',
              boxShadow: habit.is_completed_today ? `0 10px 25px -5px ${habit.color}50` : 'none'
            }">
              <component :is="getIcon(habit.icon)" :size="32" />
            </div>
            <h3 class="text-xl font-extrabold tracking-tight transition-colors"
              :class="habit.is_completed_today ? 'text-slate-900' : 'text-slate-400'">
              {{ habit.name }}
            </h3>

            <p v-if="habit.is_completed_today"
              class="text-[10px] font-black uppercase tracking-[0.2em] text-green-500 mt-3 animate-pulse">
              Completed Today
            </p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="isModalOpen = false"></div>

      <div class="relative bg-white w-full max-w-md rounded-[2.5rem] p-10 shadow-2xl">
        <div class="flex justify-between items-center mb-8">
          <h2 class="text-2xl font-black text-slate-900">New Habit</h2>
          <button @click="isModalOpen = false" class="text-slate-400 hover:text-slate-600 transition">
            <X :size="24" />
          </button>
        </div>

        <form @submit.prevent="addHabit" class="space-y-6">
          <div>
            <label class="block text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Habit Name</label>
            <input v-model="newHabitName" type="text" placeholder="e.g. Morning Run"
              class="w-full bg-slate-50 border-2 border-slate-100 rounded-2xl px-5 py-4 focus:border-indigo-500 focus:outline-none transition font-bold text-lg"
              autofocus>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Icon Name</label>
              <input v-model="newHabitIcon" type="text" placeholder="Flame, Heart..."
                class="w-full bg-slate-50 border-2 border-slate-100 rounded-2xl px-5 py-3 focus:border-indigo-500 focus:outline-none transition font-bold">
            </div>
            <div>
              <label class="block text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Color (Hex)</label>
              <input v-model="newHabitColor" type="color"
                class="w-full h-[52px] bg-slate-50 border-2 border-slate-100 rounded-2xl p-1 focus:border-indigo-500 focus:outline-none transition">
            </div>
          </div>

          <button type="submit"
            class="w-full bg-slate-900 text-white py-5 rounded-2xl font-bold text-lg hover:bg-indigo-600 transition shadow-xl shadow-slate-200 mt-4">
            Create Habit
          </button>
        </form>
      </div>
    </div>
  </div>
</template>