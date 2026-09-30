"""Ground an explicit data-acquisition command before selecting a workflow."""

from __future__ import annotations

import re


def acquisition_request_excluded(task: str) -> bool:
    """A mention of downloading is not an instruction when it is denied or instructional."""
    return bool(
        re.search(r"\bhow\s+(?:do\s+i|can\s+i|to)\b.{0,80}\bdownload\b|(?:如何|怎麼|怎样).{0,80}(?:下載|下载)", task, re.I)
        or re.search(r"不要|不想|別|别|\b(?:do\s+not|don't|not\s+to|without)\s+(?:want\s+to\s+)?(?:download|fetch)\b", task, re.I)
    )


def explicit_acquisition_request(task: str) -> bool:
    """Recognize a clear download command, not a how-to or mixed operation."""
    if not re.search(r"下載|下载|\bdownload\b|\bfetch\b", task, re.I):
        return False
    if not re.search(r"資料|数据|檔案|文件|網路|网络|\b(?:data|dataset|file|network|STRING)\b", task, re.I):
        return False
    if acquisition_request_excluded(task):
        return False
    if re.search(r"推論|推断|分析|執行|执行|\b(?:infer|analy[sz]e|run|execute)\b", task, re.I):
        return False
    return True
