import chromadb
from datetime import datetime

# Connect to Chroma Cloud
client = chromadb.HttpClient(
    ssl=True,
    host='api.trychroma.com',
    tenant='your-tenant-id',
    database='support-kb',
    headers={
        'x-chroma-token': 'YOUR_API_KEY'
    }
)

# Create a collection for support cases
collection = client.create_collection("support_cases")

# Add some example support cases
support_cases = [
    {
        "case": "Customer reported issues connecting their IoT devices to the dashboard.",
        "resolution": "Guided customer through firewall configuration and port forwarding setup.",
        "category": "connectivity",
        "date": "2024-03-15"
    },
    {
        "case": "User couldn't access admin features after recent update.",
        "resolution": "Discovered role permissions weren't migrated correctly. Applied fix and documented process.",
        "category": "permissions",
        "date": "2024-03-16"
    }
]

# Add documents to collection
collection.add(
    documents=[case["case"] + "\n" + case["resolution"] for case in support_cases],
    metadatas=[{
        "category": case["category"],
        "date": case["date"]
    } for case in support_cases],
    ids=[f"case_{i}" for i in range(len(support_cases))]
)
