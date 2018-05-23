from unittest import mock

import docker
import pytest

import docker_push_latest_if_changed
from docker_push_latest_if_changed import _docker_push_latest_if_changed
from docker_push_latest_if_changed import _get_docker_client
from docker_push_latest_if_changed import _get_docker_cmds_blob
from docker_push_latest_if_changed import _get_image_cmds_hash
from docker_push_latest_if_changed import _get_image_parity_fields
from docker_push_latest_if_changed import _get_packages_hash
from docker_push_latest_if_changed import _get_sanitized_target
from docker_push_latest_if_changed import _get_sha256_hexdigest
from docker_push_latest_if_changed import _is_image_changed
from docker_push_latest_if_changed import _push_image
from docker_push_latest_if_changed import _tag_image
from docker_push_latest_if_changed import _validate_source
from docker_push_latest_if_changed import GET_PACKAGE_LIST_COMMAND
from docker_push_latest_if_changed import ImageParityFields
from docker_push_latest_if_changed import main


@pytest.fixture
def mock_docker_client():
    _mock_docker_client = mock.Mock()
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_get_docker_client',
        autospec=True,
        return_value=_mock_docker_client
    ):
        yield _mock_docker_client


@pytest.fixture
def mock_tag_image():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_tag_image',
        autospec=True,
    ) as _mock_tag_image:
        yield _mock_tag_image


@pytest.fixture
def mock_push_image():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_push_image',
        autospec=True,
    ) as _mock_push_image:
        yield _mock_push_image


@pytest.fixture
def mock_is_image_changed():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_is_image_changed',
        autospec=True,
    ) as _mock_is_image_changed:
        yield _mock_is_image_changed


@pytest.fixture
def mock_validate_source():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_validate_source',
        autospec=True,
    ) as _mock_validate_source:
        yield _mock_validate_source


@pytest.fixture
def mock_get_image_parity_fields():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_get_image_parity_fields',
        autospec=True,
    ) as _mock_get_image_parity_fields:
        yield _mock_get_image_parity_fields


@pytest.fixture
def mock_get_image_cmds_hash():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_get_image_cmds_hash',
        autospec=True,
    ) as _mock_get_image_cmds_hash:
        yield _mock_get_image_cmds_hash


@pytest.fixture
def mock_get_packages_hash():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_get_packages_hash',
        autospec=True,
    ) as _mock_get_packages_hash:
        yield _mock_get_packages_hash


@pytest.fixture
def mock_get_docker_cmds_blob():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_get_docker_cmds_blob',
        autospec=True,
    ) as _mock_get_docker_cmds_blob:
        yield _mock_get_docker_cmds_blob


@pytest.fixture
def mock_get_sha256_hexdigest():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_get_sha256_hexdigest',
        autospec=True,
    ) as _mock_get_sha256_hexdigest:
        yield _mock_get_sha256_hexdigest


@pytest.fixture
def mock_sha256():
    _mock_sha256 = mock.Mock()
    with mock.patch(
        'hashlib.sha256',
        autospec=True,
        return_value=_mock_sha256
    ):
        yield _mock_sha256


@pytest.fixture
def mock_docker_client_creation():
    with mock.patch.object(
        docker,
        'Client',
        autospec=True
    ) as _mock_docker_client_creation:
        yield _mock_docker_client_creation


@pytest.fixture
def mock_docker_push_latest_if_changed():
    with mock.patch.object(
        docker_push_latest_if_changed,
        '_docker_push_latest_if_changed',
        autospec=True
    ) as _mock_docker_push_latest_if_changed:
        yield _mock_docker_push_latest_if_changed


def test_docker_push_latest_if_changed_with_source_target_image_changed(
    mock_docker_client,
    mock_is_image_changed,
    mock_tag_image,
    mock_push_image,
    mock_validate_source,
):
    source = 'wew:3'
    target = 'wew:hue'
    is_dry_run = True

    mock_is_image_changed.return_value = True
    _docker_push_latest_if_changed(source, target, is_dry_run)

    mock_validate_source.assert_called_once_with(source, mock_docker_client)
    mock_docker_client.pull.assert_called_once_with(target)
    expected_push_image_calls = [
        mock.call(source, mock_docker_client, is_dry_run),
        mock.call(target, mock_docker_client, is_dry_run),
    ]
    assert expected_push_image_calls == mock_push_image.call_args_list


def test_docker_push_latest_if_changed_with_source_target_no_image_changed(
    mock_docker_client,
    mock_is_image_changed,
    mock_tag_image,
    mock_push_image,
    mock_validate_source,
):
    source = 'woah:there'
    target = 'here:there'
    is_dry_run = True

    mock_is_image_changed.return_value = False
    _docker_push_latest_if_changed(source, target, is_dry_run)

    mock_validate_source.assert_called_once_with(source, mock_docker_client)
    mock_docker_client.pull.assert_called_once_with(target)
    mock_push_image.assert_called_once_with(
        source,
        mock_docker_client,
        is_dry_run,
    )


