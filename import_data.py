from pymongo import MongoClient
import json
import os
from datetime import datetime
import sys

try:
    # MongoDB Atlas connection string
    MONGODB_URI = "mongodb+srv://pabitragiri05admin:pabitragiri05@obarly.thgwlny.mongodb.net/?retryWrites=true&w=majority&appName=obarly"

    # Connect to MongoDB Atlas
    print('Connecting to MongoDB Atlas...')
    client = MongoClient(MONGODB_URI)
    db = client['Inventory']

    # Test connection
    client.admin.command('ping')
    print('Successfully connected to MongoDB Atlas')

    # Import collections
    collections = ['Products', 'Users', 'Orders']  # Added Orders collection

    for collection_name in collections:
        try:
            # Find the most recent export file
            files = [f for f in os.listdir('.') if f.startswith(f'{collection_name.lower()}_export_')]
            if not files:
                print(f'No export file found for {collection_name}')
                continue
            
            latest_file = max(files)
            print(f'Importing from {latest_file}')
            
            # Read and import data
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collection = db[collection_name]
            if data:
                # Clear existing data
                collection.delete_many({})
                print(f'Cleared existing data from {collection_name}')
                
                # Insert new data
                result = collection.insert_many(data)
                print(f'Successfully imported {len(result.inserted_ids)} documents to {collection_name}')
            else:
                print(f'No data to import for {collection_name}')

        except Exception as e:
            print(f'Error importing {collection_name}: {str(e)}')
            continue

    print('Import completed successfully!')

except Exception as e:
    print(f'Fatal error: {str(e)}')
    sys.exit(1)

finally:
    if 'client' in locals():
        client.close()
        print('MongoDB connection closed') 