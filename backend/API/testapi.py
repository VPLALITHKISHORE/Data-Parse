# test_connection.py
from pymongo import MongoClient
import requests

def test_mongodb():
    """Test MongoDB connection"""
    try:
        client = MongoClient('mongodb://localhost:27017')
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test each database
        databases = ['CREDIT_DATA', 'CSV', 'UPI_EXCEL']
        for db_name in databases:
            try:
                db = client[db_name]
                collection = db['error_json']
                count = collection.count_documents({})
                print(f"✅ {db_name}: {count} documents")
                
                # Show sample document
                sample = collection.find_one()
                if sample:
                    print(f"   Sample fields: {list(sample.keys())[:5]}...")
                
            except Exception as e:
                print(f"❌ {db_name}: {e}")
                
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

def test_api():
    """Test API endpoints"""
    try:
        # Test root endpoint
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ API root endpoint working!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ API root endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("Make sure to start the API server first: python app.py")

if __name__ == "__main__":
    print("🔍 Testing connections...")
    test_mongodb()
    print("\n" + "="*50 + "\n")
    test_api()
