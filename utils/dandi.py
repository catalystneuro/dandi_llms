from dandi.dandiapi import DandiAPIClient
from dandischema.models import Dandiset
import concurrent.futures


def get_dandiset_metadata(dandiset_id: str):
    with DandiAPIClient() as client:
        dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id="draft")
        return dandiset.get_metadata()


def list_dandiset_files(dandiset_id: str):
    with DandiAPIClient() as client:
        dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id="draft")
        return [i.dict().get("path") for i in dandiset.get_assets() if i.dict().get("path").endswith(".nwb")]


def get_file_url(dandiset_id: str, file_path: str):
    with DandiAPIClient() as client:
        asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(file_path)
        return asset.get_content_url(follow_redirects=1, strip_query=True)


def has_nwb(metadata: Dandiset):
    if hasattr(metadata, "assetsSummary"):
        assets_summary = metadata.assetsSummary
        if hasattr(assets_summary, "dataStandard"):
            return any(x.identifier == "RRID:SCR_015242" for x in assets_summary.dataStandard)
    return False


def process_dandiset(dandiset):
    try:
        metadata = dandiset.get_metadata()
        if has_nwb(metadata):
            return metadata
    except:
        pass
    return None


def get_all_dandisets_metadata():
    with DandiAPIClient() as client:
        all_metadata = []
        dandisets = list(client.get_dandisets())
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_dandiset, dandiset) for dandiset in dandisets]
            for future in concurrent.futures.as_completed(futures):
                metadata = future.result()
                if metadata:
                    all_metadata.append(metadata)
    return all_metadata


def collect_relevant_metadata(metadata_list: list):
    """Extract only relevant text fields from metadata list"""
    all_metadata_formatted = []
    for m in metadata_list:
        title = f"title: {m.name}"
        description = f"description: {m.description}"
        approaches = [f"approach: {a.name}" for a in m.assetsSummary.approach]
        measurement_techniques = [f"measurement technique: {a.name}" for a in m.assetsSummary.measurementTechnique]
        variables_measured = [f"variable measured: {a}" for a in m.assetsSummary.variableMeasured]
        species = [f"species: {a.name}" for a in m.assetsSummary.species]
        all_metadata_formatted.append(
            {
                "dandiset_id": m.id,
                "title": title,
                "description": description,
                "approaches": approaches,
                "measurement_techniques": measurement_techniques,
                "variables_measured": variables_measured,
                "species": species,
            }
        )
    return all_metadata_formatted