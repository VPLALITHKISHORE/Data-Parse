# app.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
from typing import Optional
import json
from bson import ObjectId

app = FastAPI(title="Error Logs API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = 'mongodb://localhost:27017'

# Database names
DATABASES = {
    'CREDIT_DATA': 'CREDIT_DATA',
    'CSV': 'CSV', 
    'UPI_EXCEL': 'UPI_EXCEL'
}

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URL)
    # Test connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    client = None

def normalize_error_data(doc, source_db):
    """Normalize error data from different database structures"""
    
    # Convert ObjectId to string
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    
    base_data = {
        '_id': doc.get('_id'),
        'database_source': source_db,
        'status': 'UNRESOLVED',
        'processedBy': 'System'
    }
    
    if source_db == 'CREDIT_DATA':
        return {
            **base_data,
            'errorType': 'CREDIT_VALIDATION',
            'errorMessage': ', '.join(doc.get('Errors', [])) if doc.get('Errors') else 'Unknown credit error',
            'sourceFormat': 'XML',
            'sourceFile': 'credit_data.xml',
            'customerId': doc.get('CUST_ID', 'N/A'),
            'originalCustomerId': doc.get('Original_CUST_ID'),
            'recordId': doc.get('RecordId'),
            'createdAt': doc.get('timestamp', datetime.now().isoformat()),
            'errorDetails': doc.get('Errors', []),
            'rawData': doc
        }
    
    elif source_db == 'CSV':
        return {
            **base_data,
            'errorType': 'CSV_PROCESSING',
            'errorMessage': ', '.join(doc.get('_errors', [])) if doc.get('_errors') else 'CSV processing error',
            'sourceFormat': 'CSV',
            'sourceFile': 'transaction_data.csv',
            'customerId': doc.get('customer_id', 'N/A'),
            'transactionId': doc.get('transaction_id'),
            'lineNumber': doc.get('_row_number'),
            'createdAt': doc.get('_processed_at', datetime.now().isoformat()),
            'errorDetails': doc.get('_errors', []),
            'errorCount': doc.get('_error_count', 0),
            'rawData': doc
        }
    
    elif source_db == 'UPI_EXCEL':
        return {
            **base_data,
            'errorType': 'EXCEL_VALIDATION',
            'errorMessage': doc.get('_error_reason', 'Excel validation failed'),
            'sourceFormat': 'Excel',
            'sourceFile': 'upi_transactions.xlsx',
            'customerId': doc.get('Customer id', 'N/A'),
            'transactionId': doc.get('transaction id'),
            'createdAt': doc.get('_processed_at', datetime.now().isoformat()),
            'errorDetails': [doc.get('_error_reason', 'Validation failed')],
            'rawData': doc
        }
    
    return base_data

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Error Logs API",
        "version": "1.0.0", 
        "databases": list(DATABASES.keys()),
        "status": "running",
        "mongodb_connected": client is not None
    }

@app.get("/api/errors")
async def get_errors(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    errorType: Optional[str] = Query(None, description="Filter by error type"),
    sourceFormat: Optional[str] = Query(None, description="Filter by source format"),
    customerId: Optional[str] = Query(None, description="Filter by customer ID"),
    database: Optional[str] = Query(None, description="Filter by database")
):
    """Get paginated error logs from all databases"""
    
    if not client:
        raise HTTPException(status_code=500, detail="MongoDB connection failed")
    
    try:
        all_errors = []
        
        # Determine which databases to query
        databases_to_query = [database] if database and database in DATABASES else DATABASES.keys()
        
        # Fetch from each database
        for db_name in databases_to_query:
            try:
                db = client[DATABASES[db_name]]
                collection = db['error_json']
                
                # Basic query - get all documents first
                cursor = collection.find({}).limit(1000)  # Limit for performance
                documents = list(cursor)
                
                # Normalize data
                for doc in documents:
                    normalized_error = normalize_error_data(doc, db_name)
                    all_errors.append(normalized_error)
                
                print(f"✅ Fetched {len(documents)} errors from {db_name}")
                
            except Exception as db_error:
                print(f"❌ Error fetching from {db_name}: {db_error}")
                continue
        
        # Apply filters after normalization
        if search:
            all_errors = [e for e in all_errors if 
                         search.lower() in e.get('errorMessage', '').lower() or
                         search.lower() in str(e.get('customerId', '')).lower()]
        
        if errorType:
            all_errors = [e for e in all_errors if e.get('errorType') == errorType]
        
        if sourceFormat:
            all_errors = [e for e in all_errors if e.get('sourceFormat') == sourceFormat]
        
        if customerId:
            all_errors = [e for e in all_errors if 
                         customerId.lower() in str(e.get('customerId', '')).lower()]
        
        # Sort by date (newest first)
        all_errors.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        # Apply pagination
        total_records = len(all_errors)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_errors = all_errors[start_idx:end_idx]
        
        total_pages = (total_records + limit - 1) // limit
        
        return {
            "data": paginated_errors,
            "pagination": {
                "currentPage": page,
                "totalPages": total_pages,
                "totalRecords": total_records,
                "recordsPerPage": limit,
                "hasPrevPage": page > 1,
                "hasNextPage": page < total_pages
            },
            "summary": {
                "databases_queried": len(databases_to_query),
                "total_errors_found": total_records
            }
        }
        
    except Exception as e:
        print(f"❌ Error in get_errors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch errors: {str(e)}")

