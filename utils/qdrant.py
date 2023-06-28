from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.models import UpdateStatus
from .openai import get_embedding_simple


def create_collection(collection_name: str="dandi_collection", vector_size: int=1536):
    client = QdrantClient("localhost", port=6333)
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.DOT),
    )   


def add_points_to_collection(embeddings_objects: list, collection_name: str="dandi_collection"):
    client = QdrantClient("localhost", port=6333)
    points_list = [PointStruct(**i) for i in embeddings_objects]
    upsert_result = client.upsert(
        collection_name=collection_name,
        wait=True,
        points=points_list,
    )
    assert upsert_result.status == UpdateStatus.COMPLETED
    print(f"{len(points_list)} points added to collection {collection_name}")


def query_similar_items(query: str, collection_name: str="dandi_collection", top_k: int=10):
    client = QdrantClient("localhost", port=6333)
    query_vector = get_embedding_simple(query)
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
    )
    return search_result


def query_all_keywords(keywords: list):
    results = dict()
    for keyword in keywords:
        search_results = query_similar_items(query=keyword)
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
