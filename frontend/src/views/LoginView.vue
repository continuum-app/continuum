<template>
    <div class="min-h-screen bg-neutral-50 dark:bg-neutral-900 flex items-center justify-center p-6">
        <div class="bg-white rounded-[3rem] p-12 shadow-2xl w-full max-w-md">
            <div class="text-center mb-10">
                <h1 class="text-4xl font-black tracking-tighter text-neutral-900 uppercase italic mb-2">Habits Factory</h1>
                <p class="text-neutral-400 font-medium">Sign in to continue</p>
            </div>

            <form @submit.prevent="handleLogin" class="space-y-6">
                <div v-if="errorMessage" class="bg-red-50 border-2 border-red-200 rounded-2xl p-4">
                    <p class="text-red-600 text-sm font-semibold">{{ errorMessage }}</p>
                </div>

                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-neutral-400 ml-2">Email</label>
                    <input v-model="email" type="email" required placeholder="you@example.com"
                        class="w-full bg-neutral-50 border-2 border-neutral-50 rounded-3xl px-6 py-4 focus:bg-white focus:border-yellow-500 transition outline-none font-bold" />
                </div>

                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-neutral-400 ml-2">Password</label>
                    <input v-model="password" type="password" required placeholder="••••••••"
                        class="w-full bg-neutral-50 border-2 border-neutral-50 rounded-3xl px-6 py-4 focus:bg-white focus:border-yellow-500 transition outline-none font-bold" />
                </div>

                <button type="submit" :disabled="loading"
                    class="w-full bg-neutral-900 text-white py-6 rounded-4xl font-black text-xl hover:bg-yellow-600 transition-all shadow-xl shadow-yellow-100 disabled:opacity-50">
                    {{ loading ? 'Signing in...' : 'Sign In' }}
                </button>

                <div class="text-center">
                    <p class="text-neutral-400 text-sm">
                        Don't have an account?
                        <router-link to="/register" class="text-yellow-600 font-bold hover:text-yellow-700">
                            Sign up
                        </router-link>
                    </p>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import authService from '../services/auth'

const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
    loading.value = true
    errorMessage.value = ''

    try {
        await authService.login(email.value, password.value)
        router.push('/dashboard')
    } catch (error) {
        console.error('Login error:', error)
        errorMessage.value = error.response?.data?.non_field_errors?.[0] || 'Invalid email or password'
    } finally {
        loading.value = false
    }
}
</script>