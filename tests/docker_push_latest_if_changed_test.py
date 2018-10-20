import re

import pytest

from docker_push_latest_if_changed import _get_image
from docker_push_latest_if_changed import _push_image
from docker_push_latest_if_changed import _tag_image
from docker_push_latest_if_changed import ImageKey
from docker_push_latest_if_changed import ImageNotFoundError
from docker_push_latest_if_changed import main
from testing.helpers import are_two_images_on_registry_the_same
from testing.helpers import is_image_on_registry
from testing.helpers import is_local_image_the_same_on_registry


IMAGE_KEY_RE_SUFFIX = (
    r"ImageKey\(commands_hash='(?P<commands_hash>\w+)', "
    r"packages_hash='(?P<packages_hash>\w+)'"
)


def test_push_new_image(
    capsys,
    fake_docker_registry,
    fake_image_foo_name,
    fake_image_bar_name,
):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:foo')
    _tag_image(source.name, source.uri, is_dry_run=False)

    target = _get_image(f'{fake_docker_registry}/{fake_image_bar_name}:latest')
    _tag_image(target.name, target.uri, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.uri, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.uri}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main(('--source', source.uri, '--target', target.uri))

    assert are_two_images_on_registry_the_same(source, target)
    assert is_local_image_the_same_on_registry(source, target)


def test_push_new_image_dry_run(
    capsys,
    fake_docker_registry,
    fake_image_foo_name,
    fake_image_bar_name,
):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:foo')
    _tag_image(source.name, source.uri, is_dry_run=False)

    target = _get_image(f'{fake_docker_registry}/{fake_image_bar_name}:latest')
    _tag_image(target.name, target.uri, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.uri, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.uri}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main(('--source', source.uri, '--target', target.uri, '--dry-run'))
    out, _ = capsys.readouterr()
    assert 'Image was not actually tagged since this is a dry run' in out
    assert 'Image was not actually pushed since this is a dry run' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)


def test_two_same_images(capsys, fake_docker_registry, fake_image_foo_name):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:foo')
    _tag_image(source.name, source.uri, is_dry_run=False)

    target = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:latest')
    _tag_image(target.name, target.uri, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.uri, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.uri}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main(('--source', source.uri, '--target', target.uri))
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.uri}' not in out
    assert 'Image has NOT changed' in out
    assert are_two_images_on_registry_the_same(source, target)
    assert is_local_image_the_same_on_registry(source, target)


def test_two_same_images_with_different_packages(
    capsys,
    fake_docker_registry,
    fake_baz_dummy_deb_images,
):
    baz_dummy_deb_name, baz_no_dummy_deb_name = fake_baz_dummy_deb_images
    source = _get_image(f'{fake_docker_registry}/{baz_dummy_deb_name}:baz')
    _tag_image(source.name, source.uri, is_dry_run=False)

    target = _get_image(
        f'{fake_docker_registry}/{baz_no_dummy_deb_name}:latest'
    )
    _tag_image(target.name, target.uri, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.uri, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.uri}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main(('--source', source.uri, '--target', target.uri))

    out, _ = capsys.readouterr()
    source_key = ImageKey(
        **re.search(
            f'Source key: {IMAGE_KEY_RE_SUFFIX}',
            out,
        ).groupdict()
    )
    target_key = ImageKey(
        **re.search(
            f'Target key: {IMAGE_KEY_RE_SUFFIX}',
            out,
        ).groupdict()
    )
    assert source_key.packages_hash != target_key.packages_hash
    assert source_key.commands_hash == target_key.commands_hash

    assert are_two_images_on_registry_the_same(source, target)
    assert is_local_image_the_same_on_registry(source, target)


def test_no_target(fake_docker_registry, fake_image_foo_name):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:foo')
    _tag_image(fake_image_foo_name, source.uri, is_dry_run=False)

    expected_target = _get_image(
        f'{fake_docker_registry}/{fake_image_foo_name}:latest'
    )

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(expected_target)
    main(('--source', source.uri))

    assert is_local_image_the_same_on_registry(source, expected_target)


def test_no_previous_image(fake_docker_registry, fake_image_foo_name):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:foo')
    _tag_image(fake_image_foo_name, source.uri, is_dry_run=False)

    target = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:latest')
    _tag_image(target.name, target.uri, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    main(('--source', source.uri, '--target', target.uri))

    assert are_two_images_on_registry_the_same(source, target)
    assert is_local_image_the_same_on_registry(source, target)


def test_omit_target_tag(fake_docker_registry, fake_image_foo_name):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:foo')
    _tag_image(fake_image_foo_name, source.uri, is_dry_run=False)

    target = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}')
    _tag_image(target.name, target.uri, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    main(('--source', source.uri, '--target', target.uri))

    expected_target = _get_image(
        f'{fake_docker_registry}/{fake_image_foo_name}:latest'
    )

    assert are_two_images_on_registry_the_same(source, expected_target)
    assert is_local_image_the_same_on_registry(source, expected_target)


def test_source_has_no_tag(fake_docker_registry, fake_image_foo_name):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}')
    _tag_image(fake_image_foo_name, source.uri, is_dry_run=False)

    target = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:latest')
    _tag_image(target.name, target.uri, is_dry_run=False)

    with pytest.raises(ValueError) as e:
        main(('--source', source.uri, '--target', target.uri))
    assert f'{source.uri} does not have a tag!' in str(e)


def test_source_and_target_have_the_same_tag(
    fake_docker_registry,
    fake_image_foo_name,
    fake_image_bar_name,
):
    source = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:latest')
    _tag_image(fake_image_foo_name, source.uri, is_dry_run=False)

    target = _get_image(f'{fake_docker_registry}/{fake_image_foo_name}:latest')
    _tag_image(target.name, target.uri, is_dry_run=False)

    with pytest.raises(ValueError) as e:
        main(('--source', source.uri, '--target', target.uri))
    assert 'repo:tags cannot be the same' in str(e)


def test_image_doesnt_exist():
    source = _get_image('woowoo.spoopy.com/woo:latest')
    with pytest.raises(ImageNotFoundError) as e:
        main(('--source', source.uri))
    assert f'The image {source.uri} was not found' in str(e)


def test_invalid_image_name():
    fake_invalid_image_name = 'lol'
    with pytest.raises(ValueError) as e:
        main(('--source', fake_invalid_image_name))
    assert f'Image uri {fake_invalid_image_name} is malformed' in str(e)