def test_docker_push_latest_if_changed_target_image_not_found(
    mock_docker_client,
    mock_is_image_changed,
    mock_tag_image,
    mock_push_image,
    mock_validate_source,
):
    source = 'whatis:real'
    target = 'not:real'
    is_dry_run = True

    fake_not_found_exception = docker.errors.NotFound('lol', mock.Mock())
    mock_docker_client.pull.side_effect = fake_not_found_exception
    _docker_push_latest_if_changed(source, target, is_dry_run)

    mock_validate_source.assert_called_once_with(source, mock_docker_client)
    mock_docker_client.pull.assert_called_once_with(target)
    mock_is_image_changed.assert_not_called()
    expected_push_image_calls = [
        mock.call(source, mock_docker_client, is_dry_run),
        mock.call(target, mock_docker_client, is_dry_run),
    ]
    assert expected_push_image_calls == mock_push_image.call_args_list


def test_validate_source(mock_docker_client):
    fake_image = 'haha.lolol.info/some-repo:pew'
    mock_docker_client.inspect_image.return_value = {
        'RepoTags': [fake_image],
    }
    _validate_source(fake_image, mock_docker_client)
    assert mock_docker_client.inspect_image.called_once_with(fake_image)


def test_validate_source_without_tag(mock_docker_client):
    fake_repo = 'car.cdr.eval/apply-me'
    mock_docker_client.inspect_image.return_value = {
        'RepoTags': ['car.cdr.eval/apply-me:latest'],
    }
    with pytest.raises(ValueError) as e:
        _validate_source(fake_repo, mock_docker_client)
    assert mock_docker_client.inspect_image.called_once_with(fake_repo)
    assert fake_repo in str(e)


def test_get_sanitized_target():
    fake_source = 'no.spoon.no.fork/only:spork'
    fake_target = None
    target = _get_sanitized_target(fake_source, fake_target)
    expected_target = 'no.spoon.no.fork/only:latest'
    assert expected_target == target


def test_get_sanitized_target_source_same_as_target():
    fake_source = 'show.me.the/money:homie'
    fake_target = 'show.me.the/money:homie'
    with pytest.raises(ValueError) as e:
        _get_sanitized_target(fake_source, fake_target)
    assert fake_source in str(e)


def test_get_sanitized_target_source_is_latest():
    fake_source = 'zombies.ate.my/neighbors:latest'
    fake_target = None
    with pytest.raises(ValueError) as e:
        _get_sanitized_target(fake_source, fake_target)
    assert fake_source in str(e)


def test_tag_image(mock_docker_client):
    fake_source = 'ready.or.not/here-i:come'
    fake_target = 'haha.tag/youre:it'
    is_dry_run = False
    _tag_image(fake_source, fake_target, mock_docker_client, is_dry_run)
    mock_docker_client.tag.assert_called_once_with(fake_source, fake_target)


def test_tag_image_is_dry_run(mock_docker_client):
    fake_source = 'go.directly/to:jail'
    fake_target = 'do.not/pass:go'
    is_dry_run = True
    _tag_image(fake_source, fake_target, mock_docker_client, is_dry_run)
    mock_docker_client.tag.assert_not_called()


def test_push_image(mock_docker_client):
    fake_image = 'please.accept/this:image'
    is_dry_run = False
    _push_image(fake_image, mock_docker_client, is_dry_run)
    mock_docker_client.push.assert_called_once_with(fake_image)


def test_push_image_is_dry_run(mock_docker_client):
    fake_image = 'no.image/for:you'
    is_dry_run = True
    _push_image(fake_image, mock_docker_client, is_dry_run)
    mock_docker_client.push.assert_not_called()


@pytest.mark.parametrize(['fake_source', 'fake_target', 'expected_output'], [
    ('mad', 'cows', True),
    ('moo', 'moo', False),
])
def test_is_image_changed(
    fake_source,
    fake_target,
    expected_output,
    mock_docker_client,
    mock_get_image_parity_fields,
):
    mock_get_image_parity_fields.side_effect = lambda image, client: image
    is_image_changed = _is_image_changed(
        fake_source,
        fake_target,
        mock_docker_client,
    )
    expected_get_image_parity_calls = [
        mock.call(fake_source, mock_docker_client),
        mock.call(fake_target, mock_docker_client),
    ]
    assert expected_get_image_parity_calls == \
        mock_get_image_parity_fields.call_args_list
    assert expected_output == is_image_changed


def test_get_image_parity_fields(
    mock_docker_client,
    mock_get_image_cmds_hash,
    mock_get_packages_hash,
):
    fake_image = 'are.potatoes/vegetables:latest'
    mock_get_image_cmds_hash.return_value = 'hashbrowns'
    mock_get_packages_hash.return_value = 'croquettes'
    image_parity_fields = _get_image_parity_fields(
        fake_image,
        mock_docker_client,
    )

    expected_image_parity_fields = ImageParityFields(
        image_cmds_hash=mock_get_image_cmds_hash.return_value,
        packages_hash=mock_get_packages_hash.return_value,
    )
    assert expected_image_parity_fields == image_parity_fields


