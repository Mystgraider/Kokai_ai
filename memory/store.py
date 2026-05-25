import uuid
import chromadb
import json

client = chromadb.PersistentClient(path="./memory_db")
existing_collections = [c.name for c in client.list_collections()]

if "kokai_semantic_memory" not in existing_collections:
    collection = client.create_collection("kokai_semantic_memory")
else:
    collection = client.get_collection("kokai_semantic_memory")

if "kokai_graph_linkage" not in existing_collections:
    graph_metadata_collection = client.create_collection("kokai_graph_linkage")
else:
    graph_metadata_collection = client.get_collection("kokai_graph_linkage")

def save_memory(text: str, tags: list = None):
    doc_id = str(uuid.uuid4())
    if collection.count() >= 500:
        oldest = collection.get(limit=1)
        if oldest['ids']:
            collection.delete(ids=[oldest['ids']])
            graph_metadata_collection.delete(ids=[oldest['ids']])

    collection.add(documents=[text], ids=[doc_id], metadatas=[{"tags": json.dumps(tags or [])}])
    extracted_entities = [w.strip("#,.-_").lower() for w in text.split() if len(w) > 4][:5]
    graph_metadata_collection.add(documents=[" ".join(extracted_entities)], ids=[doc_id])

def deep_retrieve_memory(query: str) -> str:
    if collection.count() == 0:
        return ""
    semantic_results = collection.query(query_texts=[query], n_results=2)
    context_chunks = []
    if semantic_results and semantic_results['documents'] and semantic_results['documents'][0]:
        context_chunks.extend(semantic_results['documents'][0])
        matched_id = semantic_results['ids'][0]
        graph_data = graph_metadata_collection.get(ids=matched_id)
        if graph_data and graph_data['documents']:
            entities = graph_data['documents']
            extended_results = collection.query(query_texts=entities, n_results=2)
            if extended_results and extended_results['documents'] and extended_results['documents'][0]:
                for doc in extended_results['documents'][0]:
                    if doc not in context_chunks:
                        context_chunks.append(doc)
    return "\n---\n".join(context_chunks)
