import requests
from pathlib import Path
import os

import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from qdrant_client import QdrantClient


def extract_behavior_descriptions_from_prompt(prompt):

    model = "gpt-3.5-turbo"
    openai.api_key = os.getenv("OPENAI_API_KEY")

    system_content = "You are a neuroscience researcher and you are interested in figuring out behavior from the methods section"

    completion = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    response = completion.choices[0].message.content
    
    return response


def ground_metadata_in_ontologies(term_list: list) -> dict:
    
    collection_name = "neuro_behavior_ontology"
    embedding_model = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
    url = "https://c1490259-dfe4-4a49-8712-24f690d450f6.us-east-1-0.aws.cloud.qdrant.io:6333"
    api_key =os.environ["QDRANT_API_KEY"]
    client = QdrantClient(
    url=url,
    api_key=api_key,
    )
    
    id_to_url = lambda x: f"http://purl.obolibrary.org/obo/{x.replace(':', '_')}"

    top = 1  # The number of similar vectors you want to retrieve from the database

    term_embedding_list = embedding_model.embed_documents(term_list)
    term_to_embeddings = {term_list[i]: term_embedding_list[i] for i in range(len(term_list))}

    term_to_identifiers_dict = {}
    for term, embedding in term_to_embeddings.items():
        
        query_vector = embedding
        search_results = client.search(collection_name=collection_name, query_vector=query_vector, limit=top, with_payload=True, with_vectors=False)
        
        ids = [result.payload[f"{collection_name}_id"] for result in search_results]
        names = [result.payload["name"] for result in search_results]
        score = [result.score for result in search_results]
        urls = [id_to_url(id) for id in ids]
        
        if ids:
            id = ids[0]
            term_to_identifiers_dict[id] = dict(name=names[0], score=score[0], url=urls[0], context=term)

    # Order the term_to_identifiers_dict by score
    term_to_identifiers_dict = dict(sorted(term_to_identifiers_dict.items(), key=lambda item: item[1]["score"], reverse=True))
    
    return term_to_identifiers_dict