// ErrorLogs.jsx - Complete updated component
import React, { useState, useEffect } from 'react';
import { 
  ChevronLeft, ChevronRight, Search, Filter, 
  Download, RefreshCw, Eye, AlertCircle, CheckCircle,
  XCircle, Clock, User, BarChart3, Database, FileText,
  TrendingUp, Activity
} from 'lucide-react';
import { errorsAPI, downloadAPI, handleFileDownload } from '../services/api';
import { dateUtils, numberUtils, colorUtils } from '../utils/helpers';
import toast from 'react-hot-toast';

const ErrorLogs = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [dbStatus, setDbStatus] = useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [customerErrors, setCustomerErrors] = useState([]);
  const [showCustomerView, setShowCustomerView] = useState(false);
  
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalRecords: 0,
    recordsPerPage: 10
  });
  
  const [filters, setFilters] = useState({
    search: '',
    errorType: '',
    sourceFormat: '',
    database: '',
    customerId: '',
    startDate: '',
    endDate: '',
    sortBy: 'createdAt',
    sortOrder: 'desc'
  });
  
  const [downloading, setDownloading] = useState(false);
  const [selectedError, setSelectedError] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(null);

  // Fetch error logs
  const fetchErrors = async (page = 1) => {
    setLoading(true);
    try {
      const params = {
        page,
        limit: pagination.recordsPerPage,
        ...filters
      };

      const response = await errorsAPI.getErrors(params);
      setData(response.data || []);
      setPagination(response.pagination || {});
      
      if (response.summary) {
        console.log('API Summary:', response.summary);
      }
    } catch (error) {
      console.error('Error fetching error logs:', error);
      toast.error('Failed to fetch error logs');
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch statistics
  const fetchStats = async () => {
    try {
      const statsData = await errorsAPI.getErrorStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('Failed to fetch statistics');
    }
  };

  // Fetch database status
  const fetchDbStatus = async () => {
    try {
      const statusData = await errorsAPI.getDatabaseStatus();
      setDbStatus(statusData);
    } catch (error) {
      console.error('Error fetching database status:', error);
    }
  };

  // Fetch customer-specific errors
  const fetchCustomerErrors = async (customerId) => {
    if (!customerId.trim()) {
      toast.error('Please enter a customer ID');
      return;
    }

    setLoading(true);
    try {
      const response = await errorsAPI.getCustomerErrors(customerId);
      setCustomerErrors(response.errors || []);
      setSelectedCustomer(customerId);
      setShowCustomerView(true);
      
      toast.success(`Found ${response.totalErrors} errors for customer ${customerId}`);
    } catch (error) {
      console.error('Error fetching customer errors:', error);
      toast.error('Failed to fetch customer errors');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchErrors();
    fetchStats();
    fetchDbStatus();
  }, [filters, pagination.recordsPerPage]);

  // Handle filter changes
  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Handle customer search
  const handleCustomerSearch = () => {
    if (filters.customerId.trim()) {
      fetchCustomerErrors(filters.customerId.trim());
    } else {
      toast.error('Please enter a customer ID');
    }
  };

  // Handle pagination
  const handlePageChange = (page) => {
    fetchErrors(page);
  };

  // Handle download
  const handleDownload = async (format) => {
    setDownloading(true);
    try {
      const params = {
        format,
        ...filters,
        filename: `error_logs_${dateUtils.formatDate(new Date(), 'yyyy-MM-dd')}`
      };

      const response = await downloadAPI.downloadErrors(params);
      const result = handleFileDownload(response, `errors.${format}`);
      
      if (result.success) {
        toast.success(`Downloaded ${result.filename}`);
      } else {
        toast.error('Download failed');
      }
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download data');
    } finally {
      setDownloading(false);
    }
  };

  // Handle status update
  const handleStatusUpdate = async (errorId, newStatus, resolutionNotes = '') => {
    setUpdatingStatus(errorId);
    try {
      await errorsAPI.updateErrorStatus(
        errorId, 
        newStatus, 
        'System User', 
        resolutionNotes
      );
      
      toast.success('Status updated successfully');
      if (showCustomerView) {
        fetchCustomerErrors(selectedCustomer);
      } else {
        fetchErrors(pagination.currentPage);
      }
      setSelectedError(null);
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Failed to update status');
    } finally {
      setUpdatingStatus(null);
    }
  };

  // Handle sort
  const handleSort = (field) => {
    const newOrder = filters.sortBy === field && filters.sortOrder === 'asc' ? 'desc' : 'asc';
    setFilters(prev => ({
      ...prev,
      sortBy: field,
      sortOrder: newOrder
    }));
  };

  // Clear filters
  const clearFilters = () => {
    setFilters({
      search: '',
      errorType: '',
      sourceFormat: '',
      database: '',
      customerId: '',
      startDate: '',
      endDate: '',
      sortBy: 'createdAt',
      sortOrder: 'desc'
    });
    setShowCustomerView(false);
    setCustomerErrors([]);
    setSelectedCustomer('');
  };

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'RESOLVED':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'IGNORED':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  // Get error type color
  const getErrorTypeColor = (errorType) => {
    return colorUtils.getErrorTypeColor(errorType);
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Statistics Dashboard */}
      {stats && (
        <div className="mb-6">
          {/* Main KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="p-2 bg-red-100 rounded-lg">
                  <AlertCircle className="h-6 w-6 text-red-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Errors</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {numberUtils.formatNumber(stats.totalErrors)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BarChart3 className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Error Types</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {Object.keys(stats.errorsByType).length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <User className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Customers Affected</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {Object.keys(stats.errorsByCustomer || {}).length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Database className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Databases</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {Object.keys(stats.errorsByDatabase).length}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Database Status Cards */}
          {dbStatus && (
            <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Database className="h-5 w-5 mr-2" />
                Database Connection Status
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(dbStatus.databases).map(([dbName, dbInfo]) => (
                  <div key={dbName} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{dbName}</h4>
                      <div className={`h-3 w-3 rounded-full ${
                        dbInfo.status === 'Connected' ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                    </div>
                    <p className="text-sm text-gray-600">{dbInfo.status}</p>
                    <p className="text-sm text-gray-500">
                      {dbInfo.error_count} errors
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Customers with Errors */}
          {stats.topCustomersWithErrors && stats.topCustomersWithErrors.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border mb-6 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                Top Customers with Most Errors
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {stats.topCustomersWithErrors.slice(0, 5).map((customer, index) => (
                  <div 
                    key={customer.customerId}
                    className="bg-gray-50 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => fetchCustomerErrors(customer.customerId)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {customer.customerId}
                        </p>
                        <p className="text-xs text-gray-500">
                          {customer.errorCount} errors
                        </p>
                      </div>
                      <div className="text-lg font-bold text-red-500">
                        #{index + 1}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Distribution Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Error by Type */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Errors by Type
              </h3>
              <div className="space-y-3">
                {Object.entries(stats.errorsByType).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div 
                        className="w-4 h-4 rounded mr-3"
                        style={{ backgroundColor: getErrorTypeColor(type) }}
                      ></div>
                      <span className="text-sm text-gray-700">
                        {type.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Error by Source */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Errors by Source Format
              </h3>
              <div className="space-y-3">
                {Object.entries(stats.errorsBySource).map(([source, count]) => (
                  <div key={source} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FileText className="h-4 w-4 text-gray-400 mr-3" />
                      <span className="text-sm text-gray-700">{source}</span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border">
        {/* Header */}
        <div className="p-6 border-b">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">
                {showCustomerView ? `Errors for Customer: ${selectedCustomer}` : 'Error Logs'}
              </h2>
              <p className="text-gray-600 mt-1">
                {showCustomerView ? 
                  `Showing ${customerErrors.length} errors for this customer` :
                  'Monitor and manage data processing errors across all databases'
                }
              </p>
            </div>
            
            <div className="flex items-center space-x-3 mt-4 sm:mt-0">
              {showCustomerView && (
                <button
                  onClick={() => {
                    setShowCustomerView(false);
                    setCustomerErrors([]);
                    setSelectedCustomer('');
                    fetchErrors(1);
                  }}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  ← Back to All Errors
                </button>
              )}
              
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </button>
              
              <div className="relative">
                <button
                  onClick={() => document.getElementById('downloadMenu').classList.toggle('hidden')}
                  disabled={downloading}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
                >
                  <Download className="h-4 w-4 mr-2" />
                  {downloading ? 'Downloading...' : 'Download'}
                </button>
                
                <div id="downloadMenu" className="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                  <div className="py-1">
                    <button
                      onClick={() => handleDownload('csv')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Download as CSV
                    </button>
                    <button
                      onClick={() => handleDownload('excel')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Download as Excel
                    </button>
                    <button
                      onClick={() => handleDownload('json')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Download as JSON
                    </button>
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => {
                  if (showCustomerView) {
                    fetchCustomerErrors(selectedCustomer);
                  } else {
                    fetchErrors(pagination.currentPage);
                    fetchStats();
                    fetchDbStatus();
                  }
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search
                  </label>
                  <div className="relative">
                    <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search errors..."
                      value={filters.search}
                      onChange={(e) => handleFilterChange('search', e.target.value)}
                      className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                    />
                  </div>
                </div>

                {/* Customer ID Search */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Customer ID Search
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      placeholder="Enter customer ID..."
                      value={filters.customerId}
                      onChange={(e) => handleFilterChange('customerId', e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleCustomerSearch()}
                      className="flex-1 block rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                    />
                    <button
                      onClick={handleCustomerSearch}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <User className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Error Type
                  </label>
                  <select
                    value={filters.errorType}
                    onChange={(e) => handleFilterChange('errorType', e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                  >
                    <option value="">All Types</option>
                    <option value="CREDIT_VALIDATION">Credit Validation</option>
                    <option value="CSV_PROCESSING">CSV Processing</option>
                    <option value="EXCEL_VALIDATION">Excel Validation</option>
                    <option value="MISSING_FIELD">Missing Field</option>
                    <option value="INVALID_FORMAT">Invalid Format</option>
                    <option value="VALIDATION_ERROR">Validation Error</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Format
                  </label>
                  <select
                    value={filters.sourceFormat}
                    onChange={(e) => handleFilterChange('sourceFormat', e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                  >
                    <option value="">All Formats</option>
                    <option value="CSV">CSV</option>
                    <option value="Excel">Excel</option>
                    <option value="XML">XML</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Database
                  </label>
                  <select
                    value={filters.database}
                    onChange={(e) => handleFilterChange('database', e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                  >
                    <option value="">All Databases</option>
                    <option value="CREDIT_DATA">Credit Data</option>
                    <option value="CSV">CSV</option>
                    <option value="UPI_EXCEL">UPI Excel</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={filters.startDate}
                    onChange={(e) => handleFilterChange('startDate', e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={filters.endDate}
                    onChange={(e) => handleFilterChange('endDate', e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                  />
                </div>

                <div className="flex items-end">
                  <button
                    onClick={clearFilters}
                    className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                  >
                    Clear All Filters
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th 
                  onClick={() => handleSort('errorType')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Error Type
                  {filters.sortBy === 'errorType' && (
                    <span className="ml-1">{filters.sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customer ID
                </th>
                <th 
                  onClick={() => handleSort('sourceFormat')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Source
                  {filters.sortBy === 'sourceFormat' && (
                    <span className="ml-1">{filters.sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Database
                </th>
                <th 
                  onClick={() => handleSort('createdAt')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Date
                  {filters.sortBy === 'createdAt' && (
                    <span className="ml-1">{filters.sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
                      <span className="ml-2 text-gray-500">Loading...</span>
                    </div>
                  </td>
                </tr>
              ) : (showCustomerView ? customerErrors : data).length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    {showCustomerView ? 
                      `No errors found for customer ${selectedCustomer}` :
                      'No error logs found'
                    }
                  </td>
                </tr>
              ) : (
                (showCustomerView ? customerErrors : data).map((error) => (
                  <tr key={error._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span 
                        className="inline-flex px-2 py-1 text-xs font-semibold rounded-full text-white"
                        style={{ backgroundColor: getErrorTypeColor(error.errorType) }}
                      >
                        {error.errorType ? error.errorType.replace('_', ' ') : 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                      <div className="truncate" title={error.errorMessage}>
                        {error.errorMessage || 'No message'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => fetchCustomerErrors(error.customerId)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                        disabled={!error.customerId || error.customerId === 'N/A'}
                      >
                        {error.customerId || 'N/A'}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        {error.sourceFormat}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {error.database_source}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {dateUtils.formatDateTime(error.createdAt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setSelectedError(error)}
                          className="text-blue-600 hover:text-blue-900"
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!showCustomerView && pagination.totalRecords > 0 && (
          <div className="px-6 py-4 border-t bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {((pagination.currentPage - 1) * pagination.recordsPerPage) + 1} to{' '}
                {Math.min(pagination.currentPage * pagination.recordsPerPage, pagination.totalRecords)} of{' '}
                {numberUtils.formatNumber(pagination.totalRecords)} results
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(pagination.currentPage - 1)}
                  disabled={!pagination.hasPrevPage}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                
                <span className="text-sm text-gray-700">
                  Page {pagination.currentPage} of {pagination.totalPages}
                </span>
                
                <button
                  onClick={() => handlePageChange(pagination.currentPage + 1)}
                  disabled={!pagination.hasNextPage}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error Detail Modal */}
      {selectedError && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Error Details - {selectedError.database_source}
              </h3>
              <button
                onClick={() => setSelectedError(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Error ID</label>
                  <p className="text-sm text-gray-900 font-mono">{selectedError._id}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Error Type</label>
                  <span 
                    className="inline-flex px-2 py-1 text-xs font-semibold rounded-full text-white"
                    style={{ backgroundColor: getErrorTypeColor(selectedError.errorType) }}
                  >
                    {selectedError.errorType ? selectedError.errorType.replace('_', ' ') : 'Unknown'}
                  </span>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Error Message</label>
                  <p className="text-sm text-gray-900 bg-red-50 p-2 rounded">
                    {selectedError.errorMessage}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Customer ID</label>
                  <p className="text-sm text-gray-900 font-mono">
                    {selectedError.customerId || 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Transaction ID</label>
                  <p className="text-sm text-gray-900 font-mono">
                    {selectedError.transactionId || 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Source Format</label>
                  <p className="text-sm text-gray-900">{selectedError.sourceFormat}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Database Source</label>
                  <p className="text-sm text-gray-900">{selectedError.database_source}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Source File</label>
                  <p className="text-sm text-gray-900">{selectedError.sourceFile || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Line Number</label>
                  <p className="text-sm text-gray-900">{selectedError.lineNumber || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Processed By</label>
                  <p className="text-sm text-gray-900">{selectedError.processedBy}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Processed At</label>
                  <p className="text-sm text-gray-900">
                    {dateUtils.formatDateTime(selectedError.createdAt)}
                  </p>
                </div>
              </div>
              
              {selectedError.errorDetails && selectedError.errorDetails.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Error Details</label>
                  <div className="bg-red-50 p-3 rounded-md">
                    <ul className="text-sm text-red-800 space-y-1">
                      {selectedError.errorDetails.map((detail, index) => (
                        <li key={index}>• {detail}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {selectedError.rawData && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Raw Data</label>
                  <div className="bg-gray-50 p-3 rounded-md max-h-64 overflow-y-auto">
                    <pre className="text-xs text-gray-900 whitespace-pre-wrap">
                      {JSON.stringify(selectedError.rawData, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ErrorLogs;
