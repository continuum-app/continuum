<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import authService from '../services/auth'
import { useDarkMode } from '../composables/useDarkMode'
import { useLanguage } from '@/composables/useLanguage'
import { ArrowLeft, Save, Moon, Sun, Settings, RefreshCw, CheckCircle2 } from 'lucide-vue-next'

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()
const { t } = useLanguage()

// State
const userInfo = ref({
    username: '',
    email: '',
    is_staff: false,
    is_superuser: false
})
const siteSettings = ref({
    allow_registration: true
})
const isSavingSettings = ref(false)
const settingsSaved = ref(false)

// Fetch user info
const fetchUserInfo = async () => {
    try {
        const res = await api.get('auth/user/')
        userInfo.value = res.data
    } catch (err) {
        console.error('Failed to fetch user info:', err)
    }
}

// Fetch site settings
const fetchSiteSettings = async () => {
    try {
        const res = await api.get('settings/')
        siteSettings.value = res.data
    } catch (err) {
        console.error('Failed to fetch site settings:', err)
    }
}

// Update site settings
const updateSiteSettings = async () => {
    isSavingSettings.value = true
    const startTime = Date.now()

    try {
        const response = await api.post('settings/update_settings/', {
            allow_registration: siteSettings.value.allow_registration
        })
        console.log('Settings updated successfully:', response.data)

        // Ensure spinner shows for at least 500ms for better UX
        const elapsedTime = Date.now() - startTime
        const remainingTime = Math.max(0, 500 - elapsedTime)

        await new Promise(resolve => setTimeout(resolve, remainingTime))

        // Set saved state to true
        settingsSaved.value = true

        // Refresh settings
        await fetchSiteSettings()

        // Hide saved message after 3 seconds
        setTimeout(() => {
            settingsSaved.value = false
        }, 3000)
    } catch (err) {
        console.error('Failed to update site settings:', err)
        console.error('Error status:', err.response?.status)
        console.error('Error data:', err.response?.data)
        console.error('Request config:', err.config)

        // More specific error messages
        if (err.response?.status === 403) {
            alert('Permission denied. Only admin users can modify site settings.')
        } else if (err.response?.status === 404) {
            alert('Settings endpoint not found. Please check your API configuration.')
        } else if (err.response?.data?.detail) {
            alert(`Error: ${err.response.data.detail}`)
        } else {
            alert('Failed to update site settings. Please check console for details.')
        }
    } finally {
        isSavingSettings.value = false
    }
}

const goBack = () => {
    router.push('/dashboard')
}

const handleLogout = () => {
    authService.logout()
    router.push('/login')
}

// Watch for changes to settings to reset saved state
watch(siteSettings, () => {
    settingsSaved.value = false
}, { deep: true })

onMounted(() => {
    fetchUserInfo()
    fetchSiteSettings()
})
</script>

<template>
    <div
        class="min-h-screen bg-slate-50 dark:bg-slate-900 p-6 md:p-12 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-300">
        <div class="max-w-5xl mx-auto">
            <!-- Header -->
            <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                <div>
                    <button @click="goBack"
                        class="flex items-center gap-2 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors mb-4 font-bold">
                        <ArrowLeft :size="20" stroke-width="2.5" />
                        Back to Dashboard
                    </button>
                    <h1 class="text-4xl font-black tracking-tighter text-slate-900 dark:text-white uppercase italic">
                        Admin Settings
                    </h1>
                    <p class="text-slate-400 dark:text-slate-500 font-medium">Site-wide settings for administrators</p>
                </div>
            </header>

            <div class="space-y-6">

                <!-- Site-Wide Settings (Admin Only) -->
                <div v-if="userInfo.is_staff || userInfo.is_superuser"
                    class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
                    <div class="flex items-center gap-3 mb-6">
                        <div class="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl">
                            <Settings :size="24" class="text-emerald-600 dark:text-emerald-400" stroke-width="2.5" />
                        </div>
                        <div class="flex-1">
                            <h2 class="text-2xl font-black text-slate-900 dark:text-white">Site-Wide Settings</h2>
                            <p class="text-sm text-slate-500 dark:text-slate-400 font-medium">Admin only - affects all
                                users</p>
                        </div>
                    </div>

                    <div class="space-y-6">
                        <!-- Registration Toggle -->
                        <div class="flex items-center justify-between p-6 bg-slate-50 dark:bg-slate-700 rounded-2xl">
                            <div class="flex-1">
                                <h3 class="font-black text-slate-900 dark:text-white text-lg mb-1">User Registration
                                </h3>
                                <p class="text-sm text-slate-500 dark:text-slate-400">
                                    Allow new users to register accounts on the site
                                </p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer ml-4">
                                <input type="checkbox" v-model="siteSettings.allow_registration" class="sr-only peer">
                                <div
                                    class="w-14 h-7 bg-slate-300 dark:bg-slate-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 dark:peer-focus:ring-emerald-800 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:start-1 after:bg-white after:border-slate-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all dark:border-slate-600 peer-checked:bg-emerald-600">
                                </div>
                                <span class="ml-3 text-sm font-bold text-slate-900 dark:text-white">
                                    {{ siteSettings.allow_registration ? 'Enabled' : 'Disabled' }}
                                </span>
                            </label>
                        </div>

                        <!-- Save Button -->
                        <button @click="updateSiteSettings" :disabled="isSavingSettings || settingsSaved" :class="[
                            'w-full px-8 py-4 rounded-2xl font-bold transition-all shadow-md active:scale-95 disabled:cursor-not-allowed flex items-center justify-center gap-2',
                            settingsSaved
                                ? 'bg-green-600 text-white'
                                : 'bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50'
                        ]">
                            <RefreshCw v-if="isSavingSettings" :size="20" class="animate-spin" />
                            <CheckCircle2 v-else-if="settingsSaved" :size="20" stroke-width="2.5" />
                            <Save v-else :size="20" stroke-width="2.5" />
                            {{ isSavingSettings ? 'Saving...' : settingsSaved ? 'Site Settings Saved' : 'Save Site Settings' }}
                        </button>
                    </div>
                </div>

                <!-- Footer -->
                <footer class="max-w-7xl mx-auto mt-16 pt-8 pb-6 border-t border-slate-200 dark:border-slate-700">
                    <div class="flex flex-col md:flex-row justify-between items-center gap-6">
                        <!-- GitHub Link -->
                        <div class="flex items-center gap-3">
                            <a href="https://github.com/habitsfactory/habitsfactory-app" target="_blank"
                                rel="noopener noreferrer"
                                class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors font-medium flex items-center gap-2 group">
                                <svg class="w-5 h-5 group-hover:scale-110 transition-transform" fill="currentColor"
                                    viewBox="0 0 24 24">
                                    <path fill-rule="evenodd"
                                        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                                        clip-rule="evenodd" />
                                </svg>
                                <span class="text-sm font-bold">{{ t('viewOnGithub') }}</span>
                            </a>
                        </div>

                    </div>

                    <!-- Copyright -->
                    <div class="text-center mt-6">
                        <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">
                            © {{ new Date().getFullYear() }} {{ t('appName') }}. {{ t('allRightsReserved') }}
                        </p>
                    </div>
                </footer>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Custom styles if needed */
</style>