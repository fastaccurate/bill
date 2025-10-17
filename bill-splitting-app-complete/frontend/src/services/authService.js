import axios from 'axios'

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Create separate axios instance for auth (no interceptors to avoid circular dependency)
const authApi = axios.create({
  baseURL: `${API_BASE_URL}/auth`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const authService = {
  // Authentication
  login: (email, password) => authApi.post('/login', { email, password }),

  register: (userData) => authApi.post('/register', userData),

  refreshToken: () => {
    const refreshToken = localStorage.getItem('refreshToken')
    return authApi.post('/refresh', {}, {
      headers: {
        Authorization: `Bearer ${refreshToken}`
      }
    })
  },

  logout: () => {
    const token = localStorage.getItem('accessToken')
    return authApi.post('/logout', {}, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
  },

  // Profile Management
  getProfile: () => {
    const token = localStorage.getItem('accessToken')
    return authApi.get('/profile', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
  },

  updateProfile: (userData) => {
    const token = localStorage.getItem('accessToken')
    return authApi.put('/profile', userData, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
  },

  changePassword: (passwordData) => {
    const token = localStorage.getItem('accessToken')
    return authApi.post('/change-password', passwordData, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
  },

  // Utility
  checkAvailability: (checkData) => authApi.post('/check-availability', checkData),
}

export default authService