import http
import json
import typing
import urllib.request

from docker_push_latest_if_changed import _inspect_image


class Image(typing.NamedTuple):
    tag: str
    name: str
    registry_uri: str
    name_tag: str
    registry_tag: str


def get_image(name, tag, registry_uri):
    if tag:
        name_tag = f'{name}:{tag}'
        registry_tag = f'{registry_uri}/{name}:{tag}'
    else:
        name_tag = name
        registry_tag = f'{registry_uri}/{name}'
    return Image(
        tag=tag,
        name=name,
        registry_uri=registry_uri,
        name_tag=name_tag,
        registry_tag=registry_tag,
    )


def is_image_on_registry(image):
    manifest = None
    try:
        manifest = _get_manifest(image)
    except urllib.error.HTTPError as e:
        if e.getcode() == http.HTTPStatus.NOT_FOUND.value:
            pass
        else:
            raise
    return True if manifest else False


def are_two_images_on_registry_the_same(source_image, target_image):
    assert source_image.registry_uri == target_image.registry_uri
    source_manifest = _get_manifest(source_image)
    target_manifest = _get_manifest(target_image)
    return source_manifest['fsLayers'] == target_manifest['fsLayers']


def is_local_image_the_same_on_registry(local_image, registry_image):
    local_image_inspect = _inspect_image(local_image.name)
    local_image_config = local_image_inspect['Config']

    registry_image_manifest = _get_manifest(registry_image)
    registry_image_config = json.loads(
        registry_image_manifest['history'][0]['v1Compatibility']
    )['config']

    return local_image_config == registry_image_config


def _get_manifest(image):
    manifest_uri = (
        f'http://{image.registry_uri}'
        f'/v2/{image.name}/manifests/{image.tag}'
    )
    response = urllib.request.urlopen(manifest_uri).read()
    return json.loads(response)