def test_get_image_cmds_hash(
    mock_docker_client,
    mock_get_docker_cmds_blob,
    mock_get_sha256_hexdigest,
):
    fake_image = 'hash.hodgebodge/potpourri:mishmash'
    mock_docker_client.history.return_value = 'gallimaufry'
    mock_get_docker_cmds_blob.return_value = 'miscellany'
    cmds_hash = _get_image_cmds_hash(fake_image, mock_docker_client)

    mock_docker_client.history.assert_called_once_with(fake_image)
    mock_get_docker_cmds_blob.assert_called_once_with(
        mock_docker_client.history.return_value
    )
    mock_get_sha256_hexdigest.assert_called_once_with(
        mock_get_docker_cmds_blob.return_value
    )
    assert mock_get_sha256_hexdigest.return_value == cmds_hash


def test_get_docker_cmds_blob():
    fake_command_0 = '/bin/sh humans_suck.sh'
    fake_command_1 = '/bin/sh robots_are_the_best.sh'
    fake_history = [
        {'CreatedBy': fake_command_0},
        {'CreatedBy': fake_command_1},
    ]
    docker_cmds_blob = _get_docker_cmds_blob(fake_history)

    expected_docker_cmds_blob = (
        'Layer 0: {command_0}\n'
        'Layer 1: {command_1}\n'
    ).format(command_0=fake_command_0, command_1=fake_command_1).encode()
    assert expected_docker_cmds_blob == docker_cmds_blob


def test_get_packages_hash(
    mock_docker_client,
    mock_get_sha256_hexdigest,
):
    fake_image = 'wait.for.that/sick:drop'
    fake_container = 'wait_for_it'
    mock_docker_client.create_container.return_value = fake_container
    mock_docker_client.logs.return_value = 'bwrrrrrr'
    mock_get_sha256_hexdigest.return_value = 'wubwubwubwub'
    packages_hash = _get_packages_hash(fake_image, mock_docker_client)

    mock_docker_client.create_container.assert_called_once_with(
        fake_image,
        GET_PACKAGE_LIST_COMMAND,
    )
    mock_docker_client.start.assert_called_once_with(fake_container)
    mock_docker_client.logs.assert_called_once_with(fake_container)
    mock_get_sha256_hexdigest.assert_called_once_with(
        mock_docker_client.logs.return_value
    )
    assert mock_get_sha256_hexdigest.return_value == packages_hash


def test_get_packages_hash_start_error(
    mock_docker_client,
    mock_get_sha256_hexdigest,
):
    fake_image = 'acteyl/methyl:carbinol'
    fake_container = 'niacin'
    mock_docker_client.create_container.return_value = fake_container
    fake_api_error_exception = docker.errors.APIError('boom', mock.Mock())
    mock_docker_client.start.side_effect = fake_api_error_exception
    with pytest.raises(docker.errors.APIError):
        _get_packages_hash(fake_image, mock_docker_client)
    mock_docker_client.create_container.assert_called_once_with(
        fake_image,
        GET_PACKAGE_LIST_COMMAND,
    )
    mock_docker_client.start.assert_called_once_with(fake_container)
    mock_docker_client.logs.assert_not_called()
    mock_get_sha256_hexdigest.assert_not_called()


def test_get_sha256_hexdigest(mock_sha256):
    fake_blob = 'bibbityblobbityboo'
    mock_sha256.hexdigest.return_value = 'hexxorz'
    sha256_hexdigest = _get_sha256_hexdigest(fake_blob)
    mock_sha256.update.assert_called_once_with(fake_blob)
    assert mock_sha256.hexdigest.return_value == sha256_hexdigest


def test_get_docker_client(mock_docker_client_creation):
    mock_docker_client_creation.return_value = 'its_just_me_a_fake!'
    docker_client = _get_docker_client()
    mock_docker_client_creation.assert_called_once_with(version='auto')
    assert mock_docker_client_creation.return_value == docker_client


@pytest.mark.parametrize('verbose', [
    '',
    '-v',
    '-vv',
])
def test_main(verbose, mock_docker_push_latest_if_changed):
    fake_source = 'let.the.bodies/hit-the:floor'
    fake_target = 'somethings.got.to/give:now'
    argv = ['--source', fake_source, '--target', fake_target]
    if verbose:
        argv.append(verbose)
    main(argv)
    mock_docker_push_latest_if_changed.assert_called_once_with(
        fake_source,
        fake_target,
        False,
    )


def test_responds_to_help(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(('--help',))
    assert excinfo.value.code == 0
    out, _ = capsys.readouterr()
    assert 'usage: ' in out
    assert '--source' in out
