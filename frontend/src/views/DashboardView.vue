<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import authService from '@/services/auth'
import { useDarkMode } from '@/composables/useDarkMode'
import { useLanguage } from '@/composables/useLanguage'
import { useHabits } from '@/composables/useHabits'
import { useCategories } from '@/composables/useCategories'
import { Plus, X, ChevronDown, Moon, Sun, BarChart3, FileText, Calendar, Languages, Check, Brain, LogOut } from 'lucide-vue-next'
import IconPicker from '@/components/IconPicker.vue'
import TrackingTab from '@/components/TrackingTab.vue'
import InsightsTab from '@/components/InsightsTab.vue'
import SummaryTab from '@/components/SummaryTab.vue'
import GraphTab from '@/components/GraphTab.vue'
import SiteFooter from '@/components/SiteFooter.vue'

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()
const { currentLanguage, setLanguage, languages, currentLanguageInfo, t } = useLanguage()
const { addHabit: addHabitApi } = useHabits()
const { categories, fetchCategories } = useCategories()

// Language dropdown state
const isLanguageDropdownOpen = ref(false)

// --- STATE ---
const isModalOpen = ref(false)
const activeTab = ref('tracking')

// Form Refs for New Habit
const newHabitName = ref('')
const newHabitType = ref('boolean')
const newHabitIcon = ref('calendar')
const newHabitColor = ref('#d97706')
const newHabitCategoryId = ref(null)
const newHabitMaxValue = ref(5)


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
    newHabitColor.value = '#d97706'
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

onMounted(() => {
  fetchCategories()
  document.addEventListener('click', closeLanguageDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeLanguageDropdown)
})

</script>

