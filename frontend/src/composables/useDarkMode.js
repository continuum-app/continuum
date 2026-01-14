// src/composables/useDarkMode.js
import { ref, watch, onMounted } from 'vue'

export function useDarkMode() {
    const isDark = ref(false)

    // Initialize dark mode from localStorage or system preference
    const initDarkMode = () => {
        const stored = localStorage.getItem('darkMode')

        if (stored !== null) {
            isDark.value = stored === 'true'
        } else {
            // Check system preference
            isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
        }

        applyDarkMode()
    }

    // Apply dark mode to document
    const applyDarkMode = () => {
        if (isDark.value) {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
    }

    // Toggle dark mode
    const toggleDarkMode = () => {
        isDark.value = !isDark.value
    }

    // Watch for changes and persist to localStorage
    watch(isDark, (newValue) => {
        localStorage.setItem('darkMode', newValue.toString())
        applyDarkMode()
    })

    onMounted(() => {
        initDarkMode()
    })

    return {
        isDark,
        toggleDarkMode
    }
}