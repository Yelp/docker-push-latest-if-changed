import http
import json
import subprocess
import urllib.request
from typing import Any
from typing import Dict
from urllib.error import HTTPError

from docker_push_latest_if_changed import Image


def is_image_on_registry(image: Image) -> bool:
    try:
        get_manifest(image)
    except HTTPError as e:
        if e.getcode() == http.HTTPStatus.NOT_FOUND.value:
            return False
        else:
            raise
    return True


def are_two_images_on_registry_the_same(
    source_image: Image,
    target_image: Image,
) -> bool:
    assert source_image.host == target_image.host
    source_manifest = get_manifest(source_image)
    target_manifest = get_manifest(target_image)
    return source_manifest['fsLayers'] == target_manifest['fsLayers']


def is_local_image_the_same_on_registry(
    local_image: Image,
    registry_image: Image,
) -> bool:
    local_image_inspect = inspect_image(local_image.name)
    local_image_config = local_image_inspect['Config']

    registry_image_manifest = get_manifest(registry_image)
    registry_image_config = json.loads(
        registry_image_manifest['history'][0]['v1Compatibility']
    )['config']

    return local_image_config == registry_image_config


def inspect_image(image_uri: str) -> Dict[str, Any]:
    output = subprocess.check_output(('docker', 'inspect', image_uri))
    return json.loads(output)[0]


def get_manifest(image: Image) -> Dict[str, Any]:
    manifest_uri = (
        f'http://{image.host}'
        f'/v2/{image.name}/manifests/{image.tag}'
    )
    response = urllib.request.urlopen(manifest_uri).read()
    return json.loads(response)