<template>
  <div
    class="min-h-screen bg-neutral-50 dark:bg-neutral-900 p-6 md:p-12 text-neutral-900 dark:text-neutral-100 transition-colors duration-300">
    <div class="max-w-7xl mx-auto">
      <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
        <div class="flex items-center gap-4">
          <img src="/logo.png" alt="App Logo" class="h-22 w-22" />
          <div>
            <h1 class="text-4xl font-black tracking-tighter text-neutral-900 dark:text-white uppercase italic">
              {{ t('appName') }}
            </h1>
            <p class="text-neutral-400 dark:text-neutral-500 font-medium">{{ t('tagline') }}</p>
          </div>
        </div>
        <div class="flex gap-4">
          <!-- Language Selector -->
          <div class="relative language-dropdown-container">
            <button @click="isLanguageDropdownOpen = !isLanguageDropdownOpen"
              class="bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 px-6 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-neutral-300 dark:hover:bg-neutral-600 transition-all shadow-md active:scale-95">
              <Languages :size="20" stroke-width="2.5" />
              <span class="text-xl">{{ currentLanguageInfo.flag }}</span>
              <ChevronDown :size="16" stroke-width="2.5" :class="{ 'rotate-180': isLanguageDropdownOpen }"
                class="transition-transform" />
            </button>

            <!-- Language Dropdown -->
            <Transition name="dropdown">
              <div v-if="isLanguageDropdownOpen"
                class="absolute top-full mt-2 right-0 bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl border border-neutral-200 dark:border-neutral-700 py-2 min-w-50 z-50">
                <button v-for="lang in languages" :key="lang.code" @click="selectLanguage(lang.code)"
                  class="w-full px-4 py-3 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors flex items-center gap-3 text-left">
                  <span class="text-xl">{{ lang.flag }}</span>
                  <span class="font-bold text-neutral-900 dark:text-white">{{ lang.name }}</span>
                  <Check v-if="currentLanguage === lang.code" :size="16"
                    class="ml-auto text-yellow-600 dark:text-yellow-400" stroke-width="3" />
                </button>
              </div>
            </Transition>
          </div>

          <!-- Dark Mode Toggle -->
          <button @click="toggleDarkMode"
            class="bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-yellow-400 px-6 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-neutral-300 dark:hover:bg-neutral-600 transition-all shadow-md active:scale-95">
            <Moon v-if="!isDark" :size="20" stroke-width="2.5" />
            <Sun v-else :size="20" stroke-width="2.5" />
          </button>

          <button @click="isModalOpen = true"
            class="bg-primary-600 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-primary-800 transition-all shadow-md active:scale-95">
            <Plus :size="20" stroke-width="3" /> {{ t('newHabit') }}
          </button>

          <button @click="handleLogout"
            class="bg-red-500 text-white px-6 py-4 rounded-2xl font-bold hover:bg-red-700 transition-all shadow-md active:scale-95">
            <LogOut :size="20" stroke-width="2.5" />
          </button>
        </div>
      </header>

      <!-- Tabs Navigation -->
      <div class="mb-6">
        <div
          class="flex gap-2 p-2 bg-white dark:bg-neutral-800 rounded-3xl shadow-md border border-neutral-100 dark:border-neutral-700">
          <button @click="activeTab = 'tracking'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'tracking'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700'
          ]">
            <Calendar :size="20" stroke-width="2.5" />
            <span>{{ t('tracking') }}</span>
          </button>

          <button @click="activeTab = 'summary'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'summary'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700'
          ]">
            <FileText :size="20" stroke-width="2.5" />
            <span>{{ t('summary') }}</span>
          </button>

          <button @click="activeTab = 'graph'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'graph'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700'
          ]">
            <BarChart3 :size="20" stroke-width="2.5" />
            <span>{{ t('graph') }}</span>
          </button>

          <button @click="activeTab = 'insights'" :class="[
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold transition-all',
            activeTab === 'insights'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700'
          ]">
            <Brain :size="20" stroke-width="2.5" />
            <span>{{ t('insights') }}</span>
          </button>
        </div>
      </div>

      <!-- Tab Content -->

      <!-- Tracking Tab -->
      <TrackingTab v-show="activeTab === 'tracking'" />

      <!-- Summary Tab -->
      <SummaryTab v-show="activeTab === 'summary'" />

      <!-- Graph Tab -->
      <GraphTab v-show="activeTab === 'graph'" />

      <!-- Insights Tab -->
      <InsightsTab v-show="activeTab === 'insights'" />
    </div>

    <SiteFooter />

    <!-- Modal for New Habit -->
    <Transition name="fade">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-neutral-900/60 backdrop-blur-md" @click="isModalOpen = false"></div>
        <div
          class="relative z-10 bg-white dark:bg-neutral-800 w-full max-w-lg rounded-4xl p-12 shadow-2xl overflow-hidden">
          <div class="absolute top-0 left-0 right-0 h-2 bg-primary-600"></div>

          <div class="flex justify-between items-center mb-10">
            <h2 class="text-3xl font-black text-neutral-900 dark:text-white">{{ t('newHabit') }}</h2>
            <button @click="isModalOpen = false"
              class="text-neutral-300 hover:text-neutral-900 dark:hover:text-white transition">
              <X :size="32" />
            </button>
          </div>

          <form @submit.prevent="addHabit" class="space-y-8">
            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-neutral-400 ml-2">{{
                t('objectiveName')
              }}</label>
              <input v-model="newHabitName" type="text" placeholder="e.g. Daily Sprints" required
                class="w-full bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-50 dark:border-neutral-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-neutral-600 focus:border-yellow-500 transition outline-none font-bold text-lg text-neutral-900 dark:text-white">
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-neutral-400 ml-2">{{ t('metricType')
              }}</label>
              <select v-model="newHabitType"
                class="w-full bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-50 dark:border-neutral-700 rounded-3xl px-6 py-4 font-bold outline-none appearance-none text-neutral-900 dark:text-white">
                <option value="boolean">{{ t('boolean') }}</option>
                <option value="counter">{{ t('counter') }}</option>
                <option value="value">{{ t('value') }}</option>
                <option value="rating">{{ t('rating') }}</option>
              </select>
            </div>

            <IconPicker v-model="newHabitIcon" :label="t('visualIcon')" />

            <!-- Max Value for Rating -->
            <div v-if="newHabitType === 'rating'" class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-neutral-400 ml-2">
                {{ t('numberOfStars') }}
              </label>
              <input v-model.number="newHabitMaxValue" type="number" min="1" max="10" placeholder="5"
                class="w-full bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-50 dark:border-neutral-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-neutral-600 focus:border-yellow-500 transition outline-none font-bold text-lg text-neutral-900 dark:text-white">
              <p class="text-xs text-neutral-400 ml-2">
                Between 1-10 stars
              </p>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-neutral-400 ml-2">{{ t('category')
              }}</label>
              <select v-model="newHabitCategoryId"
                class="w-full bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-50 dark:border-neutral-700 rounded-3xl px-6 py-4 font-bold outline-none appearance-none text-neutral-900 dark:text-white">
                <option :value="null">{{ t('uncategorized') }}</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-neutral-400 ml-2">{{
                t('identityColor')
              }}</label>
              <div class="flex items-center gap-4 bg-neutral-50 dark:bg-neutral-700 p-4 rounded-3xl">
                <input v-model="newHabitColor" type="color"
                  class="w-16 h-12 rounded-xl border-none bg-transparent cursor-pointer">
                <span class="font-mono font-bold text-neutral-400">{{ newHabitColor }}</span>
              </div>
            </div>

            <button type="submit"
              class="w-full bg-yellow-600 text-white py-6 rounded-4xl font-black text-xl hover:bg-yellow-700 transition-all shadow-xl">
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
  transform: tranneutralY(-10px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: tranneutralY(-5px);
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