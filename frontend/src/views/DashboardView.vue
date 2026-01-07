<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const habits = ref([])

const fetchHabits = async () => {
  try {
    // This calls your Django API
    const response = await axios.get('http://127.0.0.1:8000/api/habits/')
    habits.value = response.data
  } catch (error) {
    console.error("Make sure Django is running!", error)
  }
}

onMounted(fetchHabits)
</script>

<template>
  <div class="p-8 bg-slate-50 min-h-screen">
    <h1 class="text-3xl font-bold text-indigo-600 mb-8">Continuum Dashboard</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div v-for="habit in habits" :key="habit.id" class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h3 class="font-bold text-xl">{{ habit.name }}</h3>
        <p class="text-slate-500">🔥 {{ habit.streak }} day streak</p>
      </div>
    </div>

    <footer class="mt-20 opacity-50 text-sm">
      Project Continuum by Joey Courcelles | Apache-2.0 license
    </footer>
  </div>
</template>