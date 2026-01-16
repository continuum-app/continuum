<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import authService from '../services/auth'
import { useDarkMode } from '../composables/useDarkMode'
import { ArrowLeft, Save, Trash2, Plus, X, Moon, Sun, User, Mail, Lock, Database } from 'lucide-vue-next'

const router = useRouter()
const { isDark, toggleDarkMode } = useDarkMode()

// State
const categories = ref([])
const userInfo = ref({
    username: '',
    email: ''
})
const isLoading = ref(false)
const isSavingCategory = ref(false)
const isDeletingCategory = ref(null)

// Category form
const newCategoryName = ref('')
const editingCategory = ref(null)

// Fetch user info
const fetchUserInfo = async () => {
    try {
        const res = await api.get('auth/user/')
        userInfo.value = res.data
    } catch (err) {
        console.error('Failed to fetch user info:', err)
    }
}

// Fetch categories
const fetchCategories = async () => {
    try {
        const res = await api.get('categories/')
        categories.value = res.data.sort((a, b) => (a.order || 0) - (b.order || 0))
    } catch (err) {
        console.error('Failed to fetch categories:', err)
    }
}

// Add new category
const addCategory = async () => {
    if (!newCategoryName.value.trim()) return

    isSavingCategory.value = true
    try {
        await api.post('categories/', {
            name: newCategoryName.value,
            order: categories.value.length
        })

        newCategoryName.value = ''
        await fetchCategories()
    } catch (err) {
        console.error('Failed to add category:', err)
        alert('Failed to add category')
    } finally {
        isSavingCategory.value = false
    }
}

// Delete category
const deleteCategory = async (categoryId) => {
    if (!confirm('Are you sure you want to delete this category? Habits in this category will become uncategorized.')) {
        return
    }

    isDeletingCategory.value = categoryId
    try {
        await api.delete(`categories/${categoryId}/`)
        await fetchCategories()
    } catch (err) {
        console.error('Failed to delete category:', err)
        alert('Failed to delete category')
    } finally {
        isDeletingCategory.value = null
    }
}

// Update category name
const updateCategory = async (category) => {
    if (!category.name.trim()) return

    try {
        await api.patch(`categories/${category.id}/`, {
            name: category.name
        })
        editingCategory.value = null
    } catch (err) {
        console.error('Failed to update category:', err)
        alert('Failed to update category')
    }
}

const goBack = () => {
    router.push('/dashboard')
}

const handleLogout = () => {
    authService.logout()
    router.push('/login')
}

onMounted(() => {
    fetchUserInfo()
    fetchCategories()
})
</script>

