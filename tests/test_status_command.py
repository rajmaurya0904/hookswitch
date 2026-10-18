"""hookswitch status and check."""


def test_status_prints_only_enabled_names_one_per_line(project, hs):
    code, out, _ = hs("status")
    assert code == 0
    assert out.splitlines() == ["github", "postgres"]


def test_status_after_disable(project, hs):
    hs("disable", "github")
    assert hs("status")[1].splitlines() == ["postgres"]


def test_status_prints_nothing_when_everything_is_off(project, hs):
    hs("disable", "github", "postgres")
    code, out, _ = hs("status")
    assert code == 0
    assert out == ""


def test_check_succeeds_when_all_named_servers_are_on(project, hs):
    code, out, err = hs("check", "github", "postgres")
    assert (code, out, err) == (0, "", "")


def test_check_exits_three_when_one_is_off(project, hs):
    code, _, err = hs("check", "github", "puppeteer")
    assert code == 3
    assert "disabled: puppeteer" in err


def test_check_quiet_suppresses_message(project, hs):
    code, _, err = hs("check", "puppeteer", "--quiet")
    assert code == 3
    assert err == ""


def test_check_unknown_server_is_an_error(project, hs):
    code, _, err = hs("check", "ghost")
    assert code == 1
    assert "unknown server(s): ghost" in err
