from scripts.installer.report import InstallReport, Scope


def test_scope_values():
    assert Scope.PROJECT.value == "project"
    assert Scope.USER.value == "user"


def test_report_records_installed_and_skipped_with_reason():
    r = InstallReport(agent="claude-code", preset="data-pipeline")
    r.add_installed("plugin -> /repo/.claude/plugins/data-pipeline")
    r.add_skipped("hooks", "agent has no hook mechanism")
    assert r.installed == ["plugin -> /repo/.claude/plugins/data-pipeline"]
    assert r.skipped == [("hooks", "agent has no hook mechanism")]
