import json
import os
import random
import shutil
import string
import subprocess
import time
import urllib.request

import pytest
from ephemeral_port_reserve import reserve

from docker_util import inspect_image


DOCKER_REGISTRY_IMAGE_NAME = 'registry'
DEFAULT_TESTING_IMAGES_PATH = os.path.abspath(
    os.path.join('testing', 'dockerfiles')
)


@pytest.fixture
def fake_docker_registry():
    subprocess.check_call(('docker', 'pull', DOCKER_REGISTRY_IMAGE_NAME))
    port = reserve()
    fake_registry_name = _get_name_with_random_suffix('registry_testing')
    run_registry_command = (
        'docker',
        'run',
        '-d',
        '-p',
        f'127.0.0.1:{port}:5000',
        '--name',
        fake_registry_name,
        'registry'
    )
    subprocess.check_call(run_registry_command)
    registry_uri = f'127.0.0.1:{port}'
    _check_registry_is_up(registry_uri)
    yield registry_uri
    subprocess.check_call(('docker', 'rm', '-f', fake_registry_name))


@pytest.fixture(scope='session')
def fake_image_foo_name():
    image_name = _build_testing_image('foo')
    yield image_name
    _delete_image(image_name)


@pytest.fixture(scope='session')
def fake_image_bar_name():
    image_name = _build_testing_image('bar')
    yield image_name
    _delete_image(image_name)


@pytest.fixture()
def dummy_deb_nginx():
    image_name = _build_testing_image('dummy_deb_nginx')
    port = reserve()
    dummy_deb_nginx_name = _get_name_with_random_suffix('dummy_deb_nginx')
    run_dummy_deb_nginx_command = (
        'docker',
        'run',
        '-d',
        '-p',
        f'127.0.0.1:{port}:80',
        '--name',
        dummy_deb_nginx_name,
        image_name
    )
    subprocess.check_call(run_dummy_deb_nginx_command)
    image_ip = inspect_image(dummy_deb_nginx_name)[
        'NetworkSettings']['Networks']['bridge']['IPAddress']
    yield (dummy_deb_nginx_name, image_ip)
    _delete_image(image_name)


@pytest.fixture()
def fake_baz_dummy_deb_images(tmpdir, dummy_deb_nginx):
    nginx_name, nginx_ip = dummy_deb_nginx
    baz_path = _create_baz_dockerfile(nginx_ip, tmpdir)
    baz_dummy_deb_image_name = _build_testing_image(
        'baz',
        dockerfile_path=baz_path,
        with_no_cache=True
    )
    subprocess.check_call(('docker', 'stop', nginx_name))
    baz_no_dummy_deb_image_name = _build_testing_image(
        'baz',
        dockerfile_path=baz_path,
        with_no_cache=True
    )
    yield baz_dummy_deb_image_name, baz_no_dummy_deb_image_name
    _delete_image(baz_dummy_deb_image_name)
    _delete_image(baz_no_dummy_deb_image_name)


def _build_testing_image(
    image_name,
    dockerfile_path=None,
    with_no_cache=False,
):
    randomized_image_name = _get_name_with_random_suffix(image_name)
    if not dockerfile_path:
        dockerfile_path = f'{DEFAULT_TESTING_IMAGES_PATH}/{image_name}'
    build_command = (
        'docker', 'build', dockerfile_path, '-t', randomized_image_name
    )
    if with_no_cache:
        build_command += ('--no-cache',)
    subprocess.check_call(build_command)
    return randomized_image_name


def _get_name_with_random_suffix(name):
    return '{}_{}'.format(
        name,
        ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)),
    )


def _delete_image(image_tag):
    image_id = inspect_image(image_tag)['Id']
    subprocess.check_call(('docker', 'rmi', '-f', image_id))


def _check_registry_is_up(registry_uri):
    check_attempts = 10
    current_attempt = 0
    catalog_uri = f'http://{registry_uri}/v2/_catalog'
    while current_attempt < check_attempts:
        current_attempt += 1
        try:
            response = urllib.request.urlopen(catalog_uri).read()
            assert {"repositories": []} == json.loads(response)
        except Exception:
            if current_attempt >= check_attempts:
                raise
            else:
                time.sleep(0.5)


def _create_baz_dockerfile(nginx_ip, tmpdir):
    src_path = f'{DEFAULT_TESTING_IMAGES_PATH}/baz'
    baz_path = tmpdir.join('baz')
    shutil.copytree(src_path, baz_path)
    with open(baz_path.join('Dockerfile'), 'w') as dockerfile:
        with open(baz_path.join('Dockerfile.tmpl'), 'r') as dockerfile_tmpl:
            contents = dockerfile_tmpl.read()
        contents = contents.replace('${IP_ADDRESS}', str(nginx_ip))
        dockerfile.write(contents)
    return baz_path
