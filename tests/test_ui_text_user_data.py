"""Log 180: agent-authored UI text stays English; quoted user data may not be."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.presentation import _ui_text_with_user_data, user_data_token  # noqa: E402


def test_user_data_may_be_non_english():
    text = f'You said "{user_data_token(0)}" about `{user_data_token(1)}`.'

    assert _ui_text_with_user_data(text, ["少數病人", "資料/"]) == 'You said "少數病人" about `資料/`.'


def test_the_agent_authored_template_is_still_checked():
    with pytest.raises(ValueError, match="must be English"):
        _ui_text_with_user_data(f"根據 {user_data_token(0)}", ["quote"])
