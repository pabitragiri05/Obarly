from pymongo import MongoClient
import json
import os
from datetime import datetime

# MongoDB Atlas connection string
MONGODB_URI = "mongodb+srv://pabitragiri05admin:pabitragiri05@obarly.thgwlny.mongodb.net/?retryWrites=true&w=majority&appName=obarly"

# Connect to MongoDB Atlas
client = MongoClient(MONGODB_URI)
db = client['Inventory']

# Import collections
collections = ['Products', 'Users']

for collection_name in collections:
    # Find the most recent export file
    files = [f for f in os.listdir('.') if f.startswith(f'{collection_name.lower()}_export_')]
    if not files:
        print(f'No export file found for {collection_name}')
        continue
    
    latest_file = max(files)
    print(f'Importing from {latest_file}')
    
    # Read and import data
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    collection = db[collection_name]
    if data:
        # Clear existing data
        collection.delete_many({})
        # Insert new data
        try:
            result = collection.insert_many(data)
            print(f'Successfully imported {len(result.inserted_ids)} documents to {collection_name}')
        except Exception as e:
            print(f'Error importing to {collection_name}: {str(e)}')
    else:
        print(f'No data to import for {collection_name}')

print('Import completed!') 