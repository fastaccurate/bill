import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { authService } from '../../services/authService'
import toast from 'react-hot-toast'

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const response = await authService.login(email, password)
      localStorage.setItem('accessToken', response.data.access_token)
      localStorage.setItem('refreshToken', response.data.refresh_token)
      toast.success('Login successful!')
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || 'Login failed'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await authService.register(userData)
      localStorage.setItem('accessToken', response.data.access_token)
      localStorage.setItem('refreshToken', response.data.refresh_token)
      toast.success('Registration successful!')
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || 'Registration failed'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const refreshToken = createAsyncThunk(
  'auth/refresh',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.refreshToken()
      localStorage.setItem('accessToken', response.data.access_token)
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || 'Token refresh failed'
      return rejectWithValue(message)
    }
  }
)

export const fetchUserProfile = createAsyncThunk(
  'auth/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.getProfile()
      return response.data.user
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch profile'
      return rejectWithValue(message)
    }
  }
)

export const updateUserProfile = createAsyncThunk(
  'auth/updateProfile',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await authService.updateProfile(userData)
      toast.success('Profile updated successfully!')
      return response.data.user
    } catch (error) {
      const message = error.response?.data?.error || 'Profile update failed'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const changePassword = createAsyncThunk(
  'auth/changePassword',
  async (passwordData, { rejectWithValue }) => {
    try {
      const response = await authService.changePassword(passwordData)
      toast.success('Password changed successfully!')
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || 'Password change failed'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

// Initial state
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  tokenRefreshing: false,
}

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearAuth: (state) => {
      state.user = null
      state.isAuthenticated = false
      state.error = null
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    },
    clearError: (state) => {
      state.error = null
    },
    setTokenRefreshing: (state, action) => {
      state.tokenRefreshing = action.payload
    },
    initializeAuth: (state) => {
      const token = localStorage.getItem('accessToken')
      if (token) {
        // Will be validated by fetchUserProfile
        state.isAuthenticated = true
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = true
        state.user = action.payload.user
        state.error = null
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = false
        state.user = null
        state.error = action.payload
      })

      // Register
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = true
        state.user = action.payload.user
        state.error = null
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = false
        state.user = null
        state.error = action.payload
      })

      // Refresh token
      .addCase(refreshToken.pending, (state) => {
        state.tokenRefreshing = true
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.tokenRefreshing = false
        state.user = action.payload.user
        state.isAuthenticated = true
      })
      .addCase(refreshToken.rejected, (state) => {
        state.tokenRefreshing = false
        state.isAuthenticated = false
        state.user = null
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
      })

      // Fetch profile
      .addCase(fetchUserProfile.pending, (state) => {
        state.isLoading = true
      })
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.isLoading = false
        state.user = action.payload
        state.isAuthenticated = true
      })
      .addCase(fetchUserProfile.rejected, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = false
        state.user = null
        state.error = action.payload
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
      })

      // Update profile
      .addCase(updateUserProfile.fulfilled, (state, action) => {
        state.user = action.payload
      })

      // Change password
      .addCase(changePassword.pending, (state) => {
        state.isLoading = true
      })
      .addCase(changePassword.fulfilled, (state) => {
        state.isLoading = false
      })
      .addCase(changePassword.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
      })
  },
})

export const { clearAuth, clearError, setTokenRefreshing, initializeAuth } = authSlice.actions
export default authSlice.reducer