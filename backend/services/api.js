// src/services/api.js
const API_BASE_URL = 'http://localhost:8000/api';

export const errorsAPI = {
  getErrors: async (params) => {
    const cleanedParams = Object.entries(params)
      .filter(([_, v]) => v != null && v !== '' && v !== undefined)
      .reduce((acc, [k, v]) => ({ ...acc, [k]: v }), {});
    
    const queryString = new URLSearchParams(cleanedParams).toString();
    const url = `${API_BASE_URL}/errors${queryString ? `?${queryString}` : ''}`;
    
    console.log('🔍 Fetching from:', url);
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  getErrorStats: async () => {
    const response = await fetch(`${API_BASE_URL}/errors/stats`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  getCustomerErrors: async (customerId) => {
    const response = await fetch(`${API_BASE_URL}/errors/customer/${encodeURIComponent(customerId)}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  getDatabaseStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/databases/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  updateErrorStatus: async (errorId, status, userId, notes) => {
    // Placeholder - will be implemented later
    return Promise.resolve({ success: true });
  }
};

// Add the missing customersAPI that other components expect
export const customersAPI = {
  getCustomers: async (params = {}) => {
    // Use the existing customer errors endpoint as a workaround
    try {
      const stats = await errorsAPI.getErrorStats();
      const customers = stats.topCustomersWithErrors || [];
      
      return {
        data: customers.map(customer => ({
          id: customer.customerId,
          customerId: customer.customerId,
          errorCount: customer.errorCount,
          status: 'active',
          lastSeen: new Date().toISOString()
        })),
        pagination: {
          currentPage: 1,
          totalPages: 1,
          totalRecords: customers.length,
          recordsPerPage: customers.length
        }
      };
    } catch (error) {
      console.error('Error fetching customers:', error);
      return {
        data: [],
        pagination: {
          currentPage: 1,
          totalPages: 1,
          totalRecords: 0,
          recordsPerPage: 10
        }
      };
    }
  },

  getCustomerById: async (customerId) => {
    try {
      const customerErrors = await errorsAPI.getCustomerErrors(customerId);
      return {
        id: customerId,
        customerId: customerId,
        errorCount: customerErrors.totalErrors,
        errors: customerErrors.errors,
        status: 'active',
        lastSeen: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error fetching customer by ID:', error);
      throw error;
    }
  },

  // Alias for compatibility
  getCustomerErrors: async (customerId) => {
    return errorsAPI.getCustomerErrors(customerId);
  }
};

export const downloadAPI = {
  downloadErrors: async (params) => {
    const data = JSON.stringify(params, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    return blob;
  },

  downloadCustomers: async (params) => {
    const customers = await customersAPI.getCustomers(params);
    const data = JSON.stringify(customers.data, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    return blob;
  }
};

export const handleFileDownload = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
  return { success: true, filename };
};

// Test function
export const testApiConnection = async () => {
  try {
    const response = await fetch('http://localhost:8000/');
    const data = await response.json();
    console.log('✅ API Connection Test:', data);
    return data;
  } catch (error) {
    console.error('❌ API Connection Failed:', error);
    throw error;
  }
};
