import pytest

from docker_push_latest_if_changed import main


def test_responds_to_help(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(('--help',))
    assert excinfo.value.code == 0
    out, _ = capsys.readouterr()
    assert 'usage: ' in out
    assert '--source' in out
