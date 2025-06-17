# MCP Server for ChromaDB

The Chroma MCP interacts with a ChromaDB instance running locally and listning on port 8000
`docker run -v -d ./chroma-data:/data --network chromadb -p 8000:8000 chromadb/chroma`

The config for starting the Chroma MCP Server as a Docker container:

```json
{
  "mcpServers": {
    "chrmoaDB": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--mount",
        "type=bind,src=/home/santosh/mcp-servers/chromaDB/.env,dst=/app/chroma_env",
        "--network",
        "chromadb",
        "santoshkal/chromamcp:main"
      ]
    }
  }
}
```

Chroma mcp server requires the connection parameters to be passed in as `.env` file. The default
name of the env file used inside the MCP Sever is `.chroma_env`. The `.env` file is mounted to the container as `.chroma_env`
in it's WORKDIR.
The .env used in the current implementation:

```sh

CHROMA_DOTENV_PATH="/app/.chroma_env" # Path to the .env within the container # Optional
CHROMA_CLIENT_TYPE="http" # ChromaDB Client type # Required
CHROMA_HOST="chromadb" # Docker network on which the ChromaDB instance is running #Required
CHROMA_PORT=8000 # Port of the ChromaDB instance listnining on # Required
CHROMA_SSL="false" # SSL mode if using HTTP # Required
```

## Available Tools

- `chroma_list_collections` - List all collections with pagination support

  - limit: Optional maximum number of collections to return
  - offset: Optional number of collections to skip before returning results

- `chroma_create_collection` - Create a new collection with optional HNSW configuration

  - collection_name: Name of the collection to create
  - space: Distance function used in HNSW index. Options: 'l2', 'ip', 'cosine'
  - ef_construction: Size of the dynamic candidate list for constructing the HNSW graph
  - ef_search: Size of the dynamic candidate list for searching the HNSW graph
  - max_neighbors: Maximum number of neighbors to consider during HNSW graph construction
  - num_threads: Number of threads to use during HNSW construction
  - batch_size: Number of elements to batch together during index construction
  - sync_threshold: Number of elements to process before syncing index to disk
  - resize_factor: Factor to resize the index by when it's full
  - embedding_function_name: Name of the embedding function to use. Options: 'default', 'cohere', 'openai', 'jina', 'voyageai', 'ollama', 'roboflow'
  - metadata: Optional metadata dict to add to the collection

- `chroma_peek_collection` - View a sample of documents in a collection

  - collection_name: Name of the collection to peek into
  - limit: Number of documents to peek at

- `chroma_get_collection_info` - Get detailed information about a collection

  - collection_name: Name of the collection to get info about

- `chroma_get_collection_count` - Get the number of documents in a collection

  - collection_name: Name of the collection to count

- `chroma_modify_collection` - Update a collection's name or metadata

  - collection_name: Name of the collection to modify
  - new_name: Optional new name for the collection
  - new_metadata: Optional new metadata for the collection
  - ef_search: Size of the dynamic candidate list for searching the HNSW graph
  - num_threads: Number of threads to use during HNSW construction
  - batch_size: Number of elements to batch together during index construction
  - sync_threshold: Number of elements to process before syncing index to disk
  - resize_factor: Factor to resize the index by when it's full

- `chroma_delete_collection` - Delete a collection

  - collection_name: Name of the collection to delete

- `chroma_add_documents` - Add documents with optional metadata and custom IDs

  - collection_name: Name of the collection to add documents to
  - documents: List of text documents to add
  - metadatas: Optional list of metadata dictionaries for each document
  - ids: Optional list of IDs for the documents

- `chroma_query_documents` - Query documents using semantic search with advanced filtering

  - collection_name: Name of the collection to query
  - query_texts: List of query texts to search for
  - n_results: Number of results to return per query
  - where: Optional metadata filters using Chroma's query operators
    Examples: - Simple equality: {"metadata_field": "value"} - Comparison: {"metadata_field": {"$gt": 5}}
          - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]} - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
    where_document: Optional document content filters
  - include: List of what to include in response. By default, this will include documents, metadatas, and distances.

- `chroma_get_documents` - Retrieve documents by IDs or filters with pagination

  - collection_name: Name of the collection to get documents from
  - ids: Optional list of document IDs to retrieve
  - where: Optional metadata filters using Chroma's query operators
    Examples: - Simple equality: {"metadata_field": "value"} - Comparison: {"metadata_field": {"$gt": 5}}
          - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]} - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
  - where_document: Optional document content filters
  - include: List of what to include in response. By default, this will include documents, and metadatas.
  - limit: Optional maximum number of documents to return
  - offset: Optional number of documents to skip before returning results
  - Returns:
    Dictionary containing the matching documents, their IDs, and requested includes

- `chroma_update_documents` - Update existing documents' content, metadata, or embeddings

  - collection_name: Name of the collection to update documents in
  - ids: List of document IDs to update (required)
  - embeddings: Optional list of new embeddings for the documents.
    Must match length of ids if provided.
  - metadatas: Optional list of new metadata dictionaries for the documents.
    Must match length of ids if provided.
  - documents: Optional list of new text documents.
    Must match length of ids if provided.

  - Returns:
    A confirmation message indicating the number of documents updated.

  - Raises:
    ValueError: If 'ids' is empty or if none of 'embeddings', 'metadatas',
    or 'documents' are provided, or if the length of provided
    update lists does not match the length of 'ids'.
    Exception: If the collection does not exist or if the update operation fails.

- `chroma_delete_documents` - Delete specific documents from a collection

  - collection_name: Name of the collection to delete documents from
  - ids: List of document IDs to delete

  - Returns:
    A confirmation message indicating the number of documents deleted.

  - Raises:
    ValueError: If 'ids' is empty
    Exception: If the collection does not exist or if the delete operation fails.
