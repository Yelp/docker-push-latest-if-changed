#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import typing


class ImageNotFoundError(ValueError):
    pass


class _ImageKey(typing.NamedTuple):
    commands_hash: str
    packages_hash: str


def _docker_push_latest_if_changed(source, target, *, is_dry_run):
    _validate_source(source)
    target = _get_sanitized_target(source, target)

    print('Pushing source image')
    _push_image(source, is_dry_run=is_dry_run)
    try:
        print('Pulling target image...')
        _pull_image(target)
    except ImageNotFoundError:
        print((
            f'Target image {target} was not found in the registry. '
            'Going to attempt to tag and push the target image anyway.'
        ))
        _tag_image(source, target, is_dry_run=is_dry_run)
        _push_image(target, is_dry_run=is_dry_run)
    else:
        if _has_image_changed(source, target):
            print((
                'Source image was found to be different from the current '
                'version of the target image. Tagging and pushing new target '
                'image.'
            ))
            _tag_image(source, target, is_dry_run=is_dry_run)
            _push_image(target, is_dry_run=is_dry_run)
        else:
            print((
                'Source image was found to be the same as the current '
                'version of the target image. Not pushing the target image.'
            ))


def _validate_source(source):
    print('Docker inspecting source to verify it exists')
    source_inspect = _inspect_image(source)
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
        repository = source.rpartition(':')[0]
        target = f'{repository}:latest'
        print((
            'Target was not given, so falling back to "{repository}:latest". '
            f'Target is now {target}'
        ))
    if source == target:
        raise ValueError((
            f'The source ({source}) and target ({target}) repo:tags are both '
            'the same! Source and target tags cannot be the same.'
        ))
    return target


def _has_image_changed(source, target):
    source_key = _get_image_key(source)
    target_key = _get_image_key(target)
    print(f'Source key: {source_key}')
    print(f'Target key: {target_key}')
    return source_key != target_key


def _get_image_key(image):
    return _ImageKey(
        commands_hash=_get_commands_hash(image),
        packages_hash=_get_packages_hash(image),
    )


def _get_commands_hash(image):
    image_commands = _get_image_commands(image)
    print(f'Docker commands for {image}:\n{image_commands}')
    return _get_sha256_hexdigest(image_commands)


def _get_packages_hash(image):
    packages = _run_in_image(image, ('dpkg', '-l'))
    print(f'Packages for {image}:\n{packages}')
    return _get_sha256_hexdigest(packages)


def _get_sha256_hexdigest(blob):
    return hashlib.sha256(blob).hexdigest()


def _tag_image(source, target, *, is_dry_run):
    print(f'Tagging image {source} as {target}')
    tag_command = ('docker', 'tag', source, target)
    if is_dry_run:
        tag_command = ('#',) + tag_command
        print(' '.join(tag_command))
        print('Image was not actually tagged since this is a dry run')
    else:
        _check_output_and_print(tag_command)


def _pull_image(image):
    pull_command = ('docker', 'pull', image)
    try:
        _check_output_and_print(pull_command)
    except subprocess.CalledProcessError as e:
        raise ImageNotFoundError(f'The image {image} was not found') from e


def _push_image(image, *, is_dry_run):
    print(f'Pushing image {image} ...')
    push_command = ('docker', 'push', image)
    if is_dry_run:
        push_command = ('#',) + push_command
        print(' '.join(push_command))
        print('Image was not actually pushed since this is a dry run')
    else:
        _check_output_and_print(push_command)


def _inspect_image(image):
    inspect_command = ('docker', 'inspect', image)
    try:
        docker_inspect_output = _check_output_and_print(inspect_command)
    except subprocess.CalledProcessError as e:
        raise ImageNotFoundError(f'The image {image} was not found') from e
    return json.loads(docker_inspect_output)[0]


def _get_image_commands(image):
    history_command = (
        'docker',
        'history',
        '--no-trunc',
        '--format',
        '{{.CreatedBy}}',
        image,
    )
    return _check_output_and_print(history_command)


def _run_in_image(image, command):
    run_command = (
        'docker',
        'run',
        '--rm',
        '--net=none',
        '--user=nobody',
        image,
    ) + command
    return _check_output_and_print(run_command)


def _check_output_and_print(command):
    print(' '.join(command))
    output = subprocess.check_output(command)
    return output


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
        '--dry-run',
        action='store_true',
        help=("Run command, but don't actually push or tag images."),

    )
    arguments = parser.parse_args(argv)
    _docker_push_latest_if_changed(
        arguments.source,
        arguments.target,
        is_dry_run=arguments.dry_run,
    )


if __name__ == '__main__':
    exit(main())
