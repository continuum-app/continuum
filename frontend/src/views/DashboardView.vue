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
        <button class="bg-indigo-600 text-white px-4 py-2 rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-700 transition">
          <Plus :size="20" /> New Habit
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="habit in habits" :key="habit.id" 
             class="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all group">
          
          <div class="flex justify-between items-start mb-6">
            <h3 class="text-xl font-bold text-slate-800">{{ habit.name }}</h3>
            <Flame class="text-orange-500" :size="24" v-if="habit.streak > 0" />
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

      <footer class="mt-20 py-8 border-t border-slate-200 text-slate-400 text-sm">
        Joey Courcelles | Apache-2.0
      </footer>
    </div>
  </div>
</template>