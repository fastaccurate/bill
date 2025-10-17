import axios from 'axios'
import { store } from '../redux/store'
import { refreshToken, clearAuth } from '../redux/slices/authSlice'

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshTokenValue = localStorage.getItem('refreshToken')
      if (refreshTokenValue) {
        try {
          // Dispatch refresh token action
          const result = await store.dispatch(refreshToken())

          if (result.type === 'auth/refresh/fulfilled') {
            // Retry original request with new token
            const newToken = localStorage.getItem('accessToken')
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return api(originalRequest)
          } else {
            // Refresh failed, clear auth
            store.dispatch(clearAuth())
            window.location.href = '/login'
          }
        } catch (refreshError) {
          // Refresh failed, clear auth
          store.dispatch(clearAuth())
          window.location.href = '/login'
        }
      } else {
        // No refresh token, clear auth
        store.dispatch(clearAuth())
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

// Group Service
export const groupService = {
  getUserGroups: () => api.get('/groups'),
  getGroupDetails: (groupId) => api.get(`/groups/${groupId}`),
  createGroup: (groupData) => api.post('/groups', groupData),
  updateGroup: (groupId, groupData) => api.put(`/groups/${groupId}`, groupData),
  addMember: (groupId, memberData) => api.post(`/groups/${groupId}/members`, memberData),
  removeMember: (groupId, userId) => api.delete(`/groups/${groupId}/members/${userId}`),
  updateMemberRole: (groupId, userId, roleData) => api.put(`/groups/${groupId}/members/${userId}/role`, roleData),
  getGroupBalance: (groupId) => api.get(`/groups/${groupId}/balance`),
}

// Expense Service
export const expenseService = {
  getGroupExpenses: (groupId, params = {}) => api.get(`/expenses/group/${groupId}`, { params }),
  getExpenseDetails: (expenseId) => api.get(`/expenses/${expenseId}`),
  createExpense: (expenseData) => api.post('/expenses', expenseData),
  updateExpense: (expenseId, expenseData) => api.put(`/expenses/${expenseId}`, expenseData),
  deleteExpense: (expenseId) => api.delete(`/expenses/${expenseId}`),
  settleExpenseParticipation: (expenseId, settlementData) => api.post(`/expenses/${expenseId}/settle`, settlementData),
  getGroupExpenseStatistics: (groupId, params = {}) => api.get(`/expenses/statistics/group/${groupId}`, { params }),
}

// Reminder Service
export const reminderService = {
  sendPaymentReminder: (reminderData) => api.post('/reminders/send-payment-reminder', reminderData),
  sendBulkReminders: (bulkReminderData) => api.post('/reminders/send-bulk-reminders', bulkReminderData),
  scheduleReminder: (scheduleData) => api.post('/reminders/schedule-reminder', scheduleData),
  getReminderCandidates: (groupId) => api.get(`/reminders/group/${groupId}/reminder-candidates`),
  sendTestSMS: (testData) => api.post('/reminders/test-sms', testData),
}

export default api