<template>
    <div
        class="min-h-screen bg-[#f8fafc] dark:bg-slate-900 p-6 md:p-12 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-300">
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
                    <p class="text-slate-400 dark:text-slate-500 font-medium">Manage your account and categories</p>
                </div>
                <div class="flex gap-4">
                    <!-- Dark Mode Toggle -->
                    <button @click="toggleDarkMode"
                        class="bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-yellow-400 px-6 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-slate-300 dark:hover:bg-slate-600 transition-all shadow-md active:scale-95">
                        <Moon v-if="!isDark" :size="20" stroke-width="2.5" />
                        <Sun v-else :size="20" stroke-width="2.5" />
                    </button>

                    <button @click="handleLogout"
                        class="bg-red-600 text-white px-8 py-4 rounded-2xl font-bold hover:bg-red-700 transition-all shadow-md active:scale-95">
                        Logout
                    </button>
                </div>
            </header>

            <div class="space-y-6">

                <!-- Account Information -->
                <div
                    class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
                    <div class="flex items-center gap-3 mb-6">
                        <div class="p-3 bg-indigo-100 dark:bg-indigo-900/30 rounded-2xl">
                            <User :size="24" class="text-indigo-600 dark:text-indigo-400" stroke-width="2.5" />
                        </div>
                        <h2 class="text-2xl font-black text-slate-900 dark:text-white">Account Information</h2>
                    </div>

                    <div class="space-y-4">
                        <div class="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
                            <User :size="20" class="text-slate-400" />
                            <div>
                                <p class="text-xs font-black uppercase tracking-widest text-slate-400">Username</p>
                                <p class="font-bold text-slate-900 dark:text-white">{{ userInfo.username || 'Loading...'
                                    }}</p>
                            </div>
                        </div>

                        <div class="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
                            <Mail :size="20" class="text-slate-400" />
                            <div>
                                <p class="text-xs font-black uppercase tracking-widest text-slate-400">Email</p>
                                <p class="font-bold text-slate-900 dark:text-white">{{ userInfo.email || 'Loading...' }}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Category Management -->
                <div
                    class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
                    <div class="flex items-center gap-3 mb-6">
                        <div class="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-2xl">
                            <Database :size="24" class="text-purple-600 dark:text-purple-400" stroke-width="2.5" />
                        </div>
                        <h2 class="text-2xl font-black text-slate-900 dark:text-white">Manage Categories</h2>
                    </div>

                    <!-- Add New Category -->
                    <div class="mb-6">
                        <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-2 block">
                            Add New Category
                        </label>
                        <div class="flex gap-3">
                            <input v-model="newCategoryName" @keyup.enter="addCategory" type="text"
                                placeholder="Enter category name"
                                class="flex-1 bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-2xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-indigo-500 transition outline-none font-bold text-slate-900 dark:text-white" />
                            <button @click="addCategory" :disabled="isSavingCategory || !newCategoryName.trim()"
                                class="px-8 py-4 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-md active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
                                <Plus :size="20" stroke-width="2.5" />
                                Add
                            </button>
                        </div>
                    </div>

                    <!-- Existing Categories -->
                    <div class="space-y-3">
                        <p class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-3">
                            Existing Categories ({{ categories.length }})
                        </p>

                        <div v-if="categories.length === 0" class="text-center py-8 text-slate-400 dark:text-slate-500">
                            No categories yet. Add your first category above.
                        </div>

                        <div v-for="category in categories" :key="category.id"
                            class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl hover:shadow-md transition-all">
                            <div class="flex-1" v-if="editingCategory !== category.id">
                                <p class="font-bold text-slate-900 dark:text-white">{{ category.name }}</p>
                            </div>

                            <input v-else v-model="category.name" @keyup.enter="updateCategory(category)"
                                @keyup.esc="editingCategory = null" type="text"
                                class="flex-1 bg-white dark:bg-slate-600 border-2 border-indigo-500 rounded-xl px-4 py-2 font-bold outline-none text-slate-900 dark:text-white"
                                autofocus />

                            <div class="flex gap-2 ml-4">
                                <button v-if="editingCategory !== category.id" @click="editingCategory = category.id"
                                    class="px-4 py-2 bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-300 dark:hover:bg-slate-500 transition-all text-sm">
                                    Edit
                                </button>

                                <button v-else @click="updateCategory(category)"
                                    class="px-4 py-2 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 transition-all text-sm flex items-center gap-1">
                                    <Save :size="16" />
                                    Save
                                </button>

                                <button v-if="editingCategory === category.id" @click="editingCategory = null"
                                    class="px-4 py-2 bg-slate-300 dark:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-400 dark:hover:bg-slate-500 transition-all text-sm">
                                    Cancel
                                </button>

                                <button @click="deleteCategory(category.id)"
                                    :disabled="isDeletingCategory === category.id"
                                    class="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-xl font-bold hover:bg-red-200 dark:hover:bg-red-900/50 transition-all text-sm flex items-center gap-1 disabled:opacity-50">
                                    <Trash2 :size="16" />
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Danger Zone -->
                <div
                    class="bg-red-50 dark:bg-red-900/20 rounded-[3rem] p-8 shadow-lg border-2 border-red-200 dark:border-red-900/50">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-3 bg-red-100 dark:bg-red-900/50 rounded-2xl">
                            <Trash2 :size="24" class="text-red-600 dark:text-red-400" stroke-width="2.5" />
                        </div>
                        <h2 class="text-2xl font-black text-red-900 dark:text-red-400">Danger Zone</h2>
                    </div>
                    <p class="text-red-700 dark:text-red-300 mb-4 font-medium">
                        Deleting categories will not delete your habits, but will uncategorize them. Category deletion
                        cannot be undone.
                    </p>
                </div>

            </div>

            <!-- Footer -->
            <footer class="mt-16 pt-8 text-center border-t border-slate-200 dark:border-slate-700">
                <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">
                    © {{ new Date().getFullYear() }} Continuum. All rights reserved.
                </p>
            </footer>

        </div>
    </div>
</template>

<style scoped>
/* Custom styles if needed */
</style>