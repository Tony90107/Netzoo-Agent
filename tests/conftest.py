"""Optional release gate: skipped coverage is not passing coverage."""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--fail-on-skip", action="store_true", default=False,
        help="Fail the selected suite if any test or collection is skipped.",
    )


def pytest_configure(config):
    if config.getoption("--fail-on-skip"):
        config.pluginmanager.register(_SkipGate(), "netzoo-skip-gate")


class _SkipGate:
    def __init__(self):
        self.skipped = set()

    def pytest_collectreport(self, report):
        if report.skipped:
            self.skipped.add(report.nodeid)

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped.add(report.nodeid)

    def pytest_sessionfinish(self, session, exitstatus):
        if self.skipped and exitstatus == pytest.ExitCode.OK:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED

    def pytest_terminal_summary(self, terminalreporter):
        if self.skipped:
            terminalreporter.write_sep("=", f"FAIL: --fail-on-skip detected {len(self.skipped)} skipped items")
