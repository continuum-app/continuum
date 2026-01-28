<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import authService from '@/services/auth'
import { useDarkMode } from '@/composables/useDarkMode'
import { useLanguage } from '@/composables/useLanguage'
import { ArrowLeft, Save, Moon, Sun, Settings, RefreshCw, CheckCircle2 } from 'lucide-vue-next'
import SiteFooter from '@/components/SiteFooter.vue'

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
        class="min-h-screen bg-neutral-50 dark:bg-neutral-900 p-6 md:p-12 font-sans text-neutral-900 dark:text-neutral-100 transition-colors duration-300">
        <div class="max-w-5xl mx-auto">
            <!-- Header -->
            <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                <div>
                    <button @click="goBack"
                        class="flex items-center gap-2 text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors mb-4 font-bold">
                        <ArrowLeft :size="20" stroke-width="2.5" />
                        {{ t('returnDashboard') }}
                    </button>
                    <h1 class="text-4xl font-black tracking-tighter text-neutral-900 dark:text-white uppercase italic">
                        Admin Settings
                    </h1>
                    <p class="text-neutral-400 dark:text-neutral-500 font-medium">Site-wide settings for administrators</p>
                </div>
            </header>

            <div class="space-y-6">

                <!-- Site-Wide Settings (Admin Only) -->
                <div v-if="userInfo.is_staff || userInfo.is_superuser"
                    class="bg-white dark:bg-neutral-800 rounded-4xl p-8 shadow-lg border border-neutral-100 dark:border-neutral-700">
                    <div class="flex items-center gap-3 mb-6">
                        <div class="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl">
                            <Settings :size="24" class="text-emerald-600 dark:text-emerald-400" stroke-width="2.5" />
                        </div>
                        <div class="flex-1">
                            <h2 class="text-2xl font-black text-neutral-900 dark:text-white">Site-Wide Settings</h2>
                            <p class="text-sm text-neutral-500 dark:text-neutral-400 font-medium">Admin only - affects all
                                users</p>
                        </div>
                    </div>

                    <div class="space-y-6">
                        <!-- Registration Toggle -->
                        <div class="flex items-center justify-between p-6 bg-neutral-50 dark:bg-neutral-700 rounded-2xl">
                            <div class="flex-1">
                                <h3 class="font-black text-neutral-900 dark:text-white text-lg mb-1">User Registration
                                </h3>
                                <p class="text-sm text-neutral-500 dark:text-neutral-400">
                                    Allow new users to register accounts on the site
                                </p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer ml-4">
                                <input type="checkbox" v-model="siteSettings.allow_registration" class="sr-only peer">
                                <div
                                    class="w-14 h-7 bg-neutral-300 dark:bg-neutral-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 dark:peer-focus:ring-emerald-800 rounded-full peer peer-checked:after:tranneutral-x-full rtl:peer-checked:after:-tranneutral-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:start-1 after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all dark:border-neutral-600 peer-checked:bg-emerald-600">
                                </div>
                                <span class="ml-3 text-sm font-bold text-neutral-900 dark:text-white">
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
                <SiteFooter />
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Custom styles if needed */
</style>