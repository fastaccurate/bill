import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { groupService } from '../../services/api'
import toast from 'react-hot-toast'

// Async thunks
export const fetchUserGroups = createAsyncThunk(
  'groups/fetchUserGroups',
  async (_, { rejectWithValue }) => {
    try {
      const response = await groupService.getUserGroups()
      return response.data.groups
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch groups'
      return rejectWithValue(message)
    }
  }
)

export const fetchGroupDetails = createAsyncThunk(
  'groups/fetchGroupDetails',
  async (groupId, { rejectWithValue }) => {
    try {
      const response = await groupService.getGroupDetails(groupId)
      return response.data.group
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch group details'
      return rejectWithValue(message)
    }
  }
)

export const createGroup = createAsyncThunk(
  'groups/createGroup',
  async (groupData, { rejectWithValue, dispatch }) => {
    try {
      const response = await groupService.createGroup(groupData)
      toast.success('Group created successfully!')
      dispatch(fetchUserGroups()) // Refresh groups list
      return response.data.group
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to create group'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const updateGroup = createAsyncThunk(
  'groups/updateGroup',
  async ({ groupId, groupData }, { rejectWithValue, dispatch }) => {
    try {
      const response = await groupService.updateGroup(groupId, groupData)
      toast.success('Group updated successfully!')
      dispatch(fetchGroupDetails(groupId))
      return response.data.group
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to update group'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const addGroupMember = createAsyncThunk(
  'groups/addMember',
  async ({ groupId, email }, { rejectWithValue, dispatch }) => {
    try {
      const response = await groupService.addMember(groupId, { email })
      toast.success('Member added successfully!')
      dispatch(fetchGroupDetails(groupId))
      return response.data.group
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to add member'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const removeMember = createAsyncThunk(
  'groups/removeMember',
  async ({ groupId, userId }, { rejectWithValue, dispatch }) => {
    try {
      const response = await groupService.removeMember(groupId, userId)
      toast.success('Member removed successfully!')
      dispatch(fetchGroupDetails(groupId))
      return response.data.group
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to remove member'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const updateMemberRole = createAsyncThunk(
  'groups/updateMemberRole',
  async ({ groupId, userId, role }, { rejectWithValue, dispatch }) => {
    try {
      const response = await groupService.updateMemberRole(groupId, userId, { role })
      toast.success('Member role updated successfully!')
      dispatch(fetchGroupDetails(groupId))
      return response.data.group
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to update member role'
      toast.error(message)
      return rejectWithValue(message)
    }
  }
)

export const fetchGroupBalance = createAsyncThunk(
  'groups/fetchGroupBalance',
  async (groupId, { rejectWithValue }) => {
    try {
      const response = await groupService.getGroupBalance(groupId)
      return { groupId, balances: response.data.member_balances }
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to fetch group balance'
      return rejectWithValue(message)
    }
  }
)

// Initial state
const initialState = {
  groups: [],
  currentGroup: null,
  groupBalances: {},
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  error: null,
  lastFetchTime: null,
}

// Slice
const groupSlice = createSlice({
  name: 'groups',
  initialState,
  reducers: {
    clearCurrentGroup: (state) => {
      state.currentGroup = null
    },
    clearError: (state) => {
      state.error = null
    },
    updateGroupInList: (state, action) => {
      const updatedGroup = action.payload
      const index = state.groups.findIndex(group => group.id === updatedGroup.id)
      if (index !== -1) {
        state.groups[index] = updatedGroup
      }
    },
    setCurrentGroup: (state, action) => {
      state.currentGroup = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch user groups
      .addCase(fetchUserGroups.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchUserGroups.fulfilled, (state, action) => {
        state.isLoading = false
        state.groups = action.payload
        state.lastFetchTime = Date.now()
        state.error = null
      })
      .addCase(fetchUserGroups.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
      })

      // Fetch group details
      .addCase(fetchGroupDetails.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchGroupDetails.fulfilled, (state, action) => {
        state.isLoading = false
        state.currentGroup = action.payload
        state.error = null
      })
      .addCase(fetchGroupDetails.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
      })

      // Create group
      .addCase(createGroup.pending, (state) => {
        state.isCreating = true
        state.error = null
      })
      .addCase(createGroup.fulfilled, (state, action) => {
        state.isCreating = false
        state.groups.push(action.payload)
        state.error = null
      })
      .addCase(createGroup.rejected, (state, action) => {
        state.isCreating = false
        state.error = action.payload
      })

      // Update group
      .addCase(updateGroup.pending, (state) => {
        state.isUpdating = true
        state.error = null
      })
      .addCase(updateGroup.fulfilled, (state, action) => {
        state.isUpdating = false
        if (state.currentGroup && state.currentGroup.id === action.payload.id) {
          state.currentGroup = action.payload
        }
        const index = state.groups.findIndex(group => group.id === action.payload.id)
        if (index !== -1) {
          state.groups[index] = action.payload
        }
        state.error = null
      })
      .addCase(updateGroup.rejected, (state, action) => {
        state.isUpdating = false
        state.error = action.payload
      })

      // Add member
      .addCase(addGroupMember.fulfilled, (state, action) => {
        if (state.currentGroup && state.currentGroup.id === action.payload.id) {
          state.currentGroup = action.payload
        }
      })

      // Remove member
      .addCase(removeMember.fulfilled, (state, action) => {
        if (state.currentGroup && state.currentGroup.id === action.payload.id) {
          state.currentGroup = action.payload
        }
      })

      // Update member role
      .addCase(updateMemberRole.fulfilled, (state, action) => {
        if (state.currentGroup && state.currentGroup.id === action.payload.id) {
          state.currentGroup = action.payload
        }
      })

      // Fetch group balance
      .addCase(fetchGroupBalance.fulfilled, (state, action) => {
        const { groupId, balances } = action.payload
        state.groupBalances[groupId] = balances
      })
  },
})

export const { 
  clearCurrentGroup, 
  clearError, 
  updateGroupInList, 
  setCurrentGroup 
} = groupSlice.actions

export default groupSlice.reducer