import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { expenseService, reminderService } from '../../services/api'
import toast from 'react-hot-toast'

// Async thunks
export const fetchGroupExpenses = createAsyncThunk(
  'expenses/fetchGroupExpenses',
  async ({ groupId, page = 1, per_page = 20, category }, { rejectWithValue }) => {
    try {
      const response = await expenseService.getGroupExpenses(groupId, { page, per_page, category })
      return { 
        groupId, 
        expenses: response.data.expenses, 
        pagination: response.data.pagination 
      }
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch expenses'
      return rejectWithValue(message)
    }
  }
)

export const fetchExpenseDetails = createAsyncThunk(
  'expenses/fetchExpenseDetails',
  async (expenseId, { rejectWithValue }) => {
    try {
      const response = await expenseService.getExpenseDetails(expenseId)
      return response.data.expense
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch expense details'
      return rejectWithValue(message)
    }
  }
)

export const createExpense = createAsyncThunk(
  'expenses/createExpense',
  async (expenseData, { rejectWithValue, dispatch }) => {
    try {
      const response = await expenseService.createExpense(expenseData)
      toast.success('Expense created successfully!')

      // Refresh expenses for the group
      dispatch(fetchGroupExpenses({ groupId: expenseData.group_id }))

      return response.data.expense
    } catch (error) {
      const message = error.response?.data?.error || error.response?.data?.errors?.[0] || 'Failed to create expense'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const updateExpense = createAsyncThunk(
  'expenses/updateExpense',
  async ({ expenseId, expenseData }, { rejectWithValue, dispatch }) => {
    try {
      const response = await expenseService.updateExpense(expenseId, expenseData)
      toast.success('Expense updated successfully!')

      // Refresh expenses for the group
      if (expenseData.group_id) {
        dispatch(fetchGroupExpenses({ groupId: expenseData.group_id }))
      }

      return response.data.expense
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to update expense'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const deleteExpense = createAsyncThunk(
  'expenses/deleteExpense',
  async ({ expenseId, groupId }, { rejectWithValue, dispatch }) => {
    try {
      await expenseService.deleteExpense(expenseId)
      toast.success('Expense deleted successfully!')

      // Refresh expenses for the group
      dispatch(fetchGroupExpenses({ groupId }))

      return expenseId
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to delete expense'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const settleExpenseParticipation = createAsyncThunk(
  'expenses/settleParticipation',
  async ({ expenseId, createSettlement = false, paymentMethod = 'cash' }, { rejectWithValue, dispatch }) => {
    try {
      const response = await expenseService.settleExpenseParticipation(expenseId, {
        create_settlement: createSettlement,
        payment_method: paymentMethod
      })
      toast.success('Expense participation settled!')

      // Refresh expense details
      dispatch(fetchExpenseDetails(expenseId))

      return response.data.expense
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to settle expense participation'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const fetchExpenseStatistics = createAsyncThunk(
  'expenses/fetchStatistics',
  async ({ groupId, start_date, end_date }, { rejectWithValue }) => {
    try {
      const response = await expenseService.getGroupExpenseStatistics(groupId, { start_date, end_date })
      return { groupId, statistics: response.data }
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch expense statistics'
      return rejectWithValue(message)
    }
  }
)

export const sendPaymentReminder = createAsyncThunk(
  'expenses/sendPaymentReminder',
  async ({ userId, groupId, messageType = 'friendly', customMessage }, { rejectWithValue }) => {
    try {
      const response = await reminderService.sendPaymentReminder({
        user_id: userId,
        group_id: groupId,
        message_type: messageType,
        custom_message: customMessage
      })
      toast.success('Payment reminder sent successfully!')
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to send payment reminder'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const sendBulkReminders = createAsyncThunk(
  'expenses/sendBulkReminders',
  async ({ groupId, messageType = 'friendly', minimumAmount = 1.0, customMessage }, { rejectWithValue }) => {
    try {
      const response = await reminderService.sendBulkReminders({
        group_id: groupId,
        message_type: messageType,
        minimum_amount: minimumAmount,
        custom_message: customMessage
      })
      toast.success(`Bulk reminders sent: ${response.data.message}`)
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to send bulk reminders'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const fetchReminderCandidates = createAsyncThunk(
  'expenses/fetchReminderCandidates',
  async (groupId, { rejectWithValue }) => {
    try {
      const response = await reminderService.getReminderCandidates(groupId)
      return { groupId, candidates: response.data.candidates }
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch reminder candidates'
      return rejectWithValue(message)
    }
  }
)

// Initial state
const initialState = {
  expenses: {},           // { groupId: [expenses] }
  currentExpense: null,
  statistics: {},         // { groupId: statistics }
  reminderCandidates: {}, // { groupId: candidates }
  pagination: {},         // { groupId: paginationInfo }
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  isSendingReminder: false,
  error: null,
}

// Slice
const expenseSlice = createSlice({
  name: 'expenses',
  initialState,
  reducers: {
    clearCurrentExpense: (state) => {
      state.currentExpense = null
    },
    clearError: (state) => {
      state.error = null
    },
    clearGroupExpenses: (state, action) => {
      const groupId = action.payload
      delete state.expenses[groupId]
      delete state.pagination[groupId]
    },
    updateExpenseInList: (state, action) => {
      const updatedExpense = action.payload

      // Update in all groups where this expense might be present
      Object.keys(state.expenses).forEach(groupId => {
        const expenseIndex = state.expenses[groupId].findIndex(exp => exp.id === updatedExpense.id)
        if (expenseIndex !== -1) {
          state.expenses[groupId][expenseIndex] = updatedExpense
        }
      })

      // Update current expense if it matches
      if (state.currentExpense && state.currentExpense.id === updatedExpense.id) {
        state.currentExpense = updatedExpense
      }
    },
    addExpenseToGroup: (state, action) => {
      const { groupId, expense } = action.payload
      if (state.expenses[groupId]) {
        state.expenses[groupId].unshift(expense) // Add to beginning
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch group expenses
      .addCase(fetchGroupExpenses.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchGroupExpenses.fulfilled, (state, action) => {
        state.isLoading = false
        const { groupId, expenses, pagination } = action.payload
        state.expenses[groupId] = expenses
        state.pagination[groupId] = pagination
        state.error = null
      })
      .addCase(fetchGroupExpenses.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
      })

      // Fetch expense details
      .addCase(fetchExpenseDetails.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchExpenseDetails.fulfilled, (state, action) => {
        state.isLoading = false
        state.currentExpense = action.payload
        state.error = null
      })
      .addCase(fetchExpenseDetails.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
      })

      // Create expense
      .addCase(createExpense.pending, (state) => {
        state.isCreating = true
        state.error = null
      })
      .addCase(createExpense.fulfilled, (state, action) => {
        state.isCreating = false
        const expense = action.payload
        const groupId = expense.group_id

        if (state.expenses[groupId]) {
          state.expenses[groupId].unshift(expense)
        }
        state.error = null
      })
      .addCase(createExpense.rejected, (state, action) => {
        state.isCreating = false
        state.error = action.payload
      })

      // Update expense
      .addCase(updateExpense.pending, (state) => {
        state.isUpdating = true
        state.error = null
      })
      .addCase(updateExpense.fulfilled, (state, action) => {
        state.isUpdating = false
        const updatedExpense = action.payload

        // Update in expenses list
        Object.keys(state.expenses).forEach(groupId => {
          const expenseIndex = state.expenses[groupId].findIndex(exp => exp.id === updatedExpense.id)
          if (expenseIndex !== -1) {
            state.expenses[groupId][expenseIndex] = updatedExpense
          }
        })

        // Update current expense
        if (state.currentExpense && state.currentExpense.id === updatedExpense.id) {
          state.currentExpense = updatedExpense
        }

        state.error = null
      })
      .addCase(updateExpense.rejected, (state, action) => {
        state.isUpdating = false
        state.error = action.payload
      })

      // Delete expense
      .addCase(deleteExpense.pending, (state) => {
        state.isDeleting = true
        state.error = null
      })
      .addCase(deleteExpense.fulfilled, (state, action) => {
        state.isDeleting = false
        const deletedExpenseId = action.payload

        // Remove from all groups
        Object.keys(state.expenses).forEach(groupId => {
          state.expenses[groupId] = state.expenses[groupId].filter(exp => exp.id !== deletedExpenseId)
        })

        // Clear current expense if it was deleted
        if (state.currentExpense && state.currentExpense.id === deletedExpenseId) {
          state.currentExpense = null
        }

        state.error = null
      })
      .addCase(deleteExpense.rejected, (state, action) => {
        state.isDeleting = false
        state.error = action.payload
      })

      // Settle expense participation
      .addCase(settleExpenseParticipation.fulfilled, (state, action) => {
        const updatedExpense = action.payload

        // Update in expenses list
        Object.keys(state.expenses).forEach(groupId => {
          const expenseIndex = state.expenses[groupId].findIndex(exp => exp.id === updatedExpense.id)
          if (expenseIndex !== -1) {
            state.expenses[groupId][expenseIndex] = updatedExpense
          }
        })

        // Update current expense
        if (state.currentExpense && state.currentExpense.id === updatedExpense.id) {
          state.currentExpense = updatedExpense
        }
      })

      // Fetch expense statistics
      .addCase(fetchExpenseStatistics.fulfilled, (state, action) => {
        const { groupId, statistics } = action.payload
        state.statistics[groupId] = statistics
      })

      // Send payment reminder
      .addCase(sendPaymentReminder.pending, (state) => {
        state.isSendingReminder = true
      })
      .addCase(sendPaymentReminder.fulfilled, (state) => {
        state.isSendingReminder = false
      })
      .addCase(sendPaymentReminder.rejected, (state, action) => {
        state.isSendingReminder = false
        state.error = action.payload
      })

      // Send bulk reminders
      .addCase(sendBulkReminders.pending, (state) => {
        state.isSendingReminder = true
      })
      .addCase(sendBulkReminders.fulfilled, (state) => {
        state.isSendingReminder = false
      })
      .addCase(sendBulkReminders.rejected, (state, action) => {
        state.isSendingReminder = false
        state.error = action.payload
      })

      // Fetch reminder candidates
      .addCase(fetchReminderCandidates.fulfilled, (state, action) => {
        const { groupId, candidates } = action.payload
        state.reminderCandidates[groupId] = candidates
      })
  },
})

export const { 
  clearCurrentExpense, 
  clearError, 
  clearGroupExpenses, 
  updateExpenseInList,
  addExpenseToGroup
} = expenseSlice.actions

export default expenseSlice.reducer