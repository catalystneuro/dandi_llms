from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain
import uuid
import openai
import os
from .dandi import get_dandiset_metadata, collect_relevant_metadata


def get_embedding_simple(text: str) -> list:
    """Get embedding for a single text"""
    embeddings_client = OpenAIEmbeddings()
    embeddings = embeddings_client.embed_query(text)
    return embeddings


def get_embeddings(metadata_list: list, max_num_sets: int = None) -> list:
    """Get embeddings for all metadata fields, organizes them as list of objects similar to Qdrant points"""
    embeddings_client = OpenAIEmbeddings()
    all_qdrant_ponits = []
    if not max_num_sets:
        max_num_sets = len(metadata_list)
    for m in metadata_list[:max_num_sets]:
        print("Generating embeddings for DANDI set:", m["dandiset_id"])
        n_approaches = len(m["approaches"])
        n_measurement_techniques = len(m["measurement_techniques"])
        n_variables_measured = len(m["variables_measured"])
        n_species = len(m["species"])
        query_list = [
            m["title"],
            m["description"],
        ]
        query_list.extend(m["approaches"])
        query_list.extend(m["measurement_techniques"])
        query_list.extend(m["variables_measured"])
        query_list.extend(m["species"])
        embeddings = embeddings_client.embed_documents(
            texts=query_list,
            chunk_size=len(query_list),
        )
        # Prepare Qdrant Points
        qdrant_points = []
        qdrant_points.append(
            {
                "id": str(uuid.uuid4()),
                "vector": embeddings[0],
                "payload": {
                    "dandiset_id": m["dandiset_id"],
                    "field": "title",
                    "text_content": m["title"],
                }
            }
        )
        qdrant_points.append(
            {
                "id": str(uuid.uuid4()),
                "vector": embeddings[1],
                "payload": {
                    "dandiset_id": m["dandiset_id"],
                    "field": "description",
                    "text_content": m["description"],
                }
            }
        )
        for i in range(n_approaches):
            qdrant_points.append(
                {
                    "id": str(uuid.uuid4()),
                    "vector": embeddings[2+i],
                    "payload": {
                        "dandiset_id": m["dandiset_id"],
                        "field": "approaches",
                        "text_content": m["approaches"][i],
                    }
                }
            )
        for i in range(n_measurement_techniques):
            qdrant_points.append(
                {
                    "id": str(uuid.uuid4()),
                    "vector": embeddings[2+n_approaches+i],
                    "payload": {
                        "dandiset_id": m["dandiset_id"],
                        "field": "measurement_techniques",
                        "text_content": m["measurement_techniques"][i],
                    }
                }
            )
        for i in range(n_variables_measured):
            qdrant_points.append(
                {
                    "id": str(uuid.uuid4()),
                    "vector": embeddings[2+n_approaches+n_measurement_techniques+i],
                    "payload": {
                        "dandiset_id": m["dandiset_id"],
                        "field": "variables_measured",
                        "text_content": m["variables_measured"][i],
                    }
                }
            )
        for i in range(n_species):
            qdrant_points.append(
                {
                    "id": str(uuid.uuid4()),
                    "vector": embeddings[2+n_approaches+n_measurement_techniques+n_variables_measured+i],
                    "payload": {
                        "dandiset_id": m["dandiset_id"],
                        "field": "species",
                        "text_content": m["species"][i],
                    }
                }
            )
        all_qdrant_ponits.extend(qdrant_points)
    return all_qdrant_ponits


def keywords_extraction(user_question: str):
    llm = ChatOpenAI(
        # openai_api_key=self.secrets.OPENAI_API_KEY,
        model="gpt-3.5-turbo-0613",
        temperature=0
    )
    schema = {
        "properties": {
            "species": {
                "type": "string",
                "description": "Biological species taxonomies",
            },
            "approaches": {
                "type": "string",
                "description": "Experimental approaches in neuroscience, such as electrophysiology, calcium imaging, etc.",
            },
            "measurement_techniques": {
                "type": "string",
                "description": "Measurement techniques, such as patch clamp, two-photon imaging, spike sorting, etc.",
            },
            "variables_measured": {
                "type": "string",
                "description": "Variables measured, such as membrane potential, spike rate, position, etc.",
            },
            "anatomy": {
                "type": "string",
                "description": "Anatomical regions, such as hippocampus, cortex, etc.",
            },
            "disease": {
                "type": "string",
                "description": "Disease models, such as Alzheimer's, Parkinson's, etc.",
            },
            "cell_types": {
                "type": "string",
                "description": "Cell types, such as pyramidal, interneuron, etc.",
            },
            "drugs": {
                "type": "string",
                "description": "Drugs, such as ketamine, nitrous oxide, etc.",
            }
        },
        "required": [],
    }
    chain = create_extraction_chain(schema, llm)
    return chain.run(user_question)


def prepare_keywords_for_semantic_search(keywords_list: list) -> list:
    keywords_set = set()
    for obj in keywords_list:
        for k, v in obj.items():
            if v:
                keywords_set.add(f"{k.lower()} {v.lower()}")
    return list(keywords_set)


def add_ordered_similarity_results_to_prompt(similarity_results: list, prompt: str = ""):
    prompt += "Most relevant Dandi sets:\n"
    for r in similarity_results:
        dandiset_id = r[0].split("/")[0].split("DANDI:")[1]
        score = r[1]
        m = get_dandiset_metadata(dandiset_id=dandiset_id)
        m2 = collect_relevant_metadata(metadata_list=[m])[0]
        m2["relevance_score"] = f"relevance score: {score}"
        text = ""
        for k, v in m2.items():
            if isinstance(v, list):
                text += ", ".join(v) + "\n"
            elif "DANDI:" in v:
                text += f'{v.replace("DANDI:", "DANDISET:")}\n'
            else:
                text += f"{v}\n"
        
        prompt += f"\n{text}"
    return prompt


def get_llm_chat_answer(prompt: str):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful neuroscience research assistant, you give brief and informative suggestions to users questions, always based on a list of relevant reference dandi sets."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message["content"]