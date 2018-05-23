#!/usr/bin/env python3
import argparse
import hashlib
import logging
from collections import namedtuple

import docker


ImageParityFields = namedtuple(
    'ImageParityFields',
    ['image_cmds_hash', 'packages_hash'],
)

GET_PACKAGE_LIST_COMMAND = 'dpkg -l'


def _docker_push_latest_if_changed(source, target, is_dry_run):
    docker_client = _get_docker_client()
    _validate_source(source, docker_client)
    target = _get_sanitized_target(source, target)

    logging.info('Pushing source image')
    _push_image(source, docker_client, is_dry_run)
    try:
        logging.warning('Pulling target image')
        docker_client.pull(target)
    except docker.errors.NotFound:
        logging.warning((
            'Target image {} was not found in the registry. '
            'Going to attempt to tag and push the target image anyway.'
        ).format(target))
        _tag_image(source, target, docker_client, is_dry_run)
        _push_image(target, docker_client, is_dry_run)
    else:
        if _is_image_changed(source, target, docker_client):
            logging.warning((
                'Source image was found to be different from the current '
                'version of the target image. Tagging and pushing new target '
                'image.'
            ))
            _tag_image(source, target, docker_client, is_dry_run)
            _push_image(target, docker_client, is_dry_run)
        else:
            logging.warning((
                'Source image was found to be the same as the current '
                'version of the target image. Not pushing the target image.'
            ))


def _validate_source(source, docker_client):
    logging.debug('Docker inspecting source to verify it exists')
    source_inspect = docker_client.inspect_image(source)
    if source not in source_inspect['RepoTags']:
        # Hack to check if source is just a repo without a tag.
        # An inspect_image query with just a repo will search for
        # latest, but the result in RepoTags will only have
        # repo:latest and not just repo
        raise ValueError((
            'The source image {source} does not have a tag! '
            'You must include a tag in the source parameter.'
        ).format(source=source))


def _get_sanitized_target(source, target):
    if not target:
        repository = source.rsplit(':', 1)[0]
        target = '{repository}:latest'.format(repository=repository)
        logging.info((
            'Target was not given so falling back to ":latest". '
            'Target is now {}'
        ).format(target))
    if source == target:
        raise ValueError((
            'The source ({source}) and target ({target}) repo:tags are both '
            'the same! Source and target cannot be the same.'
        ).format(source=source, target=target))
    return target


def _tag_image(source, target, docker_client, is_dry_run):
    logging.warning('Tagging target image {}'.format(target))
    if is_dry_run:
        logging.warning(
            'WARNING: Image was not actually tagged since this is a dry run'
        )
    else:
        docker_client.tag(source, target)


def _push_image(image, docker_client, is_dry_run):
    logging.warning('Pushing target image {} ...'.format(image))
    if is_dry_run:
        logging.warning(
            'WARNING: Image was not actually pushed since this is a dry run'
        )
    else:
        docker_client.push(image)


def _is_image_changed(source, target, docker_client):
    source_parity_fields = _get_image_parity_fields(source, docker_client)
    target_parity_fields = _get_image_parity_fields(target, docker_client)
    logging.info('Source parity fields: {}'.format(source_parity_fields))
    logging.info('Target parity fields: {}'.format(target_parity_fields))
    if source_parity_fields == target_parity_fields:
        return False
    else:
        return True


def _get_image_parity_fields(image, docker_client):
    return ImageParityFields(
        image_cmds_hash=_get_image_cmds_hash(image, docker_client),
        packages_hash=_get_packages_hash(image, docker_client),
    )


def _get_image_cmds_hash(image, docker_client):
    image_history = docker_client.history(image)
    docker_cmds_blob = _get_docker_cmds_blob(image_history)
    logging.debug((
        'Docker commands blob for {image}:\n'
        '{docker_cmds_blob}'
    ).format(image=image, docker_cmds_blob=docker_cmds_blob))
    cmds_hash = _get_sha256_hexdigest(docker_cmds_blob)
    return cmds_hash


def _get_docker_cmds_blob(history):
    docker_cmds_blob = []
    for layer_number, layer in enumerate(history):
        cmd = layer['CreatedBy']
        layer_blob = 'Layer {layer_number}: {cmd}\n'.format(
            layer_number=layer_number,
            cmd=cmd,
        )
        docker_cmds_blob.append(layer_blob)
    docker_cmds_blob = ''.join(docker_cmds_blob).encode()
    return docker_cmds_blob


def _get_packages_hash(image, docker_client):
    container = docker_client.create_container(image, GET_PACKAGE_LIST_COMMAND)
    try:
        docker_client.start(container)
    except docker.errors.APIError:
        logging.error((
            'Attempt to get package list from the image {image} with the '
            'command {package_list_command} failed!'
        ).format(image=image, package_list_command=GET_PACKAGE_LIST_COMMAND))
        raise
    container_packages_blob = docker_client.logs(container)
    logging.debug((
        'Packages blob for {image}:\n'
        '{container_packages_blob}'
    ).format(image=image, container_packages_blob=container_packages_blob))
    packages_hash = _get_sha256_hexdigest(container_packages_blob)
    return packages_hash


def _get_sha256_hexdigest(blob):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(blob)
    return sha256_hash.hexdigest()


def _get_docker_client():
    return docker.Client(version='auto')


def _setup_logging(verbosity):
    logger = logging.getLogger()
    if verbosity == 0:
        logger.setLevel(logging.WARNING)
    elif verbosity == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--source', required=True,
        help=(
            'Local image tag to be considered for pushing.  '
            'For example `--source docker.example.com/img-name:2017.01.05`.'
        ),
    )
    parser.add_argument(
        '--target',
        help=(
            'Target remote image to push if the docker image is changed.  '
            'If omitted, the image will be $repository:latest of the '
            '`--source` image.'
        ),
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help=(
            'Make output more verbose. Use twice for more verbosity.'
        ),
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=(
            "Run command, but don't actually push or tag images."
        ),

    )
    arguments = parser.parse_args(argv)
    _setup_logging(arguments.verbose)
    _docker_push_latest_if_changed(
        arguments.source,
        arguments.target,
        arguments.dry_run
    )


if __name__ == '__main__':
    exit(main())