@app.get("/api/errors/stats")
async def get_error_stats():
    """Get comprehensive error statistics"""
    
    if not client:
        raise HTTPException(status_code=500, detail="MongoDB connection failed")
    
    try:
        stats = {
            "totalErrors": 0,
            "errorsByType": {},
            "errorsBySource": {},
            "errorsByDatabase": {},
            "errorsByCustomer": {},
            "topCustomersWithErrors": []
        }
        
        all_errors = []
        
        # Fetch from each database
        for db_name in DATABASES.keys():
            try:
                db = client[DATABASES[db_name]]
                collection = db['error_json']
                
                # Get count
                error_count = collection.count_documents({})
                stats["errorsByDatabase"][db_name] = error_count
                
                # Fetch sample documents for stats
                cursor = collection.find({}).limit(500)  # Limit for performance
                documents = list(cursor)
                
                for doc in documents:
                    normalized_error = normalize_error_data(doc, db_name)
                    all_errors.append(normalized_error)
                
                print(f"✅ Processed {len(documents)} errors from {db_name}")
                
            except Exception as db_error:
                stats["errorsByDatabase"][db_name] = 0
                print(f"❌ Error processing {db_name}: {db_error}")
                continue
        
        # Calculate stats
        stats["totalErrors"] = len(all_errors)
        
        customer_error_count = {}
        
        for error in all_errors:
            # Error type stats
            error_type = error.get('errorType', 'Unknown')
            stats["errorsByType"][error_type] = stats["errorsByType"].get(error_type, 0) + 1
            
            # Source format stats
            source_format = error.get('sourceFormat', 'Unknown')
            stats["errorsBySource"][source_format] = stats["errorsBySource"].get(source_format, 0) + 1
            
            # Customer stats
            customer_id = error.get('customerId')
            if customer_id and customer_id != 'N/A':
                customer_error_count[customer_id] = customer_error_count.get(customer_id, 0) + 1
        
        # Top customers with errors
        stats["topCustomersWithErrors"] = [
            {"customerId": customer_id, "errorCount": count}
            for customer_id, count in sorted(customer_error_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return stats
        
    except Exception as e:
        print(f"❌ Error in get_error_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")

@app.get("/api/errors/customer/{customer_id}")
async def get_customer_errors(customer_id: str):
    """Get all errors for a specific customer"""
    
    if not client:
        raise HTTPException(status_code=500, detail="MongoDB connection failed")
    
    try:
        customer_errors = []
        
        # Search in each database
        for db_name in DATABASES.keys():
            try:
                db = client[DATABASES[db_name]]
                collection = db['error_json']
                
                # Build customer-specific query for each database
                query = {}
                if db_name == 'CREDIT_DATA':
                    query = {'CUST_ID': {'$regex': customer_id, '$options': 'i'}}
                elif db_name == 'CSV':
                    query = {'customer_id': {'$regex': customer_id, '$options': 'i'}}
                elif db_name == 'UPI_EXCEL':
                    query = {'Customer id': {'$regex': customer_id, '$options': 'i'}}
                
                # Fetch matching documents
                cursor = collection.find(query)
                documents = list(cursor)
                
                # Normalize data
                for doc in documents:
                    normalized_error = normalize_error_data(doc, db_name)
                    customer_errors.append(normalized_error)
                
                print(f"✅ Found {len(documents)} errors for customer {customer_id} in {db_name}")
                
            except Exception as db_error:
                print(f"❌ Error searching {db_name} for customer {customer_id}: {db_error}")
                continue
        
        # Sort by date (newest first)
        customer_errors.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        return {
            "customerId": customer_id,
            "totalErrors": len(customer_errors),
            "errors": customer_errors,
            "databases_searched": list(DATABASES.keys())
        }
        
    except Exception as e:
        print(f"❌ Error in get_customer_errors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch customer errors: {str(e)}")

@app.get("/api/databases/status")
async def get_database_status():
    """Check database connection status"""
    
    status = {
        "mongodb_connected": False,
        "databases": {},
        "total_collections": 0,
        "total_errors": 0
    }
    
    try:
        if client:
            # Test MongoDB connection
            client.admin.command('ping')
            status["mongodb_connected"] = True
            
            # Check each database
            for db_name, db_real_name in DATABASES.items():
                try:
                    db = client[db_real_name]
                    collection = db['error_json']
                    
                    # Get collection stats
                    error_count = collection.count_documents({})
                    
                    status["databases"][db_name] = {
                        "status": "Connected",
                        "collection_exists": True,
                        "error_count": error_count,
                        "last_checked": datetime.now().isoformat()
                    }
                    
                    status["total_collections"] += 1
                    status["total_errors"] += error_count
                    
                except Exception as db_error:
                    status["databases"][db_name] = {
                        "status": f"Error: {str(db_error)}",
                        "collection_exists": False,
                        "error_count": 0,
                        "last_checked": datetime.now().isoformat()
                    }
        else:
            status["connection_error"] = "MongoDB client not initialized"
        
    except Exception as e:
        status["mongodb_connected"] = False
        status["connection_error"] = str(e)
    
    return status

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Error Logs API...")
    print(f"📊 Databases to monitor: {list(DATABASES.keys())}")
    # Remove reload=True to fix the warning
    uvicorn.run(app, host="0.0.0.0", port=8000)
