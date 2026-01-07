<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Plus, Flame, CheckCircle } from 'lucide-vue-next'

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

const addHabit = async () => {
  if (!newHabitName.value) return

  try {
    const response = await axios.post('http://127.0.0.1:8000/api/habits/', {
      name: newHabitName.value,
      streak: 0
    })

    // Add the new habit to the list and close modal
    habits.value.push(response.data)
    newHabitName.value = ''
    isModalOpen.value = false
  } catch (error) {
    console.error("Could not save habit", error)
  }
}

onMounted(fetchHabits)
</script>

<template>
  <div class="min-h-screen bg-slate-50 p-6 md:p-12">
    <div class="max-w-5xl mx-auto">

      <div class="flex justify-between items-center mb-10">
        <h1 class="text-3xl font-black text-slate-900 tracking-tight">CONTINUUM</h1>
        <button @click="isModalOpen = true"
          class="bg-indigo-600 text-white px-4 py-2 rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-700 transition">
          <Plus :size="20" /> New Habit
        </button>
      </div>

      <div v-if="habits.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="habit in habits" :key="habit.id"
          class="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all">
          <div class="flex justify-between items-start mb-6">
            <h3 class="text-xl font-bold text-slate-800">{{ habit.name }}</h3>
            <Flame v-if="habit.streak > 0" class="text-orange-500" :size="24" />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-4xl font-black text-slate-900">{{ habit.streak }}</p>
              <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Day Streak</p>
            </div>
            <button @click="completeHabit(habit)"
              class="bg-slate-900 text-white p-4 rounded-2xl hover:bg-indigo-600 transition-colors">
              <CheckCircle :size="24" />
            </button>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-20 bg-white rounded-3xl border-2 border-dashed border-slate-200">
        <p class="text-slate-400 font-medium">No habits yet. Click "New Habit" to start!</p>
      </div>

      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="isModalOpen = false"></div>
        <div class="relative bg-white w-full max-w-md rounded-[2.5rem] p-10 shadow-2xl">
          <h2 class="text-2xl font-black mb-6">New Habit</h2>
          <input v-model="newHabitName" type="text"
            class="w-full bg-slate-50 border-2 border-slate-100 rounded-2xl px-5 py-4 mb-6" placeholder="Habit Name">
          <div class="flex gap-3">
            <button @click="isModalOpen = false" class="flex-1 font-bold text-slate-400">Cancel</button>
            <button @click="addHabit" class="flex-1 bg-slate-900 text-white py-4 rounded-2xl font-bold">Create</button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>