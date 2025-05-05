from pymongo import MongoClient
import json
from datetime import datetime
from bson import ObjectId

# Connect to local MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Inventory']

# Export collections
collections = ['Products', 'Users']

def json_serializer(obj):
    if isinstance(obj, (datetime, ObjectId)):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

for collection_name in collections:
    collection = db[collection_name]
    data = list(collection.find())
    
    # Save to file
    filename = f'{collection_name.lower()}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=json_serializer)
    
    print(f'Exported {len(data)} documents from {collection_name} to {filename}')

print('Export completed!') 