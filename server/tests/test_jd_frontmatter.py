"""JDs clipped from a browser extension arrive with YAML frontmatter attached.

Left in place it does three things, in increasing order of severity: it makes
the derived title literally `title: "..."`, it feeds ~250 chars of `tags:`
and `source:` noise to the model as job-description prose, and — verified by
controlled test in #48 — it destabilises the model's tool-call serialisation
badly enough to fail the fit stage outright (0/2 with it, 2/2 without).

The clipper's leading `---` is frequently lost when the text is copied out of
an editor, so the unfenced form has to be handled too, without mistaking a
markdown horizontal rule for a frontmatter terminator.
"""

from typing import Any

from db.job_descriptions import derive_title, strip_frontmatter

FENCED = """---
title: "Senior Frontend Engineer"
source: "https://example.com/jobs/1"
tags:
  - "clippings"
---

Acme Corp is hiring a frontend engineer.

Responsibilities:
- Build things
"""

# Leading `---` lost on copy — the shape actually observed in the DB.
UNFENCED = """title: "Senior Front End Software Engineer, React"
source: "https://job-boards.greenhouse.io/example/jobs/123"
author:
published:
created: 2026-07-26
description: "Seattle, Washington, United States"
tags:
  - "clippings"
---
Anduril Industries is a defense technology company with a mission to transform
U.S. and allied military capabilities with advanced technology.
"""

PLAIN = """Staff Software Engineer, Claude Code — Anthropic

We're looking for a Software Engineer to help us build agentic coding tools.
"""

# A horizontal rule in the body must not be read as a frontmatter terminator.
HORIZONTAL_RULE = """Senior Engineer at Foo

Responsibilities:
- Build things

---

Apply at example.com
"""


class TestStripFrontmatter:
    def test_fenced_block_is_removed_and_metadata_returned(self) -> None:
        body, meta = strip_frontmatter(FENCED)

        assert body.startswith("Acme Corp is hiring")
        assert "clippings" not in body
        assert "source:" not in body
        assert meta["title"] == "Senior Frontend Engineer"

    def test_unfenced_block_missing_its_opening_delimiter_is_removed(self) -> None:
        body, meta = strip_frontmatter(UNFENCED)

        assert body.startswith("Anduril Industries is a defense technology company")
        assert "greenhouse.io" not in body
        assert "clippings" not in body
        assert meta["title"] == "Senior Front End Software Engineer, React"

    def test_plain_prose_is_returned_unchanged(self) -> None:
        body, meta = strip_frontmatter(PLAIN)

        assert body == PLAIN
        assert meta == {}

    def test_a_horizontal_rule_is_not_treated_as_a_terminator(self) -> None:
        body, meta = strip_frontmatter(HORIZONTAL_RULE)

        assert body == HORIZONTAL_RULE
        assert meta == {}

    def test_empty_content_is_safe(self) -> None:
        assert strip_frontmatter("") == ("", {})


class TestDeriveTitle:
    def test_prefers_the_frontmatter_title_over_the_first_body_line(self) -> None:
        assert derive_title(UNFENCED) == "Senior Front End Software Engineer, React"

    def test_fenced_frontmatter_title_is_used(self) -> None:
        assert derive_title(FENCED) == "Senior Frontend Engineer"

    def test_falls_back_to_the_first_body_line_without_frontmatter(self) -> None:
        assert derive_title(PLAIN) == "Staff Software Engineer, Claude Code — Anthropic"

    def test_never_returns_a_raw_frontmatter_key(self) -> None:
        title = derive_title(UNFENCED)

        assert title is not None
        assert not title.startswith("title:")
        assert '"' not in title


class TestCreateJdPersistsTheBody:
    """The model must never receive the frontmatter — that is what breaks #48."""

    def test_inserted_content_is_the_body_and_title_comes_from_frontmatter(self) -> None:
        from unittest.mock import MagicMock, patch

        from db import job_descriptions

        captured: dict[str, Any] = {}

        def capture(payload: dict[str, Any]) -> MagicMock:
            captured.update(payload)
            execute = MagicMock()
            execute.execute.return_value = MagicMock(data=[{"id": "jd-1", **payload}])
            return execute

        client = MagicMock()
        client.table.return_value.insert.side_effect = capture

        with patch.object(job_descriptions, "get_client", return_value=client):
            job_descriptions.create_jd(UNFENCED, "user-1")

        assert captured["content"].startswith("Anduril Industries is a defense")
        assert "clippings" not in captured["content"]
        assert "greenhouse.io" not in captured["content"]
        assert captured["title"] == "Senior Front End Software Engineer, React"
