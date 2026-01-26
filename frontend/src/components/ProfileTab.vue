<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useLanguage } from '@/composables/useLanguage'
import { useHabits } from '@/composables/useHabits'
import { useCategories } from '@/composables/useCategories'
import * as LucideIcons from 'lucide-vue-next'
import { User, Mail, Lock, Save, RefreshCw, Plus, Trash2, Pencil, X, Check, ArchiveRestore, Archive, CheckCircle2 } from 'lucide-vue-next'
import IconPicker from './IconPicker.vue'

const { t } = useLanguage()
const { habits, archivedHabits, fetchHabits, fetchArchivedHabits, archiveHabit, unarchiveHabit, deleteHabit, updateHabit } = useHabits()
const { categories, isSavingCategory, isDeletingCategory, fetchCategories, addCategory, deleteCategory, updateCategory } = useCategories()

// User info state
const userInfo = ref({
    username: '',
    email: '',
    is_staff: false,
    is_superuser: false
})

// Profile form state
const profileEmail = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isSavingProfile = ref(false)
const profileSaved = ref(false)
const passwordError = ref('')
const passwordSuccess = ref(false)

// Category management
const newCategoryName = ref('')
const editingCategory = ref(null)
const editingCategoryName = ref('')

// Habit editing
const editingHabit = ref(null)
const editingHabitData = ref({
    name: '',
    icon: '',
    color: '',
    habit_type: '',
    max_value: 5,
    unit: '',
    category: null
})
const isSavingHabit = ref(false)

// Fetch user info
const fetchUserInfo = async () => {
    try {
        const response = await api.get('auth/user/')
        userInfo.value = response.data
        profileEmail.value = response.data.email
    } catch (err) {
        console.error('Failed to fetch user info:', err)
    }
}

// Update profile email
const updateProfile = async () => {
    isSavingProfile.value = true
    try {
        await api.patch('auth/user/', { email: profileEmail.value })
        profileSaved.value = true
        setTimeout(() => { profileSaved.value = false }, 3000)
    } catch (err) {
        console.error('Failed to update profile:', err)
    } finally {
        isSavingProfile.value = false
    }
}

// Change password
const changePassword = async () => {
    passwordError.value = ''
    passwordSuccess.value = false

    if (newPassword.value !== confirmPassword.value) {
        passwordError.value = t('passwordMismatch')
        return
    }

    if (newPassword.value.length < 8) {
        passwordError.value = t('passwordTooShort')
        return
    }

    isSavingProfile.value = true
    try {
        await api.post('auth/password/change/', {
            old_password: currentPassword.value,
            new_password1: newPassword.value,
            new_password2: confirmPassword.value
        })
        passwordSuccess.value = true
        currentPassword.value = ''
        newPassword.value = ''
        confirmPassword.value = ''
        setTimeout(() => { passwordSuccess.value = false }, 3000)
    } catch (err) {
        passwordError.value = err.response?.data?.old_password?.[0] || t('passwordChangeFailed')
    } finally {
        isSavingProfile.value = false
    }
}

// Category management
const handleAddCategory = async () => {
    if (!newCategoryName.value.trim()) return
    await addCategory(newCategoryName.value.trim())
    newCategoryName.value = ''
}

const startEditCategory = (category) => {
    editingCategory.value = category.id
    editingCategoryName.value = category.name
}

const saveEditCategory = async (categoryId) => {
    if (!editingCategoryName.value.trim()) return
    await updateCategory(categoryId, editingCategoryName.value.trim())
    editingCategory.value = null
    await fetchCategories()
}

const cancelEditCategory = () => {
    editingCategory.value = null
    editingCategoryName.value = ''
}

const handleDeleteCategory = async (categoryId) => {
    if (confirm(t('confirmDeleteCategory'))) {
        await deleteCategory(categoryId)
    }
}

// Habit editing (for archived habits)
const startEditHabit = (habit) => {
    editingHabit.value = habit.id
    editingHabitData.value = {
        name: habit.name,
        icon: habit.icon,
        color: habit.color,
        habit_type: habit.habit_type,
        max_value: habit.max_value || 5,
        unit: habit.unit || '',
        category: habit.category?.id || null
    }
}

