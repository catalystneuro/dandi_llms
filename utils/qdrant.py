from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.models import UpdateStatus
from concurrent.futures import ThreadPoolExecutor, wait
from .openai import get_embedding_simple


def create_collection(collection_name: str="dandi_collection", vector_size: int=1536):
    client = QdrantClient("localhost", port=6333)
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.DOT),
    )   


def add_points_to_collection(embeddings_objects: list, collection_name: str="dandi_collection"):
    def upsert_batch(points_batch):
        client = QdrantClient("localhost", port=6333)
        points_list = [PointStruct(**i) for i in points_batch]
        upsert_result = client.upsert(
            collection_name=collection_name,
            wait=True,
            points=points_list,
        )
        assert upsert_result.status == UpdateStatus.COMPLETED

    with ThreadPoolExecutor() as executor:
        batch_size = 100
        batches = [embeddings_objects[i:i + batch_size] for i in range(0, len(embeddings_objects), batch_size)]
        futures = [executor.submit(upsert_batch, batch) for batch in batches]
        
        # Wait for all futures to complete
        wait(futures)
    print(f"All points added to collection {collection_name}")


def get_collection_info(collection_name: str="dandi_collection"):
    client = QdrantClient("localhost", port=6333)
    return client.get_collection(collection_name=collection_name).dict()


def query_similar_items(query: str, collection_name: str="dandi_collection", top_k: int=10):
    client = QdrantClient("localhost", port=6333)
    query_vector = get_embedding_simple(query)
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
    )
    return search_result


def query_from_user_input(text: str, collection_name: str="dandi_collection", top_k: int=10):
    search_results = query_similar_items(query=text, collection_name=collection_name, top_k=top_k)
    results = dict()
    for sr in search_results:
        dandiset_id = sr.payload["dandiset_id"]
        score = sr.score
        if dandiset_id not in results:
            results[dandiset_id] = score
        else:
            results[dandiset_id] += score
    #     print(f'{sr.payload["dandiset_id"]} \n{sr.payload["text_content"]} \n{sr.score} \n')
    return get_top_scores(results)


def query_all_keywords(keywords: list, collection_name: str="dandi_collection", top_k: int=10):
    results = dict()
    for keyword in keywords:
        search_results = query_similar_items(query=keyword, collection_name=collection_name, top_k=top_k)
        for sr in search_results:
            dandiset_id = sr.payload["dandiset_id"]
            score = sr.score
            if dandiset_id not in results:
                results[dandiset_id] = score
            else:
                results[dandiset_id] += score
    return get_top_scores(results)


def get_top_scores(dictionary: dict, N: int=None):
    sorted_items = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
    if not N:
        N = len(dictionary)
    top_scores = sorted_items[:min(N, len(dictionary))]
    return top_scores
