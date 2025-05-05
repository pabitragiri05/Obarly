from pymongo import MongoClient
import json
from datetime import datetime
from bson import ObjectId
import sys

try:
    # Connect to local MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Inventory']

    # Export collections
    collections = ['Products', 'Users', 'Orders']  # Added Orders collection

    def json_serializer(obj):
        if isinstance(obj, (datetime, ObjectId)):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    for collection_name in collections:
        try:
            collection = db[collection_name]
            data = list(collection.find())
            
            if not data:
                print(f"Warning: No data found in {collection_name} collection")
                continue
            
            # Save to file
            filename = f'{collection_name.lower()}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=json_serializer, ensure_ascii=False)
            
            print(f'Successfully exported {len(data)} documents from {collection_name} to {filename}')

        except Exception as e:
            print(f'Error exporting {collection_name}: {str(e)}')
            continue

    print('Export completed!')

except Exception as e:
    print(f'Fatal error: {str(e)}')
    sys.exit(1)

finally:
    if 'client' in locals():
        client.close()
        print('MongoDB connection closed') 