from chromadb.config import Settings

import chromadb

chroma_client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    settings=Settings(allow_reset=True, anonymized_telemetry=False),
)

collection = chroma_client.create_collection(name="support_cases")

# Add some example support cases
support_cases = [
    {
        "case": "Customer reported frequent disconnects between their smart thermostats and the mobile app.",
        "resolution": "Identified outdated firmware on devices; guided customer through update process.",
        "category": "connectivity",
        "date": "2024-03-17",
    },
    {
        "case": "User unable to add new IoT sensors to the monitoring dashboard.",
        "resolution": "Discovered device registration limit reached; increased limit and refreshed dashboard.",
        "category": "device-management",
        "date": "2024-03-18",
    },
    {
        "case": "Customer's dashboard showed delayed data from environmental sensors.",
        "resolution": "Found network latency issues; optimized data batch processing settings.",
        "category": "performance",
        "date": "2024-03-21",
    },
    {
        "case": "User reported error 'Asset error: configuring device' when onboarding a new device.",
        "resolution": "Advised user to wait and retry; device successfully configured after a short delay.",
        "category": "onboarding",
        "date": "2024-03-22",
    },
    {
        "case": "Customer could not visualize real-time data on their dashboard.",
        "resolution": "Enabled real-time data streaming and refreshed visualization widgets.",
        "category": "dashboard",
        "date": "2024-03-23",
    },
    {
        "case": "User received 'identifier undefined' error when deploying a data logic script.",
        "resolution": "Corrected asset type name in the script and redeployed successfully.",
        "category": "scripting",
        "date": "2024-03-24",
    },
    {
        "case": "Customer's IoT device failed to connect after moving to a private LTE network.",
        "resolution": "Adjusted DHCP configuration to set correct MTU value for LTE connectivity.",
        "category": "network",
        "date": "2024-03-25",
    },
    {
        "case": "User unable to access historical data for their devices.",
        "resolution": "Restored archived data and updated data retention policy for the account.",
        "category": "data-management",
        "date": "2024-03-26",
    },
    {
        "case": "Customer reported incorrect device status displayed after firmware update.",
        "resolution": "Rolled back to previous firmware version and scheduled further testing.",
        "category": "firmware",
        "date": "2024-03-27",
    },
    {
        "case": "User could not map new asset types to the EI agent in the dashboard.",
        "resolution": "Provided step-by-step mapping instructions and verified successful configuration.",
        "category": "configuration",
        "date": "2024-03-28",
    },
]

# Add documents to collection
collection.add(
    documents=[case["case"] + "\n" + case["resolution"] for case in support_cases],
    metadatas=[
        {"category": case["category"], "date": case["date"]} for case in support_cases
    ],
    ids=[f"case_{i}" for i in range(len(support_cases))],
)
# results = collection.query(
#     query_texts=[
#         """
#         I'm having trouble helping a customer with IoT device connectivity.
# Can you check our support knowledge base for similar cases and suggest a solution?"
#     """
#     ],
#     n_results=2,  # how many results to return
# )
# print(results)
