#!/usr/bin/env python3
import argparse
import hashlib
from collections import namedtuple

import docker_util
from verbose_print import print_v
from verbose_print import print_vv
from verbose_print import set_print_level


ImageParityFields = namedtuple(
    'ImageParityFields',
    ('image_cmds_hash', 'packages_hash'),
)

GET_PACKAGE_LIST_COMMAND = ['dpkg', '-l']


def _docker_push_latest_if_changed(source, target, is_dry_run):
    _validate_source(source)
    target = _get_sanitized_target(source, target)

    print_v('Pushing source image')
    docker_util.push_image(source, is_dry_run)
    try:
        print('Pulling target image...')
        docker_util.pull_image(target)
    except docker_util.ImageNotFoundError:
        print((
            f'Target image {target} was not found in the registry. '
            'Going to attempt to tag and push the target image anyway.'
        ))
        docker_util.tag_image(source, target, is_dry_run)
        docker_util.push_image(target, is_dry_run)
    else:
        if _is_image_changed(source, target):
            print((
                'Source image was found to be different from the current '
                'version of the target image. Tagging and pushing new target '
                'image.'
            ))
            docker_util.tag_image(source, target, is_dry_run)
            docker_util.push_image(target, is_dry_run)
        else:
            print((
                'Source image was found to be the same as the current '
                'version of the target image. Not pushing the target image.'
            ))


def _validate_source(source):
    print_vv('Docker inspecting source to verify it exists')
    source_inspect = docker_util.inspect_image(source)
    if source not in source_inspect['RepoTags']:
        # Hack to check if source is just a repo without a tag.
        # An inspect query with just a repo will search for
        # latest, but the result in RepoTags will only have
        # repo:latest and not just repo
        raise ValueError((
            f'The source image {source} does not have a tag! '
            'You must include a tag in the source parameter.'
        ))


def _get_sanitized_target(source, target):
    if not target:
        repository = source.rsplit(':', 1)[0]
        target = '{repository}:latest'.format(repository=repository)
        print_v((
            'Target was not given, so falling back to "{repository}:latest". '
            f'Target is now {target}'
        ))
    if source == target:
        raise ValueError((
            f'The source ({source}) and target ({target}) repo:tags are both '
            'the same! Source and target tags cannot be the same.'
        ))
    return target


def _is_image_changed(source, target):
    source_parity_fields = _get_image_parity_fields(source)
    target_parity_fields = _get_image_parity_fields(target)
    print_v(f'Source parity fields: {source_parity_fields}')
    print_v(f'Target parity fields: {target_parity_fields}')
    if source_parity_fields == target_parity_fields:
        return False
    else:
        return True


def _get_image_parity_fields(image):
    return ImageParityFields(
        image_cmds_hash=_get_image_cmds_hash(image),
        packages_hash=_get_packages_hash(image),
    )


def _get_image_cmds_hash(image):
    image_cmds = docker_util.get_image_cmds(image)
    print_vv(f'Docker commands for {image}:\n{image_cmds}')
    cmds_hash = _get_sha256_hexdigest(image_cmds)
    return cmds_hash


def _get_packages_hash(image):
    packages_blob = docker_util.run_in_image(image, GET_PACKAGE_LIST_COMMAND)
    print_vv(f'Packages blob for {image}:\n{packages_blob}')
    packages_hash = _get_sha256_hexdigest(packages_blob)
    return packages_hash


def _get_sha256_hexdigest(blob):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(blob)
    return sha256_hash.hexdigest()


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
    set_print_level(arguments.verbose)
    _docker_push_latest_if_changed(
        arguments.source,
        arguments.target,
        arguments.dry_run
    )
