import pytest

from hookswitch.config import toggle_server


def test_toggle_server_changes_state():
    config = {
        "servers": {
            "server1": {"enabled": False},
            "server2": {"enabled": True},
        }
    }
    # Enable server1
    new_config = toggle_server(config, "server1", True)
    assert new_config["servers"]["server1"]["enabled"] is True
    # server2 unchanged
    assert new_config["servers"]["server2"]["enabled"] is True
    # original config unchanged
    assert config["servers"]["server1"]["enabled"] is False


def test_toggle_server_disables():
    config = {
        "servers": {
            "server1": {"enabled": True},
        }
    }
    new_config = toggle_server(config, "server1", False)
    assert new_config["servers"]["server1"]["enabled"] is False
    assert config["servers"]["server1"]["enabled"] is True


def test_toggle_server_raises_key_error():
    config = {"servers": {}}
    with pytest.raises(KeyError):
        toggle_server(config, "nonexistent", True)


def test_toggle_server_returns_new_dict():
    config = {"servers": {"s": {"enabled": False}}}
    new_config = toggle_server(config, "s", True)
    assert new_config is not config
    assert new_config["servers"] is not config["servers"]
    assert new_config["servers"]["s"] is not config["servers"]["s"]