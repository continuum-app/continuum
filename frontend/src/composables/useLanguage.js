import { ref, computed } from 'vue'
import { translations } from './translations'

const currentLanguage = ref(localStorage.getItem('language') || 'en')

export const useLanguage = () => {
    const setLanguage = (lang) => {
        currentLanguage.value = lang
        localStorage.setItem('language', lang)
    }

    const languages = [
        { code: 'en', name: 'English', flag: '🇺🇸' },
        { code: 'fr', name: 'Français', flag: '🇫🇷' },
        { code: 'es', name: 'Español', flag: '🇪🇸' },
        { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
        { code: 'pt', name: 'Português', flag: '🇵🇹' },
        { code: 'zh', name: '中文', flag: '🇨🇳' },
        { code: 'ja', name: '日本語', flag: '🇯🇵' },
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