const saveEditHabit = async () => {
    isSavingHabit.value = true
    try {
        await updateHabit(editingHabit.value, {
            name: editingHabitData.value.name,
            icon: editingHabitData.value.icon,
            color: editingHabitData.value.color,
            habit_type: editingHabitData.value.habit_type,
            max_value: editingHabitData.value.max_value,
            unit: editingHabitData.value.unit,
            category: editingHabitData.value.category
        })
        editingHabit.value = null
        await fetchHabits(new Date().toISOString().split('T')[0])
        await fetchArchivedHabits()
    } catch (err) {
        console.error('Failed to update habit:', err)
    } finally {
        isSavingHabit.value = false
    }
}

const cancelEditHabit = () => {
    editingHabit.value = null
}

const handleArchiveHabit = async (habitId) => {
    await archiveHabit(habitId)
}

const handleDeleteActiveHabit = async (habitId) => {
    if (confirm(t('confirmDeletePermanent'))) {
        await deleteHabit(habitId)
        await fetchHabits(new Date().toISOString().split('T')[0])
    }
}

const handleUnarchive = async (habitId) => {
    await unarchiveHabit(habitId)
    await fetchHabits(new Date().toISOString().split('T')[0])
}

const handleDelete = async (habitId) => {
    if (confirm(t('confirmDeletePermanent'))) {
        await deleteHabit(habitId)
        await fetchArchivedHabits()
    }
}

// Get icon component
const getIcon = (iconName) => {
    if (!iconName) return LucideIcons.Calendar
    const pascalCase = iconName
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join('')
    return LucideIcons[pascalCase] || LucideIcons.Calendar
}

onMounted(() => {
    fetchUserInfo()
    fetchCategories()
    fetchHabits(new Date().toISOString().split('T')[0])
    fetchArchivedHabits()
})
</script>

