// DataTable.jsx - Standalone version without external dependencies
import React, { useState, useEffect } from 'react';
import { 
  ChevronLeft, ChevronRight, Search, Filter, 
  Download, RefreshCw, Eye, Calendar, User,
  FileText, Clock, Mail, Phone
} from 'lucide-react';

const DataTable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalRecords: 0,
    recordsPerPage: 10
  });
  const [filters, setFilters] = useState({
    search: '',
    sourceFormat: '',
    processedBy: '',
    startDate: '',
    endDate: '',
    sortBy: 'createdAt',
    sortOrder: 'desc'
  });
  const [downloading, setDownloading] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Mock customer data (replace with your API data)
  const mockCustomerData = {
    data: [
      {
        _id: '1',
        customerId: 'CUST001',
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@email.com',
        phone: '+1-555-0123',
        sourceFormat: 'CSV',
        processedBy: 'System',
        createdAt: '2025-09-28T00:00:00Z',
        dateOfBirth: '1990-01-15',
        address: {
          street: '123 Main St',
          city: 'New York',
          state: 'NY',
          zipCode: '10001',
          country: 'USA'
        },
        additionalData: {
          totalPurchases: 15,
          lastPurchase: '2025-09-20'
        }
      },
      {
        _id: '2',
        customerId: 'CUST002',
        firstName: 'Jane',
        lastName: 'Smith',
        email: 'jane.smith@email.com',
        phone: '+1-555-0124',
        sourceFormat: 'Excel',
        processedBy: 'System',
        createdAt: '2025-09-27T12:00:00Z',
        dateOfBirth: '1985-05-20',
        address: {
          street: '456 Oak Ave',
          city: 'Los Angeles',
          state: 'CA',
          zipCode: '90210',
          country: 'USA'
        },
        additionalData: {
          totalPurchases: 8,
          lastPurchase: '2025-09-25'
        }
      },
      {
        _id: '3',
        customerId: 'CUST003',
        firstName: 'Mike',
        lastName: 'Johnson',
        email: 'mike.johnson@email.com',
        phone: '+1-555-0125',
        sourceFormat: 'XML',
        processedBy: 'Manual',
        createdAt: '2025-09-26T08:30:00Z',
        dateOfBirth: '1992-12-10',
        address: {
          street: '789 Pine St',
          city: 'Chicago',
          state: 'IL',
          zipCode: '60601',
          country: 'USA'
        },
        additionalData: {
          totalPurchases: 22,
          lastPurchase: '2025-09-28'
        }
      },
      {
        _id: '4',
        customerId: 'CUST004',
        firstName: 'Sarah',
        lastName: 'Wilson',
        email: 'sarah.wilson@email.com',
        phone: '+1-555-0126',
        sourceFormat: 'CSV',
        processedBy: 'System',
        createdAt: '2025-09-25T16:45:00Z',
        dateOfBirth: '1988-07-03',
        additionalData: {
          totalPurchases: 5,
          lastPurchase: '2025-09-22'
        }
      },
      {
        _id: '5',
        customerId: 'CUST005',
        firstName: 'David',
        lastName: 'Brown',
        email: 'david.brown@email.com',
        phone: '+1-555-0127',
        sourceFormat: 'JSON',
        processedBy: 'Automated',
        createdAt: '2025-09-24T10:15:00Z',
        dateOfBirth: '1995-03-18',
        additionalData: {
          totalPurchases: 12,
          lastPurchase: '2025-09-27'
        }
      }
    ],
    pagination: {
      currentPage: 1,
      totalPages: 1,
      totalRecords: 5,
      recordsPerPage: 10,
      hasPrevPage: false,
      hasNextPage: false
    }
  };

  // Utility functions
  const formatNumber = (num) => {
    if (num == null || isNaN(num)) return '0';
    return new Intl.NumberFormat().format(num);
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return dateString;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (error) {
      return dateString;
    }
  };

  const getCurrentDateForFilename = () => {
    return new Date().toISOString().split('T')[0];
  };

  // Fetch customers data
  const fetchCustomers = async (page = 1) => {
    setLoading(true);
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // In real implementation, you would make API calls here
      // const response = await fetch(`http://localhost:8000/api/customers?page=${page}`);
      // const data = await response.json();
      
      // Filter mock data based on current filters
      let filteredData = [...mockCustomerData.data];
      
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        filteredData = filteredData.filter(customer => 
          customer.customerId.toLowerCase().includes(searchTerm) ||
          `${customer.firstName} ${customer.lastName}`.toLowerCase().includes(searchTerm) ||
          customer.email.toLowerCase().includes(searchTerm)
        );
      }
      
      if (filters.sourceFormat) {
        filteredData = filteredData.filter(customer => 
          customer.sourceFormat === filters.sourceFormat
        );
      }
      
      if (filters.processedBy) {
        filteredData = filteredData.filter(customer => 
          customer.processedBy.toLowerCase().includes(filters.processedBy.toLowerCase())
        );
      }
      
      setData(filteredData);
      setPagination({
        currentPage: page,
        totalPages: Math.ceil(filteredData.length / pagination.recordsPerPage),
        totalRecords: filteredData.length,
        recordsPerPage: pagination.recordsPerPage,
        hasPrevPage: page > 1,
        hasNextPage: page < Math.ceil(filteredData.length / pagination.recordsPerPage)
      });
      
    } catch (error) {
      console.error('Error fetching customers:', error);
      alert('Failed to fetch customer data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [filters]);

  // Handle filter changes
  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Handle pagination
  const handlePageChange = (page) => {
    setPagination(prev => ({ ...prev, currentPage: page }));
    fetchCustomers(page);
  };

  // Handle download
  const handleDownload = async (format) => {
    setDownloading(true);
    try {
      // Simulate download process
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const filename = `customers_${getCurrentDateForFilename()}.${format}`;
      
      // In real implementation, you would generate and download the file
      // For now, just show success message
      console.log(`Downloading ${filename} with ${data.length} records`);
      alert(`Downloaded ${filename} successfully!`);
      
      // Close dropdown menu
      document.getElementById('downloadMenu').classList.add('hidden');
      
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download data');
    } finally {
      setDownloading(false);
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
      sourceFormat: '',
      processedBy: '',
      startDate: '',
      endDate: '',
      sortBy: 'createdAt',
      sortOrder: 'desc'
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-sm border">
        {/* Header */}
        <div className="p-6 border-b">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">
                Customer Data
              </h2>
              <p className="text-gray-600 mt-1">
                View and manage processed customer records
              </p>
            </div>
            
            <div className="flex items-center space-x-3 mt-4 sm:mt-0">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
                {Object.values(filters).some(v => v && v !== 'createdAt' && v !== 'desc') && (
                  <span className="ml-2 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                    Active
                  </span>
                )}
              </button>
              
              <div className="relative">
                <button
                  onClick={() => document.getElementById('downloadMenu').classList.toggle('hidden')}
                  disabled={downloading}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  <Download className="h-4 w-4 mr-2" />
                  {downloading ? 'Downloading...' : 'Download'}
                </button>
                
                <div id="downloadMenu" className="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border">
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
                onClick={() => fetchCustomers(pagination.currentPage)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search
                  </label>
                  <div className="relative">
                    <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search customers..."
                      value={filters.search}
                      onChange={(e) => handleFilterChange('search', e.target.value)}
                      className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Format
                  </label>
                  <select
                    value={filters.sourceFormat}
                    onChange={(e) => handleFilterChange('sourceFormat', e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  >
                    <option value="">All Formats</option>
                    <option value="CSV">CSV</option>
                    <option value="Excel">Excel</option>
                    <option value="XML">XML</option>
                    <option value="JSON">JSON</option>
                    <option value="PDF">PDF</option>
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
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
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
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Processed By
                  </label>
                  <input
                    type="text"
                    placeholder="Processor name..."
                    value={filters.processedBy}
                    onChange={(e) => handleFilterChange('processedBy', e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>

                <div className="flex items-end space-x-2">
                  <button
                    onClick={clearFilters}
                    className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Clear Filters
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
                  onClick={() => handleSort('customerId')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Customer ID
                    {filters.sortBy === 'customerId' && (
                      <span className="ml-1 text-gray-400">
                        {filters.sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('firstName')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Name
                    {filters.sortBy === 'firstName' && (
                      <span className="ml-1 text-gray-400">
                        {filters.sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('email')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Email
                    {filters.sortBy === 'email' && (
                      <span className="ml-1 text-gray-400">
                        {filters.sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone
                </th>
                <th 
                  onClick={() => handleSort('sourceFormat')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Source
                    {filters.sortBy === 'sourceFormat' && (
                      <span className="ml-1 text-gray-400">
                        {filters.sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('processedBy')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Processed By
                    {filters.sortBy === 'processedBy' && (
                      <span className="ml-1 text-gray-400">
                        {filters.sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('createdAt')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Processed At
                    {filters.sortBy === 'createdAt' && (
                      <span className="ml-1 text-gray-400">
                        {filters.sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                      <span className="ml-2 text-gray-500">Loading customers...</span>
                    </div>
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-4 text-center text-gray-500">
                    <div className="py-8">
                      <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-lg font-medium text-gray-900 mb-1">No customer data found</p>
                      <p className="text-gray-500">
                        Try adjusting your filters or check if data exists in the system.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                data.map((customer) => (
                  <tr key={customer._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {customer.customerId || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {`${customer.firstName || ''} ${customer.lastName || ''}`.trim() || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <Mail className="h-4 w-4 text-gray-400 mr-2" />
                        {customer.email || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <Phone className="h-4 w-4 text-gray-400 mr-2" />
                        {customer.phone || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {customer.sourceFormat}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {customer.processedBy}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 text-gray-400 mr-2" />
                        {formatDateTime(customer.createdAt)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button
                        onClick={() => setSelectedCustomer(customer)}
                        className="text-blue-600 hover:text-blue-900"
                        title="View customer details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pagination.totalRecords > 0 && (
          <div className="px-6 py-4 border-t bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing <span className="font-medium">
                  {((pagination.currentPage - 1) * pagination.recordsPerPage) + 1}
                </span> to <span className="font-medium">
                  {Math.min(pagination.currentPage * pagination.recordsPerPage, pagination.totalRecords)}
                </span> of <span className="font-medium">
                  {formatNumber(pagination.totalRecords)}
                </span> results
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
                  Page <span className="font-medium">{pagination.currentPage}</span> of{' '}
                  <span className="font-medium">{pagination.totalPages}</span>
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

      {/* Enhanced Customer Detail Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white max-h-screen overflow-y-auto">
            <div className="flex items-center justify-between mb-4 pb-4 border-b">
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Customer Details
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  Customer ID: {selectedCustomer.customerId}
                </p>
              </div>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Personal Information */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                  <User className="h-5 w-5 mr-2" />
                  Personal Information
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Customer ID</label>
                    <p className="text-sm text-gray-900 font-mono">{selectedCustomer.customerId || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Full Name</label>
                    <p className="text-sm text-gray-900">
                      {`${selectedCustomer.firstName || ''} ${selectedCustomer.lastName || ''}`.trim() || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.email || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Phone</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.phone || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Date of Birth</label>
                    <p className="text-sm text-gray-900">
                      {selectedCustomer.dateOfBirth ? formatDate(selectedCustomer.dateOfBirth) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Processing Information */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  Processing Information
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Source Format</label>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      {selectedCustomer.sourceFormat}
                    </span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Processed By</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.processedBy}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Processed At</label>
                    <p className="text-sm text-gray-900">{formatDateTime(selectedCustomer.createdAt)}</p>
                  </div>
                </div>
              </div>
              
              {/* Address Information */}
              {selectedCustomer.address && (
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Address Information</h4>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-900">
                      {[
                        selectedCustomer.address.street,
                        selectedCustomer.address.city,
                        selectedCustomer.address.state,
                        selectedCustomer.address.zipCode,
                        selectedCustomer.address.country
                      ].filter(Boolean).join(', ') || 'No address provided'}
                    </p>
                  </div>
                </div>
              )}
              
              {/* Additional Data */}
              {selectedCustomer.additionalData && Object.keys(selectedCustomer.additionalData).length > 0 && (
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Additional Information</h4>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(selectedCustomer.additionalData).map(([key, value]) => (
                        <div key={key}>
                          <label className="block text-sm font-medium text-gray-700 capitalize">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </label>
                          <p className="text-sm text-gray-900">{value || 'N/A'}</p>
                        </div>
                      ))}
                    </div>
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

export default DataTable;
