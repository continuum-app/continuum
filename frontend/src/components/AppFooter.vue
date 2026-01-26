<script setup>
import { useRouter } from 'vue-router'
import { useLanguage } from '@/composables/useLanguage'
import { Settings, Download } from 'lucide-vue-next'

const router = useRouter()
const { t } = useLanguage()

const goToAdminSettings = () => {
  router.push('/admin-settings')
}

const goToExport = () => {
  router.push('/export')
}
</script>

<template>
  <footer class="max-w-7xl mx-auto mt-16 pt-8 pb-6 border-t border-slate-200 dark:border-slate-700">
    <div class="flex flex-col md:flex-row justify-between items-center gap-6">
      <!-- GitHub Link -->
      <div class="flex items-center gap-3">
        <a href="https://github.com/habitsfactory/habitsfactory-app" target="_blank" rel="noopener noreferrer"
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
        class="flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-bold transition-all shadow-sm active:scale-95">
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
</template>
