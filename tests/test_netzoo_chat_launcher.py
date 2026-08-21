import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]
LAUNCHER = REPO_ROOT / "netzoo-chat"


class NetZooChatLauncherTests(unittest.TestCase):
    def test_active_project_identity_is_netzoo_agent(self):
        compose = (REPO_ROOT / "docker-compose.yml").read_text()
        observer_compose = (REPO_ROOT / "docker-compose.observer.yml").read_text()
        policy = (REPO_ROOT / "AGENTS.md").read_text()

        self.assertIn("name: netzoo_agent", compose)
        self.assertEqual(
            compose.count("image: netzoo_agent:latest")
            + observer_compose.count("image: netzoo_agent:latest"),
            2,
        )
        self.assertNotIn("netzoo-panda-puma", compose)
        self.assertNotIn("network-zoo-panda-puma", compose)
        self.assertIn("project: netzoo_agent", policy)

    def test_launcher_uses_default_state_machine_mode(self):
        source = LAUNCHER.read_text()

        self.assertIn('scripts/netzoo_agent.py "$@"', source)
        self.assertNotIn("--timeline", source)
        self.assertNotIn("--transient-trace", source)

    def test_launcher_supplies_ephemeral_observer_secrets_to_compose(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_bin = tmp_path / "bin"
            fake_bin.mkdir()
            docker = fake_bin / "docker"
            docker.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                ": \"${NETZOO_TEST_OUTPUT:?}\"\n"
                ">\"$NETZOO_TEST_OUTPUT\"\n"
                "for name in NETZOO_OBSERVER_CREDENTIAL_PEPPER NETZOO_OBSERVER_AGENT_KEY "
                "NETZOO_OBSERVER_ADMIN_KEY NETZOO_OBSERVER_DB_PASSWORD "
                "NETZOO_OBSERVER_OBJECT_ACCESS_KEY NETZOO_OBSERVER_OBJECT_SECRET_KEY; do\n"
                "  [[ -n \"${!name:-}\" ]] && echo \"$name=set\" >>\"$NETZOO_TEST_OUTPUT\" || echo \"$name=missing\" >>\"$NETZOO_TEST_OUTPUT\"\n"
                "done\n"
            )
            docker.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            env["NETZOO_TEST_OUTPUT"] = str(tmp_path / "observed.env")
            for name in (
                "NETZOO_OBSERVER_CREDENTIAL_PEPPER",
                "NETZOO_OBSERVER_AGENT_KEY",
                "NETZOO_OBSERVER_ADMIN_KEY",
                "NETZOO_OBSERVER_DB_PASSWORD",
                "NETZOO_OBSERVER_OBJECT_ACCESS_KEY",
                "NETZOO_OBSERVER_OBJECT_SECRET_KEY",
            ):
                env.pop(name, None)

            result = subprocess.run(
                ["bash", str(LAUNCHER)],
                cwd=REPO_ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            observed = (tmp_path / "observed.env").read_text().splitlines()
            self.assertEqual(len(observed), 6)
            self.assertTrue(all(line.endswith("=set") for line in observed))


if __name__ == "__main__":
    unittest.main()
