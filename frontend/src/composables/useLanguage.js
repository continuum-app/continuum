import { ref, computed } from 'vue'
import { translations } from '@/composables/translations'

const supportedLanguages = ['en', 'fr']

const getInitialLanguage = () => {
    const stored = localStorage.getItem('language')
    if (stored && supportedLanguages.includes(stored)) {
        return stored
    }

    // Detect browser/OS language
    const browserLang = navigator.language || navigator.userLanguage
    const langCode = browserLang?.split('-')[0] // e.g., 'en-US' -> 'en'

    if (langCode && supportedLanguages.includes(langCode)) {
        return langCode
    }

    return 'en'
}

const currentLanguage = ref(getInitialLanguage())

export const useLanguage = () => {
    const setLanguage = (lang) => {
        currentLanguage.value = lang
        localStorage.setItem('language', lang)
    }

    const languages = [
        { code: 'en', name: 'English', flag: '🇺🇸' },
        { code: 'fr', name: 'Français', flag: '🇫🇷' },
    ]

    const currentLanguageInfo = computed(() => {
        return languages.find(lang => lang.code === currentLanguage.value) || languages[0]
    })

    // Get translation function
    const t = (key) => {
        return translations[currentLanguage.value]?.[key] || translations['en'][key] || key
    }

    return {
        currentLanguage,
        setLanguage,
        languages,
        currentLanguageInfo,
        t
    }
}