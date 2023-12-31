import tiktoken
from .openai import (
    keywords_extraction, 
    prepare_keywords_for_semantic_search, 
    add_ordered_similarity_results_to_prompt, 
    get_llm_chat_answer
)
from .qdrant import query_all_keywords, query_from_user_input


base_prompt = """Given the user input and the list of most reference dandisets, propose which dandisets the user might be interested in using.
Explain your decision based on the information of the reference dandisets.
Suggest only the dandisets which you consider to be most relevant. There can be multiple relevant dandisets.
Structure your answer as a numbered list, with one suggestion per item.
Always start your answers always with: "The most relevant dandisets for your question are:" 
Unless you consider there are no relevant dandisets, in which case only reply: "There are no relevant dandisets for your question"
---
User input: {user_input}
---
Reference dandisets:
{dandisets_text}
---
Begin:"""


base_prompt_methods = """Given the user input and the list of most reference dandisets, propose which dandisets the user might be interested in using.
Explain your decision based on the information of the reference dandisets.
Suggest only the dandisets which you consider to be most relevant. There can be multiple relevant dandisets.
Importantly, your response should give emphasis to the methods and techniques used, for examplo electrophyisiology, imaging, behavioral recordings, etc.
Always start your answers always with: "The most relevant dandisets for your question are:" 
Unless you consider there are no relevant dandisets, in which case only reply: "There are no relevant dandisets for your question".
Structure your answer as a numbered list, with one suggestion per item. For example:
1. dandiset number - dandiset title
    why this dandiset is relevant...
2. dandiset number - dandiset title
    why this dandiset is relevant...
...
---
User input: {user_input}
---
Reference dandisets:
{dandisets_text}
---
Begin:"""


max_num_tokens = {
    "gpt-3.5-turbo": 4000,
    "gpt-3.5-turbo-16k": 16000,
    "gpt-4": 8000,
    "gpt-4-32k": 32000,
}

def suggest_relevant_dandisets(user_input: str, model: str = "gpt-3.5-turbo", method: int = 1) -> str:
    if method == 1:
        ordered_similarity_results = query_from_user_input(text=user_input, top_k=15)
    elif method == 2:
        keywords = keywords_extraction(user_input=user_input)
        keywords_2 = prepare_keywords_for_semantic_search(keywords)
        ordered_similarity_results = query_all_keywords(keywords_2, top_k=15)
    else:
        raise ValueError("method must be 1 or 2")
    dandisets_text = add_ordered_similarity_results_to_prompt(similarity_results=ordered_similarity_results)
    prompt = prepare_prompt(user_input=user_input, dandisets_text=dandisets_text)
    return get_llm_chat_answer(prompt, model=model)


def prepare_prompt(user_input: str, dandisets_text: str, model: str = "gpt-3.5-turbo") -> str:
    prompt = base_prompt_methods.format(user_input=user_input, dandisets_text=dandisets_text)
    encoding = tiktoken.encoding_for_model(model)
    excess_tokens = len(encoding.encode(prompt)) - max_num_tokens[model]
    if excess_tokens > 0:
        dandiset_text_tokens = encoding.encode(dandisets_text)
        dandisets_text = encoding.decode(dandiset_text_tokens[:-excess_tokens])
        prompt = base_prompt_methods.format(user_input=user_input, dandisets_text=dandisets_text)
    return prompt