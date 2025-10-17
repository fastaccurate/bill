import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { initializeAuth, fetchUserProfile } from './redux/slices/authSlice'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Home from './pages/Home'
import Groups from './pages/Groups'
import Expenses from './pages/Expenses'
import LoadingSpinner from './components/LoadingSpinner'

function App() {
  const dispatch = useDispatch()
  const { isAuthenticated, isLoading, user } = useSelector((state) => state.auth)

  useEffect(() => {
    // Initialize auth state from localStorage
    dispatch(initializeAuth())

    // Fetch user profile if token exists
    const token = localStorage.getItem('accessToken')
    if (token && !user) {
      dispatch(fetchUserProfile())
    }
  }, [dispatch, user])

  // Private route wrapper
  const PrivateRoute = ({ children }) => {
    return isAuthenticated ? children : <Navigate to="/login" replace />
  }

  // Public route wrapper (redirect if authenticated)
  const PublicRoute = ({ children }) => {
    return !isAuthenticated ? children : <Navigate to="/" replace />
  }

  if (isLoading && !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="large" message="Loading application..." />
      </div>
    )
  }

  return (
    <div className="App">
      <Routes>
        {/* Public Routes */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } 
        />
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } 
        />

        {/* Private Routes */}
        <Route 
          path="/*" 
          element={
            <PrivateRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/groups" element={<Groups />} />
                  <Route path="/groups/:groupId" element={<Groups />} />
                  <Route path="/expenses" element={<Expenses />} />
                  <Route path="/expenses/:expenseId" element={<Expenses />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            </PrivateRoute>
          } 
        />
      </Routes>
    </div>
  )
}

export default App