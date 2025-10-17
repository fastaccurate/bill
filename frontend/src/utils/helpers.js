import { format, parseISO, formatDistanceToNow } from 'date-fns'

// Format currency
export const formatCurrency = (amount, currency = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount)
}

// Format date
export const formatDate = (date, formatString = 'MMM dd, yyyy') => {
  if (!date) return ''

  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date
    return format(parsedDate, formatString)
  } catch (error) {
    console.error('Error formatting date:', error)
    return ''
  }
}

// Format relative time (e.g., "2 hours ago")
export const formatRelativeTime = (date) => {
  if (!date) return ''

  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date
    return formatDistanceToNow(parsedDate, { addSuffix: true })
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return ''
  }
}

// Validate email
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Validate phone number
export const validatePhone = (phone) => {
  const phoneRegex = /^[+]?[1-9]\d{1,14}$/
  return phoneRegex.test(phone.replace(/[\s-()]/g, ''))
}

// Generate random color
export const generateColor = (seed) => {
  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#6366f1', '#f97316'
  ]
  return colors[seed % colors.length]
}

// Calculate balance color
export const getBalanceColor = (balance) => {
  if (balance > 0) return 'text-green-600'
  if (balance < 0) return 'text-red-600'
  return 'text-gray-600'
}

// Format phone number
export const formatPhoneNumber = (phone) => {
  const cleaned = phone.replace(/\D/g, '')

  if (cleaned.length === 10) {
    return `(${cleaned.substring(0, 3)}) ${cleaned.substring(3, 6)}-${cleaned.substring(6)}`
  }

  return phone
}

// Calculate split amounts
export const calculateSplit = (amount, participants, method = 'equal', data = {}) => {
  const totalAmount = parseFloat(amount)

  switch (method) {
    case 'equal':
      const amountPerPerson = totalAmount / participants.length
      return participants.reduce((acc, participant) => {
        acc[participant.id] = amountPerPerson
        return acc
      }, {})

    case 'exact':
      return data.amounts || {}

    case 'percentage':
      return participants.reduce((acc, participant) => {
        const percentage = data.percentages[participant.id] || 0
        acc[participant.id] = (totalAmount * percentage) / 100
        return acc
      }, {})

    default:
      return {}
  }
}

// Truncate text
export const truncateText = (text, maxLength = 50) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// Debounce function
export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Copy to clipboard
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
    return false
  }
}

// Generate initials from name
export const getInitials = (name) => {
  if (!name) return 'U'
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('')
}

// Calculate percentage
export const calculatePercentage = (value, total) => {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}