<template>
    <div class="space-y-8">
        <!-- Account Section -->
        <div
            class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-3 mb-6">
                <div class="p-3 rounded-2xl bg-primary-100 dark:bg-primary-900">
                    <User :size="24" class="text-primary-600 dark:text-primary-400" stroke-width="2.5" />
                </div>
                <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('accountInformation') }}</h2>
            </div>

            <div class="space-y-6">
                <!-- Username (read-only) -->
                <div class="space-y-2">
                    <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('username')
                    }}</label>
                    <div
                        class="bg-slate-100 dark:bg-slate-700 rounded-2xl px-6 py-4 font-bold text-slate-600 dark:text-slate-300">
                        {{ userInfo.username }}
                    </div>
                </div>

                <!-- Email -->
                <div class="space-y-2">
                    <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2">{{ t('email')
                    }}</label>
                    <div class="flex gap-3">
                        <input v-model="profileEmail" type="email"
                            class="flex-1 bg-slate-50 dark:bg-slate-700 border-2 border-slate-100 dark:border-slate-600 rounded-2xl px-6 py-4 font-bold outline-none focus:border-primary-500 transition text-slate-900 dark:text-white" />
                        <button @click="updateProfile" :disabled="isSavingProfile"
                            class="px-6 py-4 bg-primary-600 text-white rounded-2xl font-bold hover:bg-primary-700 transition-all disabled:opacity-50 flex items-center gap-2">
                            <RefreshCw v-if="isSavingProfile" :size="20" class="animate-spin" />
                            <Save v-else :size="20" />
                            {{ profileSaved ? (t('saved')) : (t('save')) }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Password Section -->
        <div
            class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-3 mb-6">
                <div class="p-3 rounded-2xl bg-orange-100 dark:bg-orange-900">
                    <Lock :size="24" class="text-orange-600 dark:text-orange-400" stroke-width="2.5" />
                </div>
                <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('changePassword') }}</h2>
            </div>

            <div class="space-y-4">
                <div class="space-y-2">
                    <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2">{{
                        t('currentPassword') || 'Current Password' }}</label>
                    <input v-model="currentPassword" type="password"
                        class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-100 dark:border-slate-600 rounded-2xl px-6 py-4 font-bold outline-none focus:border-primary-500 transition text-slate-900 dark:text-white" />
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                        <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2">{{
                            t('newPassword') || 'New Password' }}</label>
                        <input v-model="newPassword" type="password"
                            class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-100 dark:border-slate-600 rounded-2xl px-6 py-4 font-bold outline-none focus:border-primary-500 transition text-slate-900 dark:text-white" />
                    </div>
                    <div class="space-y-2">
                        <label class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2">{{
                            t('confirmNewPassword') || 'Confirm Password' }}</label>
                        <input v-model="confirmPassword" type="password"
                            class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-100 dark:border-slate-600 rounded-2xl px-6 py-4 font-bold outline-none focus:border-primary-500 transition text-slate-900 dark:text-white" />
                    </div>
                </div>

                <div v-if="passwordError"
                    class="p-4 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-2xl font-bold">
                    {{ passwordError }}
                </div>

                <div v-if="passwordSuccess"
                    class="p-4 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-2xl font-bold">
                    {{ t('passwordChanged') }}
                </div>

                <button @click="changePassword"
                    :disabled="isSavingProfile || !currentPassword || !newPassword || !confirmPassword"
                    class="w-full py-4 bg-orange-600 text-white rounded-2xl font-bold hover:bg-orange-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                    <RefreshCw v-if="isSavingProfile" :size="20" class="animate-spin" />
                    <Lock v-else :size="20" />
                    {{ t('updatePassword') }}
                </button>
            </div>
        </div>

        <!-- Category Management -->
        <div
            class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-3 mb-6">
                <div class="p-3 rounded-2xl bg-purple-100 dark:bg-purple-900">
                    <component :is="LucideIcons.FolderOpen" :size="24" class="text-purple-600 dark:text-purple-400"
                        stroke-width="2.5" />
                </div>
                <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('yourCategories') }}
                </h2>
            </div>

            <!-- Add Category -->
            <div class="flex gap-3 mb-6">
                <input v-model="newCategoryName" type="text"
                    :placeholder="t('newCategoryName') || 'New category name...'" @keyup.enter="handleAddCategory"
                    class="flex-1 bg-slate-50 dark:bg-slate-700 border-2 border-slate-100 dark:border-slate-600 rounded-2xl px-6 py-4 font-bold outline-none focus:border-primary-500 transition text-slate-900 dark:text-white" />
                <button @click="handleAddCategory" :disabled="isSavingCategory || !newCategoryName.trim()"
                    class="px-6 py-4 bg-purple-600 text-white rounded-2xl font-bold hover:bg-purple-700 transition-all disabled:opacity-50 flex items-center gap-2">
                    <RefreshCw v-if="isSavingCategory" :size="20" class="animate-spin" />
                    <Plus v-else :size="20" />
                    {{ t('add') }}
                </button>
            </div>

            <!-- Category List -->
            <div class="space-y-3">
                <div v-for="category in categories" :key="category.id"
                    class="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
                    <template v-if="editingCategory === category.id">
                        <input v-model="editingCategoryName" type="text"
                            class="flex-1 bg-white dark:bg-slate-600 border-2 border-primary-500 rounded-xl px-4 py-2 font-bold outline-none text-slate-900 dark:text-white"
                            @keyup.enter="saveEditCategory(category.id)" />
                        <button @click="saveEditCategory(category.id)"
                            class="p-2 rounded-xl bg-green-500 text-white hover:bg-green-600 transition-all hover:scale-120">
                            <Check :size="20" />
                        </button>
                        <button @click="cancelEditCategory"
                            class="p-2 rounded-xl bg-slate-300 dark:bg-slate-500 text-slate-700 dark:text-white hover:bg-slate-400 transition-all hover:scale-120">
                            <X :size="20" />
                        </button>
                    </template>
                    <template v-else>
                        <span class="flex-1 font-bold text-slate-900 dark:text-white">{{ category.name }}</span>
                        <button @click="startEditCategory(category)"
                            class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120">
                            <Pencil :size="18" class="text-slate-400 hover:text-primary-500" />
                        </button>
                        <button @click="handleDeleteCategory(category.id)"
                            :disabled="isDeletingCategory === category.id"
                            class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120">
                            <RefreshCw v-if="isDeletingCategory === category.id" :size="18"
                                class="animate-spin text-slate-400" />
                            <Trash2 v-else :size="18" class="text-slate-400 hover:text-red-500" />
                        </button>
                    </template>
                </div>

                <div v-if="categories.length === 0" class="text-center py-8 text-slate-400 font-medium">
                    {{ t('noCategories') }}
                </div>
            </div>
        </div>

        <!-- Manage Habits -->
        <div
            class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-3 mb-6">
                <div class="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-2xl">
                    <CheckCircle2 :size="24" class="text-blue-600 dark:text-blue-400" stroke-width="2.5" />
                </div>
                <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('yourHabits') }}</h2>
            </div>

            <!-- Existing Habits -->
            <div class="space-y-3">
                <p class="text-xs font-black uppercase tracking-widest text-slate-400 ml-2 mb-3">
                    Your Habits ({{ habits.length }})
                </p>

                <div v-if="habits.length === 0" class="text-center py-8 text-slate-400 dark:text-slate-500">
                    No habits yet. Create your first habit using the "+ Add Habit" button at the top.
                </div>

                <div v-for="habit in habits" :key="habit.id"
                    class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl hover:shadow-md transition-all">
                    <div class="flex items-center gap-4 flex-1">
                        <div class="shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
                            :style="{ backgroundColor: habit.color + '20' }">
                            <component :is="getIcon(habit.icon)" :size="20" :style="{ color: habit.color }"
                                stroke-width="2.5" />
                        </div>
                        <div class="flex-1">
                            <p class="font-bold text-slate-900 dark:text-white">{{ habit.name }}</p>
                            <div class="flex gap-2 mt-1">
                                <span
                                    class="text-xs px-2 py-1 rounded-full bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300 font-bold">
                                    {{ habit.habit_type }}
                                </span>
                                <span v-if="habit.category"
                                    class="text-xs px-2 py-1 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 font-bold">
                                    {{ habit.category.name }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="flex gap-2 ml-4">
                        <button @click="startEditHabit(habit)" :title="t('editHabit')"
                            class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120">
                            <Pencil :size="18" class="text-slate-400 hover:text-blue-500" />
                        </button>
                        <button @click="handleArchiveHabit(habit.id)" :title="t('archiveHabit')"
                            class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120">
                            <Archive :size="18" class="text-slate-400 hover:text-yellow-500" />
                        </button>
                        <button @click="handleDeleteActiveHabit(habit.id)" :title="t('deleteHabitPermanently')"
                            class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120">
                            <Trash2 :size="18" class="text-slate-400 hover:text-red-500" />
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Archived Habits -->
        <div
            class="bg-white dark:bg-slate-800 rounded-[3rem] p-8 shadow-lg border border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-3 mb-6">
                <div class="p-3 rounded-2xl bg-amber-100 dark:bg-amber-900">
                    <Archive :size="24" class="text-amber-600 dark:text-amber-400" stroke-width="2.5" />
                </div>
                <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ t('archivedHabits') }}
                </h2>
            </div>

            <div class="space-y-4">
                <div v-for="habit in archivedHabits" :key="habit.id"
                    class="flex items-center gap-2 p-4 bg-slate-50 dark:bg-slate-700 rounded-2xl">
                    <!-- Icon -->
                    <div class="p-3 rounded-xl" :style="{ backgroundColor: habit.color + '20' }">
                        <component :is="getIcon(habit.icon)" :size="24" :style="{ color: habit.color }"
                            stroke-width="2.5" />
                    </div>

                    <!-- Info -->
                    <div class="flex-1">
                        <h4 class="font-bold text-slate-900 dark:text-white">{{ habit.name }}</h4>
                        <p class="text-sm text-slate-400">{{ habit.habit_type }}</p>
                    </div>

                    <!-- Actions -->
                    <button @click="startEditHabit(habit)"
                        class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120"
                        :title="t('edit') || 'Edit'">
                        <Pencil :size="18" class="text-slate-400 hover:text-blue-500" />
                    </button>
                    <button @click="handleUnarchive(habit.id)"
                        class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120"
                        :title="t('unarchive') || 'Restore'">
                        <ArchiveRestore :size="18" class="text-slate-400 hover:text-green-500" />
                    </button>
                    <button @click="handleDelete(habit.id)"
                        class="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hover:scale-120"
                        :title="t('deletePermanently') || 'Delete permanently'">
                        <Trash2 :size="18" class="text-slate-400 hover:text-red-500" />
                    </button>
                </div>

                <div v-if="archivedHabits.length === 0" class="text-center py-8 text-slate-400 font-medium">
                    {{ t('noArchivedHabits') }}
                </div>
            </div>
        </div>

        <!-- Edit Habit Modal -->
        <Teleport to="body">
            <Transition name="fade">
                <div v-if="editingHabit" class="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-md" @click="cancelEditHabit"></div>
                    <div
                        class="relative bg-white dark:bg-slate-800 w-full max-w-lg rounded-[3rem] p-12 shadow-2xl overflow-visible">
                        <div class="absolute top-0 left-0 right-0 h-2 bg-blue-500 rounded-t-[3rem]"></div>

                        <div class="flex justify-between items-center mb-10">
                            <h2 class="text-3xl font-black text-slate-900 dark:text-white">{{ t('editHabit') }}
                            </h2>
                            <button @click="cancelEditHabit"
                                class="text-slate-300 hover:text-slate-900 dark:hover:text-white transition">
                                <X :size="32" />
                            </button>
                        </div>

                        <form @submit.prevent="saveEditHabit" class="space-y-8">
                            <div class="space-y-2">
                                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{
                                    t('habitName') || 'Habit Name' }}</label>
                                <input v-model="editingHabitData.name" type="text" required
                                    class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-primary-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white" />
                            </div>

                            <IconPicker v-model="editingHabitData.icon" :label="t('icon') || 'Icon'" />

                            <div class="space-y-2">
                                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{
                                    t('type')
                                    || 'Type' }}</label>
                                <select v-model="editingHabitData.habit_type"
                                    class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-primary-500 transition outline-none font-bold text-slate-900 dark:text-white appearance-none cursor-pointer">
                                    <option value="boolean">{{ t('typeBoolean') || 'Yes/No' }}</option>
                                    <option value="value">{{ t('typeValue') || 'Value' }}</option>
                                    <option value="rating">{{ t('typeRating') || 'Rating' }}</option>
                                </select>
                            </div>

                            <div class="space-y-2">
                                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{
                                    t('category') || 'Category' }}</label>
                                <select v-model="editingHabitData.category"
                                    class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-primary-500 transition outline-none font-bold text-slate-900 dark:text-white appearance-none cursor-pointer">
                                    <option :value="null">{{ t('noCategory') || 'No category' }}</option>
                                    <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}
                                    </option>
                                </select>
                            </div>

                            <div v-if="editingHabitData.habit_type === 'value'" class="space-y-2">
                                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{
                                    t('unit')
                                    || 'Unit' }}</label>
                                <input v-model="editingHabitData.unit" type="text"
                                    :placeholder="t('unitPlaceholder') || 'e.g., km, hours, pages'"
                                    class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-primary-500 transition outline-none font-bold text-slate-900 dark:text-white" />
                            </div>

                            <div v-if="editingHabitData.habit_type === 'rating'" class="space-y-2">
                                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{
                                    t('maxRating') || 'Max Rating' }}</label>
                                <input v-model.number="editingHabitData.max_value" type="number" min="1" max="10"
                                    class="w-full bg-slate-50 dark:bg-slate-700 border-2 border-slate-50 dark:border-slate-700 rounded-3xl px-6 py-4 focus:bg-white dark:focus:bg-slate-600 focus:border-primary-500 transition outline-none font-bold text-lg text-slate-900 dark:text-white" />
                            </div>

                            <div class="space-y-2">
                                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">{{
                                    t('color') || 'Color' }}</label>
                                <div class="flex items-center gap-4 bg-slate-50 dark:bg-slate-700 p-4 rounded-3xl">
                                    <input v-model="editingHabitData.color" type="color"
                                        class="w-16 h-10 rounded-2xl cursor-pointer border-none" />
                                    <span class="font-mono text-sm text-slate-600 dark:text-slate-400">{{
                                        editingHabitData.color
                                        }}</span>
                                </div>
                            </div>

                            <div class="flex gap-3">
                                <button type="submit" :disabled="isSavingHabit"
                                    class="flex-1 bg-blue-600 text-white py-4 rounded-3xl font-black hover:bg-blue-700 transition-all shadow-xl disabled:opacity-50 flex items-center justify-center gap-2">
                                    <RefreshCw v-if="isSavingHabit" :size="20" class="animate-spin" />
                                    <Save v-else :size="20" stroke-width="2.5" />
                                    {{ isSavingHabit ? (t('saving')) : (t('save')) }}
                                </button>
                                <button type="button" @click="cancelEditHabit"
                                    class="flex-1 bg-slate-300 dark:bg-slate-600 text-slate-700 dark:text-slate-300 py-4 rounded-3xl font-black hover:bg-slate-400 dark:hover:bg-slate-500 transition-all">
                                    {{ t('cancel') }}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </Transition>
        </Teleport>
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
</style>
