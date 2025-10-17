// API Endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    PROFILE: '/auth/profile',
    LOGOUT: '/auth/logout',
  },
  GROUPS: {
    LIST: '/groups',
    DETAILS: (id) => `/groups/${id}`,
    CREATE: '/groups',
    UPDATE: (id) => `/groups/${id}`,
    MEMBERS: (id) => `/groups/${id}/members`,
    BALANCE: (id) => `/groups/${id}/balance`,
  },
  EXPENSES: {
    GROUP_EXPENSES: (groupId) => `/expenses/group/${groupId}`,
    DETAILS: (id) => `/expenses/${id}`,
    CREATE: '/expenses',
    UPDATE: (id) => `/expenses/${id}`,
    DELETE: (id) => `/expenses/${id}`,
    SETTLE: (id) => `/expenses/${id}/settle`,
    STATISTICS: (groupId) => `/expenses/statistics/group/${groupId}`,
  },
  REMINDERS: {
    SEND: '/reminders/send-payment-reminder',
    BULK: '/reminders/send-bulk-reminders',
    CANDIDATES: (groupId) => `/reminders/group/${groupId}/reminder-candidates`,
  }
}

// Expense Categories
export const EXPENSE_CATEGORIES = [
  { value: 'food', label: '🍕 Food & Dining', color: '#f59e0b' },
  { value: 'transport', label: '🚗 Transportation', color: '#3b82f6' },
  { value: 'utilities', label: '⚡ Utilities', color: '#10b981' },
  { value: 'entertainment', label: '🎬 Entertainment', color: '#8b5cf6' },
  { value: 'shopping', label: '🛍️ Shopping', color: '#ec4899' },
  { value: 'health', label: '🏥 Health & Medical', color: '#ef4444' },
  { value: 'travel', label: '✈️ Travel', color: '#06b6d4' },
  { value: 'education', label: '📚 Education', color: '#84cc16' },
  { value: 'rent', label: '🏠 Rent & Housing', color: '#6366f1' },
  { value: 'general', label: '📝 General', color: '#6b7280' },
]

// Split Methods
export const SPLIT_METHODS = [
  { 
    value: 'equal', 
    label: 'Equal Split', 
    description: 'Split the amount equally among all participants',
    icon: '⚖️'
  },
  { 
    value: 'exact', 
    label: 'Exact Amounts', 
    description: 'Specify exact amounts for each participant',
    icon: '🎯'
  },
  { 
    value: 'percentage', 
    label: 'By Percentage', 
    description: 'Split by percentage of total amount',
    icon: '📊'
  },
]

// Payment Methods
export const PAYMENT_METHODS = [
  { value: 'cash', label: 'Cash', icon: '💵' },
  { value: 'bank_transfer', label: 'Bank Transfer', icon: '🏦' },
  { value: 'online', label: 'Online Payment', icon: '💳' },
  { value: 'upi', label: 'UPI', icon: '📱' },
  { value: 'other', label: 'Other', icon: '💰' },
]

// Message Types
export const REMINDER_MESSAGE_TYPES = [
  { 
    value: 'friendly', 
    label: 'Friendly Reminder', 
    description: 'A polite reminder for payment',
    color: '#10b981'
  },
  { 
    value: 'urgent', 
    label: 'Urgent Reminder', 
    description: 'A more direct reminder',
    color: '#f59e0b'
  },
  { 
    value: 'final', 
    label: 'Final Notice', 
    description: 'Final notice for overdue payment',
    color: '#ef4444'
  },
]

// App Configuration
export const APP_CONFIG = {
  APP_NAME: 'Bill Splitting App',
  VERSION: '1.0.0',
  CURRENCY_SYMBOL: '$',
  CURRENCY_CODE: 'USD',
  DATE_FORMAT: 'MMM dd, yyyy',
  TIME_FORMAT: 'HH:mm',
  ITEMS_PER_PAGE: 20,
  MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
  SUPPORTED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif'],
}

// Validation Rules
export const VALIDATION_RULES = {
  EMAIL: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  PHONE: /^[+]?[0-9]{10,15}$/,
  PASSWORD_MIN_LENGTH: 8,
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 50,
  AMOUNT_MIN: 0.01,
  AMOUNT_MAX: 999999.99,
}

// Local Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'accessToken',
  REFRESH_TOKEN: 'refreshToken',
  USER_PREFERENCES: 'userPreferences',
  THEME: 'theme',
  LANGUAGE: 'language',
}

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Session expired. Please log in again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
}

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Welcome back!',
  REGISTER: 'Account created successfully!',
  PROFILE_UPDATE: 'Profile updated successfully!',
  PASSWORD_CHANGE: 'Password changed successfully!',
  GROUP_CREATE: 'Group created successfully!',
  EXPENSE_CREATE: 'Expense added successfully!',
  PAYMENT_REMINDER: 'Payment reminder sent!',
}