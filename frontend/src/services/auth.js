import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/auth/'

class AuthService {
    async login(email, password) {
        const response = await axios.post(API_URL + 'login/', {
            email,
            password
        })

        if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token)
            localStorage.setItem('refresh_token', response.data.refresh_token)
            localStorage.setItem('user', JSON.stringify(response.data.user))
        }

        return response.data
    }

    logout() {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
    }

    async register(email, password1, password2) {
        return axios.post(API_URL + 'registration/', {
            email,
            password1,
            password2
        })
    }

    getCurrentUser() {
        const user = localStorage.getItem('user')
        return user ? JSON.parse(user) : null
    }

    getAccessToken() {
        return localStorage.getItem('access_token')
    }

    getRefreshToken() {
        return localStorage.getItem('refresh_token')
    }

    async refreshToken() {
        const refresh = this.getRefreshToken()

        if (!refresh) {
            throw new Error('No refresh token available')
        }

        const response = await axios.post(API_URL + 'token/refresh/', {
            refresh
        })

        if (response.data.access) {
            localStorage.setItem('access_token', response.data.access)
        }

        return response.data.access
    }
}

export default new AuthService()