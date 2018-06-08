import re

import pytest

from docker_push_latest_if_changed import _ImageKey
from docker_push_latest_if_changed import _push_image
from docker_push_latest_if_changed import _tag_image
from docker_push_latest_if_changed import ImageNotFoundError
from docker_push_latest_if_changed import main
from testing.helpers import are_two_images_on_registry_the_same
from testing.helpers import get_image
from testing.helpers import is_image_on_registry
from testing.helpers import is_local_image_the_same_on_registry


IMAGE_KEY_RE_SUFFIX = (
    "_ImageKey\(commands_hash='(?P<commands_hash>\w+)', "
    "packages_hash='(?P<packages_hash>\w+)'"
)


def test_push_new_image(
    capsys,
    fake_docker_registry,
    fake_image_foo_name,
    fake_image_bar_name,
):
    source = get_image(fake_image_foo_name, 'foo', fake_docker_registry)
    _tag_image(source.name, source.registry_tag, is_dry_run=False)

    target = get_image(fake_image_bar_name, 'latest', fake_docker_registry)
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.registry_tag, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.registry_tag}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main(('--source', source.registry_tag, '--target', target.registry_tag))

    assert are_two_images_on_registry_the_same(source, target)
    assert is_local_image_the_same_on_registry(source, target)


def test_push_new_image_dry_run(
    capsys,
    fake_docker_registry,
    fake_image_foo_name,
    fake_image_bar_name,
):
    source = get_image(fake_image_foo_name, 'foo', fake_docker_registry)
    _tag_image(source.name, source.registry_tag, is_dry_run=False)

    target = get_image(fake_image_bar_name, 'latest', fake_docker_registry)
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.registry_tag, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.registry_tag}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main((
        '--source',
        source.registry_tag,
        '--target',
        target.registry_tag,
        '--dry-run',
    ))
    out, _ = capsys.readouterr()
    assert 'Image was not actually tagged since this is a dry run' in out
    assert 'Image was not actually pushed since this is a dry run' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)


def test_two_same_images(capsys, fake_docker_registry, fake_image_foo_name):
    source = get_image(fake_image_foo_name, 'foo', fake_docker_registry)
    _tag_image(source.name, source.registry_tag, is_dry_run=False)

    target = get_image(fake_image_foo_name, 'latest', fake_docker_registry)
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.registry_tag, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.registry_tag}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main(('--source', source.registry_tag, '--target', target.registry_tag))
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.registry_tag}' not in out
    assert f'Source image was found to be the same as the current' in out
    assert are_two_images_on_registry_the_same(source, target)
    assert is_local_image_the_same_on_registry(source, target)


def test_two_same_images_with_different_packages(
    capsys,
    fake_docker_registry,
    fake_baz_dummy_deb_images,
):
    baz_dummy_deb_name, baz_no_dummy_deb_name = fake_baz_dummy_deb_images
    source = get_image(
        baz_dummy_deb_name,
        'baz',
        fake_docker_registry,
    )
    _tag_image(source.name, source.registry_tag, is_dry_run=False)

    target = get_image(
        baz_no_dummy_deb_name,
        'latest',
        fake_docker_registry,
    )
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    _push_image(target.registry_tag, is_dry_run=False)
    out, _ = capsys.readouterr()
    assert f'Pushing image {target.registry_tag}' in out
    assert not is_image_on_registry(source)
    assert is_image_on_registry(target)

    main(('--source', source.registry_tag, '--target', target.registry_tag))

    out, _ = capsys.readouterr()
    source_key = _ImageKey(
        **re.search(
            f'Source key: {IMAGE_KEY_RE_SUFFIX}',
            out,
        ).groupdict()
    )
    target_key = _ImageKey(
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
    source = get_image(fake_image_foo_name, 'foo', fake_docker_registry)
    _tag_image(fake_image_foo_name, source.registry_tag, is_dry_run=False)

    expected_target = get_image(
        fake_image_foo_name,
        'latest',
        fake_docker_registry,
    )

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(expected_target)
    main(('--source', source.registry_tag))

    assert is_local_image_the_same_on_registry(source, expected_target)


def test_no_previous_image(fake_docker_registry, fake_image_foo_name):
    source = get_image(fake_image_foo_name, 'foo', fake_docker_registry)
    _tag_image(fake_image_foo_name, source.registry_tag, is_dry_run=False)

    target = get_image(fake_image_foo_name, 'latest', fake_docker_registry)
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    main(('--source', source.registry_tag, '--target', target.registry_tag))

    assert are_two_images_on_registry_the_same(source, target)
    assert is_local_image_the_same_on_registry(source, target)


def test_omit_target_tag(fake_docker_registry, fake_image_foo_name):
    source = get_image(fake_image_foo_name, 'foo', fake_docker_registry)
    _tag_image(fake_image_foo_name, source.registry_tag, is_dry_run=False)

    target = get_image(fake_image_foo_name, None, fake_docker_registry)
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    assert not is_image_on_registry(source)
    assert not is_image_on_registry(target)
    main(('--source', source.registry_tag, '--target', target.registry_tag))

    expected_target = get_image(
        fake_image_foo_name,
        'latest',
        fake_docker_registry,
    )

    assert are_two_images_on_registry_the_same(source, expected_target)
    assert is_local_image_the_same_on_registry(source, expected_target)


def test_source_has_no_tag(fake_docker_registry, fake_image_foo_name):
    source = get_image(fake_image_foo_name, None, fake_docker_registry)
    _tag_image(fake_image_foo_name, source.registry_tag, is_dry_run=False)

    target = get_image(fake_image_foo_name, 'latest', fake_docker_registry)
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    with pytest.raises(ValueError) as e:
        main((
            '--source',
            source.registry_tag,
            '--target',
            target.registry_tag
        ))
    assert f'{source.registry_tag} does not have a tag!' in str(e)


def test_source_and_target_have_the_same_tag(
    fake_docker_registry,
    fake_image_foo_name,
    fake_image_bar_name,
):
    source = get_image(fake_image_foo_name, 'latest', fake_docker_registry)
    _tag_image(fake_image_foo_name, source.registry_tag, is_dry_run=False)

    target = get_image(fake_image_foo_name, 'latest', fake_docker_registry)
    _tag_image(target.name, target.registry_tag, is_dry_run=False)

    with pytest.raises(ValueError) as e:
        main((
            '--source',
            source.registry_tag,
            '--target',
            target.registry_tag
        ))
    assert f'repo:tags are both the same!' in str(e)


def test_image_doesnt_exist():
    source = get_image('woo', 'latest', 'woowoo.spoopy.com')
    with pytest.raises(ImageNotFoundError) as e:
        main(('--source', source.registry_tag))
    assert f'The image {source.registry_tag} was not found' in str(e)


def test_invalid_image_name():
    fake_invalid_image_name = '////'
    with pytest.raises(ImageNotFoundError) as e:
        main(('--source', fake_invalid_image_name))
    assert f'The image {fake_invalid_image_name} was not found' in str(e)
