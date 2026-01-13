<template>
    <div class="min-h-screen bg-[#f8fafc] flex items-center justify-center p-6">
        <div class="bg-white rounded-[3rem] p-12 shadow-2xl w-full max-w-md">
            <div class="text-center mb-10">
                <h1 class="text-4xl font-black tracking-tighter text-slate-900 uppercase italic mb-2">Continuum</h1>
                <p class="text-slate-400 font-medium">Create your account</p>
            </div>

            <form @submit.prevent="handleRegister" class="space-y-6">
                <div v-if="errorMessage" class="bg-red-50 border-2 border-red-200 rounded-2xl p-4">
                    <p class="text-red-600 text-sm font-semibold">{{ errorMessage }}</p>
                </div>

                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Email</label>
                    <input v-model="email" type="email" required placeholder="you@example.com"
                        class="w-full bg-slate-50 border-2 border-slate-50 rounded-3xl px-6 py-4 focus:bg-white focus:border-indigo-500 transition outline-none font-bold" />
                </div>

                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Password</label>
                    <input v-model="password1" type="password" required placeholder="••••••••"
                        class="w-full bg-slate-50 border-2 border-slate-50 rounded-3xl px-6 py-4 focus:bg-white focus:border-indigo-500 transition outline-none font-bold" />
                </div>

                <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Confirm
                        Password</label>
                    <input v-model="password2" type="password" required placeholder="••••••••"
                        class="w-full bg-slate-50 border-2 border-slate-50 rounded-3xl px-6 py-4 focus:bg-white focus:border-indigo-500 transition outline-none font-bold" />
                </div>

                <button type="submit" :disabled="loading"
                    class="w-full bg-slate-900 text-white py-6 rounded-4xl font-black text-xl hover:bg-indigo-600 transition-all shadow-xl shadow-indigo-100 disabled:opacity-50">
                    {{ loading ? 'Creating account...' : 'Sign Up' }}
                </button>

                <div class="text-center">
                    <p class="text-slate-400 text-sm">
                        Already have an account?
                        <router-link to="/login" class="text-indigo-600 font-bold hover:text-indigo-700">
                            Sign in
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
const password1 = ref('')
const password2 = ref('')
const loading = ref(false)
const errorMessage = ref('')

const handleRegister = async () => {
    loading.value = true
    errorMessage.value = ''

    if (password1.value !== password2.value) {
        errorMessage.value = 'Passwords do not match'
        loading.value = false
        return
    }

    try {
        await authService.register(email.value, password1.value, password2.value)
        // Auto-login after registration
        await authService.login(email.value, password1.value)
        router.push('/dashboard')
    } catch (error) {
        console.error('Registration error:', error)
        errorMessage.value = error.response?.data?.email?.[0] || 'Registration failed. Please try again.'
    } finally {
        loading.value = false
    }
}
</script>