
We have identified at least three problems where leveraging the potential of Large Language Models (LLMs) could help address these issues effectively.

## 1. Automatically assign relevant ontological terms to Dandiset metadata
LLMs are very promising tools to automate the extraction of well-annotated references to relevant ontological terms (species, techniques, equipment, sensory modality, task type, etc.) from raw unstructured text data such as abstracts, methods sections, or entire papers.

In recent developments, OpenAI trained and [made available](https://openai.com/blog/function-calling-and-other-api-updates) models specialized in structured data (JSON) extraction, which could be readily applied to this end.

## 2. Identify Dandisets relevant to a scientific question
Given a scientific question, LLMs can also be helpful to search for potentially useful Dandisets. For this we would produce vector embeddings for each Dandiset. Such vectors will hold semantic values extracted from DANDI set abstracts and asset summaries, on top of which semantic search could be performed. In a first, naive approach, we will rank the results based on semantic similarity and return the first options as they come. In a more advanced approach, we plan to run a prompt consisting of the original question plus top results through a LLM asking it to further enquire and explain in which ways the best results would be relevant to the posed question.

[search_dandisets](search_dandisets.ipynb)

## 3. Auto-generate analysis code
With a scientific question defined and useful DANDI sets identified, LLMs could further produce code scripts for advanced data processing, analysis and visualization.


## Relevant tools and services
[OpenAI](https://openai.com/) and [Cohere](https://cohere.com/) are the LLMs SaaS providers we would consider using for completion, extraction and embedding tasks. These models are publicly available through APIs.

[Qdrant](https://qdrant.tech/) and [Weaviate](https://weaviate.io/) are two options of vector search engines, both open source and with SaaS offerings as well.

[LangChain](https://github.com/hwchase17/langchain) is a Python package useful for creating applications using LLMs.


# Run Qdrant

```bash
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant:latest
```

Navigate to `http://localhost:6333/dashboard` to access the service Dashboard.
