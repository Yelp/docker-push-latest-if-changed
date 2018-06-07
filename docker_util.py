import json
import subprocess

from verbose_print import print_v


class ImageNotFoundError(Exception):
    def __init__(self, image):
        self.image = image
        self.message = f'The image {image} was not found.'

    def __str__(self):
        return self.message


def tag_image(source, target, is_dry_run):
    print(f'Tagging image {source} as {target}')
    tag_command = ('docker', 'tag', source, target)
    if is_dry_run:
        print_v(' '.join(tag_command))
        print('Image was not actually tagged since this is a dry run')
    else:
        _check_output_and_print(tag_command)


def pull_image(image):
    pull_command = ('docker', 'pull', image)
    try:
        _check_output_and_print(pull_command)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode()
        if image in stderr and 'not found' in stderr:
            raise ImageNotFoundError(image) from e
        else:
            raise


def push_image(image, is_dry_run):
    print(f'Pushing image {image} ...')
    push_command = ('docker', 'push', image)
    if is_dry_run:
        print_v(' '.join(push_command))
        print('Image was not actually pushed since this is a dry run')
    else:
        _check_output_and_print(push_command)


def inspect_image(image):
    inspect_command = ('docker', 'inspect', image)
    try:
        docker_inspect_output = _check_output_and_print(inspect_command)
    except subprocess.CalledProcessError as e:
        if 'Error: No such object' in e.stderr.decode():
            raise ImageNotFoundError(image) from e
        else:
            raise
    return json.loads(docker_inspect_output)[0]


def get_image_cmds(image):
    history_command = (
        'docker',
        'history',
        '--no-trunc',
        '--format',
        '{{.CreatedBy}}',
        image,
    )
    return _check_output_and_print(history_command)


def run_in_image(image, command):
    run_command = ['docker', 'run', image] + command
    return subprocess.check_output(run_command)


def _check_output_and_print(command):
    print_v(' '.join(command))
    try:
        output = subprocess.check_output(command, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode())
        raise
    return output
