from typing import Any
from unittest.mock import MagicMock, patch

from pipeline.generator import _format_fit_report, _format_narratives, run_generator


def test_format_narratives_empty_list() -> None:
    """Verify formatting handles empty narratives."""
    result = _format_narratives([])
    assert result == "No candidate background narratives available."


def test_format_narratives_with_overview_and_roles() -> None:
    """Verify narratives are formatted into sections."""
    narratives = [
        {
            "title": "Career Overview",
            "content": "10 years in software",
            "category": "career_overview",
        },
        {"title": "Senior Engineer at Acme", "content": "Led team of 5", "category": "role"},
    ]
    result = _format_narratives(narratives)
    assert "## Career Overview" in result
    assert "### Career Overview" in result
    assert "## Role Narratives" in result
    assert "### Senior Engineer at Acme" in result
    assert "10 years in software" in result
    assert "Led team of 5" in result


def test_format_narratives_separates_supplemental_from_roles() -> None:
    """Supplemental narratives get their own section, not the role section."""
    narratives = [
        {"title": "Overview", "content": "10 years", "category": "career_overview"},
        {"title": "Engineer at Acme", "content": "Led team of 5", "category": "work_experience"},
        {"title": "Side Projects", "content": "Built a meetup app", "category": "supplemental"},
    ]
    result = _format_narratives(narratives)

    assert "## Additional Background (not employment — do not list as roles)" in result
    assert "### Side Projects" in result
    assert "Built a meetup app" in result

    # The supplemental narrative must fall outside the role section.
    roles_block = result.split("## Role Narratives")[1].split("## Additional Background")[0]
    assert "Side Projects" not in roles_block
    assert "Engineer at Acme" in roles_block


def test_format_narratives_keeps_unknown_categories_as_roles() -> None:
    """An unrecognized category is treated as a role rather than dropped."""
    narratives: list[dict[str, Any]] = [
        {"title": "Engineer at Acme", "content": "Led team of 5", "category": "role"},
        {"title": "Contractor at Beta", "content": "Shipped a thing", "category": None},
    ]
    result = _format_narratives(narratives)

    assert "## Role Narratives" in result
    assert "### Engineer at Acme" in result
    assert "### Contractor at Beta" in result
    assert "Additional Background" not in result


def test_format_narratives_supplemental_only() -> None:
    """Supplemental-only input renders without an empty role section."""
    narratives = [{"title": "Side Projects", "content": "Built things", "category": "supplemental"}]
    result = _format_narratives(narratives)

    assert "## Additional Background (not employment — do not list as roles)" in result
    assert "## Role Narratives" not in result
    assert "## Career Overview" not in result


def test_format_fit_report_all_sections() -> None:
    """Verify fit report is formatted with all sections."""
    fit_report = {
        "matches": [{"priority": "required", "requirement": "Python", "notes": "primary language"}],
        "gaps": [
            {"type": "soft", "requirement": "Go", "notes": None},
            {"type": "hard", "requirement": "Top secret clearance", "notes": None},
        ],
        "terminology": [{"my_term": "backend", "jd_term": "server-side"}],
    }
    result = _format_fit_report(fit_report)
    assert "MATCHES" in result
    assert "[REQUIRED] Python" in result
    assert "[SOFT] Go" in result
    assert "[HARD] Top secret clearance" in result
    assert "backend → server-side" in result


def test_run_generator_calls_api_and_returns_structured_data() -> None:
    """Verify run_generator calls Anthropic and extracts tool response."""
    mock_response = MagicMock()
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "summary": "Experienced engineer",
        "experience": [],
        "skills": ["Python", "Go"],
    }
    mock_response.content = [mock_tool_block]

    with (
        patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
        patch("pipeline.generator.load_prompt") as mock_load_prompt,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        mock_load_prompt.return_value = "System prompt"

        result = run_generator(
            narratives_text="Narrative text",
            fit_report={"matches": [], "gaps": [], "terminology": []},
            user_id="user-123",
            contact_info=None,
        )

        assert result["summary"] == "Experienced engineer"
        assert result["skills"] == ["Python", "Go"]
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-5"
        assert call_kwargs["max_tokens"] == 8192
