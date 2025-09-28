// Dashboard.jsx - Standalone version without external dependencies
import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  Users, AlertTriangle, CheckCircle, TrendingUp, 
  Calendar, Database, FileText, Activity 
} from 'lucide-react';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [dateRange, setDateRange] = useState({
    startDate: '',
    endDate: ''
  });

  // Mock data for demonstration (replace with your actual API calls)
  const mockDashboardData = {
    totalRecords: 164323,
    totalErrors: 164323,
    resolvedErrors: 12500,
    successRate: 92.4,
    resolutionRate: 76.1,
    averageRecordsPerDay: 5477,
    averageErrorsPerDay: 5477,
    recordsByFormat: [
      { name: 'Credit Data', value: 151077, color: '#007bff' },
      { name: 'CSV', value: 715, color: '#28a745' },
      { name: 'UPI Excel', value: 12531, color: '#6f42c1' }
    ],
    errorsByType: [
      { name: 'Credit Validation', count: 151077 },
      { name: 'CSV Processing', count: 715 },
      { name: 'Excel Validation', count: 12531 }
    ],
    processingTrend: [
      { date: '2025-09-22', records: 4200, errors: 420 },
      { date: '2025-09-23', records: 3800, errors: 380 },
      { date: '2025-09-24', records: 5200, errors: 520 },
      { date: '2025-09-25', records: 6100, errors: 610 },
      { date: '2025-09-26', records: 5900, errors: 590 },
      { date: '2025-09-27', records: 4500, errors: 450 },
      { date: '2025-09-28', records: 5800, errors: 580 }
    ],
    processingByType: [
      { processor: 'System', records: 150000 },
      { processor: 'Manual', records: 10000 },
      { processor: 'Automated', records: 4323 }
    ],
    errorStatusDistribution: [
      { status: 'Unresolved', count: 151823, percentage: 92.4 },
      { status: 'Resolved', count: 12500, percentage: 7.6 }
    ]
  };

  // Utility functions
  const formatNumber = (num) => {
    if (num == null || isNaN(num)) return '0';
    return new Intl.NumberFormat().format(num);
  };

  const formatLarge = (num) => {
    if (num == null || isNaN(num)) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatPercentage = (num) => {
    if (num == null || isNaN(num)) return '0%';
    return `${num.toFixed(1)}%`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusColor = (status) => {
    const colors = {
      'Unresolved': '#ef4444',
      'Resolved': '#22c55e',
      'Ignored': '#6b7280'
    };
    return colors[status] || '#6b7280';
  };

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In real implementation, you would make API calls here
      // const response = await fetch('http://localhost:8000/api/errors/stats');
      // const data = await response.json();
      
      setDashboardStats(mockDashboardData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Show error notification
      alert('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  // Handle date range change
  const handleDateRangeChange = (field, value) => {
    setDateRange(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!dashboardStats) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">Failed to load dashboard data. Please try again.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Overview of data processing and validation metrics
          </p>
        </div>

        {/* Date Range Filter */}
        <div className="flex space-x-4 mt-4 sm:mt-0">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={dateRange.startDate}
              onChange={(e) => handleDateRangeChange('startDate', e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={dateRange.endDate}
              onChange={(e) => handleDateRangeChange('endDate', e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Records</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatLarge(dashboardStats.totalRecords)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatNumber(dashboardStats.totalRecords)} total
              </p>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-600">
                {formatNumber(dashboardStats.averageRecordsPerDay)} per day avg
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Errors</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatLarge(dashboardStats.totalErrors)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatNumber(dashboardStats.totalErrors)} errors
              </p>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-sm">
              <CheckCircle className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-600">
                {formatNumber(dashboardStats.resolvedErrors)} resolved
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatPercentage(dashboardStats.successRate)}
              </p>
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full"
                style={{ width: `${dashboardStats.successRate}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Database className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Resolution Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatPercentage(dashboardStats.resolutionRate)}
              </p>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-sm">
              <Calendar className="h-4 w-4 text-blue-500 mr-1" />
              <span className="text-blue-600">
                {formatNumber(dashboardStats.averageErrorsPerDay)} errors/day avg
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Records by Source Format */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Records by Source Format
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={dashboardStats.recordsByFormat}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  nameKey="name"
                >
                  {dashboardStats.recordsByFormat.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [formatNumber(value), 'Records']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Errors by Type */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Errors by Type
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dashboardStats.errorsByType}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis 
                  tickFormatter={(value) => formatLarge(value)}
                />
                <Tooltip 
                  formatter={(value) => [formatNumber(value), 'Errors']}
                />
                <Bar 
                  dataKey="count" 
                  fill="#ef4444"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Daily Activity Trend */}
        <div className="bg-white rounded-lg shadow-sm border p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Processing Activity Trend (Last 7 Days)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dashboardStats.processingTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date"
                  tickFormatter={formatDate}
                />
                <YAxis 
                  tickFormatter={(value) => formatLarge(value)}
                />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  formatter={(value, name) => [
                    formatNumber(value), 
                    name === 'records' ? 'Records' : 'Errors'
                  ]}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="records" 
                  stroke="#22c55e" 
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Processed Records"
                />
                <Line 
                  type="monotone" 
                  dataKey="errors" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Errors Found"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Processing Summary Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Processing Summary by Type
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Processor Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Records
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dashboardStats.processingByType.map((processor, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {processor.processor}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatNumber(processor.records)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Error Status Distribution
          </h3>
          <div className="space-y-4">
            {dashboardStats.errorStatusDistribution.map((status, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div 
                    className="w-4 h-4 rounded-full mr-3"
                    style={{ backgroundColor: getStatusColor(status.status) }}
                  ></div>
                  <span className="text-sm font-medium text-gray-900">
                    {status.status}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    {formatNumber(status.count)}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({formatPercentage(status.percentage)})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center">
          <FileText className="h-5 w-5 text-blue-500 mr-2" />
          <div>
            <p className="text-sm font-medium text-blue-800">
              Dashboard Overview
            </p>
            <p className="text-sm text-blue-600">
              Displaying data from {formatNumber(dashboardStats.totalRecords)} total records across 3 databases: 
              Credit Data ({formatNumber(151077)}), CSV ({formatNumber(715)}), and UPI Excel ({formatNumber(12531)})
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
