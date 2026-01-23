// composables/useCookies.js
export function useCookies() {
    const setCookie = (name, value, days = 365) => {
        const date = new Date()
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000))
        const expires = `expires=${date.toUTCString()}`
        document.cookie = `${name}=${value};${expires};path=/`
    }

    const getCookie = (name) => {
        const nameEQ = `${name}=`
        const cookies = document.cookie.split(';')
        for (let cookie of cookies) {
            cookie = cookie.trim()
            if (cookie.indexOf(nameEQ) === 0) {
                return cookie.substring(nameEQ.length)
            }
        }
        return null
    }

    return { setCookie, getCookie }
}