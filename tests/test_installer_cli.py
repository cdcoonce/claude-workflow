import json

from scripts.installer import cli


def _make_preset(root, name):
    p = root / name / ".claude-plugin"
    p.mkdir(parents=True)
    (p / "plugin.json").write_text(json.dumps({"name": name, "version": "1.0.0"}))


def test_install_project_scope_places_plugin(tmp_path, monkeypatch):
    presets = tmp_path / "presets"
    presets.mkdir()
    _make_preset(presets, "data-pipeline")
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)  # so claude-code auto-detects
    monkeypatch.setattr(cli, "PRESETS_ROOT", presets)
    monkeypatch.chdir(repo)

    rc = cli.main(["install", "--preset", "data-pipeline"])

    assert rc == 0
    assert (repo / ".claude" / "plugins" / "data-pipeline" / ".claude-plugin" / "plugin.json").is_file()


def test_install_dry_run_writes_nothing(tmp_path, monkeypatch):
    presets = tmp_path / "presets"
    presets.mkdir()
    _make_preset(presets, "data-pipeline")
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    monkeypatch.setattr(cli, "PRESETS_ROOT", presets)
    monkeypatch.chdir(repo)

    rc = cli.main(["install", "--preset", "data-pipeline", "--dry-run"])

    assert rc == 0
    assert not (repo / ".claude" / "plugins" / "data-pipeline").exists()


def test_install_unknown_preset_errors(tmp_path, monkeypatch, capsys):
    presets = tmp_path / "presets"
    presets.mkdir()
    _make_preset(presets, "data-pipeline")
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    monkeypatch.setattr(cli, "PRESETS_ROOT", presets)
    monkeypatch.chdir(repo)

    rc = cli.main(["install", "--preset", "nope"])

    assert rc == 2
    assert "data-pipeline" in capsys.readouterr().out  # lists valid presets


def test_list_shows_presets_and_detected_agent(tmp_path, monkeypatch, capsys):
    presets = tmp_path / "presets"
    presets.mkdir()
    _make_preset(presets, "analysis")
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    monkeypatch.setattr(cli, "PRESETS_ROOT", presets)
    monkeypatch.chdir(repo)

    rc = cli.main(["list"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "analysis" in out
    assert "claude-code" in out
