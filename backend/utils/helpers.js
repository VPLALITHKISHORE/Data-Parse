// utils/helpers.js
export const dateUtils = {
  formatDateTime: (dateString) => {
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
  },
  
  formatDate: (date, format) => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  },

  getRelativeTime: (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffHours < 1) return 'Just now';
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return dateUtils.formatDateTime(dateString);
    } catch {
      return 'Unknown';
    }
  }
};

export const numberUtils = {
  formatNumber: (num) => {
    if (num == null || isNaN(num)) return '0';
    return new Intl.NumberFormat().format(num);
  },

  formatLarge: (num) => {
    if (num == null || isNaN(num)) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  }
};

export const colorUtils = {
  getErrorTypeColor: (errorType) => {
    const colors = {
      'CREDIT_VALIDATION': '#dc3545',
      'CSV_PROCESSING': '#fd7e14', 
      'EXCEL_VALIDATION': '#6f42c1',
      'MISSING_FIELD': '#dc3545',
      'INVALID_FORMAT': '#fd7e14',
      'VALIDATION_ERROR': '#28a745',
      'PARSING_ERROR': '#e83e8c',
      'DATA_TYPE_ERROR': '#17a2b8',
      'BUSINESS_RULE_ERROR': '#6610f2'
    };
    return colors[errorType] || '#6c757d';
  },

  getDatabaseColor: (database) => {
    const colors = {
      'CREDIT_DATA': '#007bff',
      'CSV': '#28a745',
      'UPI_EXCEL': '#6f42c1'
    };
    return colors[database] || '#6c757d';
  }
};
