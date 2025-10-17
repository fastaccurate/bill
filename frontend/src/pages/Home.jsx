import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { fetchUserGroups } from '../redux/slices/groupSlice'
import { 
  UserGroupIcon, 
  CurrencyDollarIcon,
  PlusIcon,
  TrendingUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import LoadingSpinner from '../components/LoadingSpinner'

const Home = () => {
  const dispatch = useDispatch()
  const { user } = useSelector((state) => state.auth)
  const { groups, isLoading } = useSelector((state) => state.groups)

  useEffect(() => {
    dispatch(fetchUserGroups())
  }, [dispatch])

  if (isLoading) {
    return <LoadingSpinner message="Loading dashboard..." />
  }

  // Calculate dashboard statistics
  const totalGroups = groups.length
  const activeGroups = groups.filter(group => group.is_active).length
  const totalExpenses = groups.reduce((sum, group) => sum + (group.total_expenses || 0), 0)

  // Recent activities (mock data for demo)
  const recentActivities = [
    {
      id: 1,
      type: 'expense_added',
      message: 'New expense "Dinner at Italian Restaurant" added to Friends group',
      amount: 85.50,
      time: '2 hours ago',
      user: 'John Doe'
    },
    {
      id: 2,
      type: 'payment_settled',
      message: 'Payment settled for "Movie tickets"',
      amount: 25.00,
      time: '5 hours ago',
      user: 'You'
    },
    {
      id: 3,
      type: 'group_created',
      message: 'New group "Weekend Trip" created',
      time: '1 day ago',
      user: 'You'
    },
  ]

  const stats = [
    {
      name: 'Active Groups',
      value: activeGroups,
      total: totalGroups,
      icon: UserGroupIcon,
      color: 'bg-blue-500',
      change: '+2 this month'
    },
    {
      name: 'Total Expenses',
      value: `$${totalExpenses.toFixed(2)}`,
      icon: CurrencyDollarIcon,
      color: 'bg-green-500',
      change: '+$125 this week'
    },
    {
      name: 'Pending Settlements',
      value: '3',
      icon: ExclamationTriangleIcon,
      color: 'bg-yellow-500',
      change: '2 due this week'
    },
    {
      name: 'Settled Payments',
      value: '12',
      icon: CheckCircleIcon,
      color: 'bg-purple-500',
      change: '+3 this week'
    },
  ]

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          Welcome back, {user?.full_name?.split(' ')[0] || 'there'}! 👋
        </h1>
        <p className="text-primary-100 text-lg">
          Here's what's happening with your bill splitting activities.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
            <div className="mt-4">
              <p className="text-sm text-gray-500">{stat.change}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Groups */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Your Groups</h2>
              <Link
                to="/groups"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="p-6">
            {groups.length === 0 ? (
              <div className="text-center py-8">
                <UserGroupIcon className="mx-auto h-12 w-12 text-gray-300" />
                <h3 className="mt-4 text-sm font-medium text-gray-900">No groups yet</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Get started by creating your first group to split bills with friends.
                </p>
                <Link
                  to="/groups"
                  className="mt-4 inline-flex items-center px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700"
                >
                  <PlusIcon className="mr-2 h-4 w-4" />
                  Create Group
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {groups.slice(0, 4).map((group) => (
                  <Link
                    key={group.id}
                    to={`/groups/${group.id}`}
                    className="block p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">{group.name}</h3>
                        <p className="text-sm text-gray-500">
                          {group.member_count} member{group.member_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          ${(group.total_expenses || 0).toFixed(2)}
                        </p>
                        <p className="text-xs text-gray-500">Total expenses</p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentActivities.map((activity) => (
                <div key={activity.id} className="flex space-x-3">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 bg-gray-200 rounded-full flex items-center justify-center">
                      <TrendingUpIcon className="h-4 w-4 text-gray-500" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                    {activity.amount && (
                      <p className="text-sm font-medium text-green-600">
                        ${activity.amount.toFixed(2)}
                      </p>
                    )}
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/groups"
            className="flex items-center p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
          >
            <PlusIcon className="h-6 w-6 text-primary-600 mr-3" />
            <span className="text-sm font-medium text-primary-700">Create Group</span>
          </Link>
          <Link
            to="/expenses"
            className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
          >
            <CurrencyDollarIcon className="h-6 w-6 text-green-600 mr-3" />
            <span className="text-sm font-medium text-green-700">Add Expense</span>
          </Link>
          <button className="flex items-center p-4 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors">
            <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600 mr-3" />
            <span className="text-sm font-medium text-yellow-700">Send Reminders</span>
          </button>
          <button className="flex items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
            <TrendingUpIcon className="h-6 w-6 text-purple-600 mr-3" />
            <span className="text-sm font-medium text-purple-700">View Reports</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Home