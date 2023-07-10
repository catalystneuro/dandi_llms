import json
import requests
from pathlib import Path

import openai
import os

root_path = Path(__file__).parent.parent
data_dir = root_path / "data"
assert data_dir.is_dir()
file_path = data_dir / "training_data.json"
dandiset_training_data = json.load(file_path.open())


def generate_prompt_from_dandiset_id(dandiset_id: str) -> str:
    dandiset_fields_metadata = dandiset_training_data[dandiset_id]["metadata"]
    abstract = dandiset_training_data[dandiset_id]["abstract"]

    prompt = generate_prompt_for_example(abstract, dandiset_fields_metadata)
    return prompt


def generate_prompt_for_example(abstract: str, expected_metadata: dict) -> str:
    prompt = f"""The abstract of the paper is:
    {abstract} 
    Information: {json.dumps(expected_metadata)}
    """
    return prompt


def generate_zero_shot_prompt(dandiset_ids: list) -> str:
    examples_prompt = ""
    for i, dandiset_id in enumerate(dandiset_ids):
        examples_prompt += (
            f"\n- Example {i+1}: {generate_prompt_from_dandiset_id(dandiset_id)}"
        )
    return examples_prompt


def get_crossref_abstract(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "message" in data and "abstract" in data["message"]:
            abstract_message = data["message"]["abstract"]
            start_index = abstract_message.find("<jats:p>") + len("<jats:p>")
            end_index = abstract_message.find("</jats:p>")
            abstract_text = abstract_message[start_index:end_index]

            # Extract the text between the tags
            cleaned_abstract_text = (
                abstract_text.replace("<jats:sup>", "")
                .replace("</jats:sup>", "")
                .replace("<jats:italic>", "")
                .replace("</jats:italic>", "")
            )

            return cleaned_abstract_text

        else:
            return None
    else:
        return None


def generate_task_prompt_from_abstract(abstract: str) -> str:
    prompt = f"""The abstract of the paper is:
    {abstract} 

    Fill as in the examples:
    Information: {{}}
    In the format of the previous reponse. If some information is missing, leave it blank.
    """
    return prompt


def query_metadata(prompt):
    system_content = "You are a neuroscience researcher and you are interested in figuring relevant metadata from abstracts"

    model = "gpt-3.5-turbo"
    openai.api_key = os.getenv("OPENAI_API_KEY")
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


def parse_response_to_dict(response):
    start_index = response.find("{")
    end_index = response.rfind("}")
    json_string = response[start_index : end_index + 1]
    response_dictionary = json.loads(json_string)

    return response_dictionary

def infer_metadata(prompt):
    response = query_metadata(prompt)

    try:
        response_dict = parse_response_to_dict(response)
        return response_dict
    except:
        return response