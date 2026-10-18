"""--color controls ANSI codes in the printed diff."""

from hookswitch.diff import GREEN, RED, RESET

ESC = "\x1b["


def test_bare_color_flag_emits_ansi(project, hs):
    _, out, _ = hs("disable", "github", "--color")
    assert f"{RED}-" in out and f"{GREEN}+" in out and RESET in out


def test_color_always_equals_bare_flag(project, hs):
    _, out, _ = hs("disable", "github", "--color", "always", "--dry-run")
    assert ESC in out


def test_no_ansi_by_default_when_not_a_terminal(project, hs):
    _, out, _ = hs("disable", "github")
    assert ESC not in out


def test_color_never(project, hs):
    _, out, _ = hs("disable", "github", "--color=never")
    assert ESC not in out


def test_no_color_env_beats_auto_but_not_explicit_flag(project, hs, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert ESC not in hs("disable", "github", "--dry-run")[1]
    assert ESC in hs("disable", "github", "--dry-run", "--color")[1]


def test_color_before_positional_does_not_swallow_the_name(project, hs):
    code, out, _ = hs("toggle", "--color", "--off", "github")
    assert code == 0
    assert ESC in out


def test_color_applies_to_undo_and_run(project, hs):
    hs("disable", "github", "-q")
    assert ESC in hs("undo", "--color")[1]
    (project / "r.yaml").write_text("disable: [github]\n", encoding="utf-8")
    assert ESC in hs("run", "r.yaml", "--color")[1]
