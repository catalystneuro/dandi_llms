import json
from pathlib import Path
import requests
import pprint

from dandi.dandiapi import DandiAPIClient


def build_metadata_dict_from_dandiset_metadata(dandiset_metadata):
    about = dandiset_metadata.about
    anatomy = [a for a in about if a.schemaKey == "Anatomy"]
    asset_summary = dandiset_metadata.assetsSummary
    species = asset_summary.species
    approach = asset_summary.approach
    measurement = asset_summary.measurementTechnique

    anatomy_name_list = [a.name for a in anatomy]
    anatomy_identifier_list = [a.identifier for a in anatomy]
    species_name_list = [s.name for s in species]
    species_identifier_list = [str(s.identifier) for s in species]
    approach_name_list = [a.name for a in approach]
    measurement_name_list = [m.name for m in measurement]

    metadata = dict(
        species_names=species_name_list,
        approach_names=approach_name_list,
        measurement_names=measurement_name_list,
        species_identifiers=species_identifier_list,
        anatomy=anatomy_name_list,
        anatomy_identifiers=anatomy_identifier_list,
    )

    return metadata


def has_nwb(metadata):
    if hasattr(metadata, "assetsSummary"):
        assets_summary = metadata.assetsSummary
        if hasattr(assets_summary, "dataStandard") and assets_summary.dataStandard:
            return any(
                x.identifier == "RRID:SCR_015242" for x in assets_summary.dataStandard
            )
    return False


def get_doi_from_dandiset_metadata(dandiset_metadata: dict) -> str | None:
    doi = None

    if hasattr(dandiset_metadata, "relatedResource"):
        related_resource_list = dandiset_metadata.relatedResource
        if related_resource_list:
            related_resource = related_resource_list[0]
            identifier = related_resource.identifier
            if identifier:
                doi = identifier

    return doi


def get_crossref_abstract(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "message" in data and "abstract" in data["message"]:
            abstract = data["message"]["abstract"]
            start_index = abstract.find("<jats:p>") + len("<jats:p>")
            end_index = abstract.find("</jats:p>")

            # Extract the text between the tags
            proper_abstract = abstract[start_index:end_index]
            proper_abstract = proper_abstract.replace("<jats:sup>", "").replace(
                "</jats:sup>", ""
            )
            cleaned_abstract = proper_abstract.replace("<jats:italic>", "").replace(
                "</jats:italic>", ""
            )

            return cleaned_abstract

        else:
            return None
    else:
        return None


def valid_doi(doi):
    is_identifier_doi = doi and ("doi" in doi.lower() or "/" in doi)
    return is_identifier_doi


if __name__ == "__main__":
    verbose = True
    client = DandiAPIClient()
    all_dandisets_generator = client.get_dandisets()

    # Build a dictionary that maps dandiset_id to a dictionary containing the doi, metadata, and abstract
    dandiset_id_to_training_metadata = dict()
    for dandiset in all_dandisets_generator:
        try:
            dandiset_metadata = dandiset.get_metadata()
        except:
            continue
        doi = get_doi_from_dandiset_metadata(dandiset_metadata)
        if valid_doi(doi) and has_nwb(dandiset_metadata):
            abstract = get_crossref_abstract(doi)
            if abstract:
                metadata_dict = build_metadata_dict_from_dandiset_metadata(
                    dandiset_metadata
                )
                dandiset_id = dandiset_metadata.identifier.split(":")[1]
                dandiset_dict = dict(doi=doi, metadata=metadata_dict, abstract=abstract)
                dandiset_id_to_training_metadata[dandiset_id] = dandiset_dict
                if verbose:
                    print("-----------------------------------")
                    print(dandiset_id, doi)
                    pprint.pprint(abstract)
                    pprint.pprint(metadata_dict)

    # Save this to json file
    root_path = Path(__file__).parent.parent
    file_path = root_path / "data" / "training_data.json"

    with file_path.open(mode="w") as fp:
        json.dump(dandiset_id_to_training_metadata, fp=fp)
