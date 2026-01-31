"""
Tests for newsletter_generator.py

Tests cover:
- Full orchestration flow (mocked client)
- Content selection integration
- All 5 sections generated
- Subject line and preview text generated
- Markdown formatting
- CLI argument parsing
- Output file naming
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from execution.newsletter_generator import (
    generate_newsletter,
    format_as_markdown,
    save_newsletter,
    NewsletterOutput,
)


class TestNewsletterOutput:
    """Tests for NewsletterOutput dataclass."""

    def test_creates_output(self):
        """Creates NewsletterOutput with all fields."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="DTC Money Minute #1: test",
            preview_text="A preview hook",
            sections={"section_1": "Content"},
            markdown="Full markdown",
            metadata={"key": "value"},
        )

        assert output.issue_number == 1
        assert output.subject_line == "DTC Money Minute #1: test"
        assert output.preview_text == "A preview hook"
        assert output.sections == {"section_1": "Content"}
        assert output.markdown == "Full markdown"
        assert output.metadata == {"key": "value"}

    def test_default_metadata(self):
        """Metadata defaults to empty dict."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="",
            preview_text="",
            sections={},
            markdown="",
        )

        assert output.metadata == {}


class TestFormatAsMarkdown:
    """Tests for format_as_markdown function."""

    def test_includes_subject_comment(self):
        """Markdown includes subject line as comment."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="DTC Money Minute #1: the secret",
            preview_text="Preview here",
            sections={},
            markdown="",
        )

        result = format_as_markdown(output)

        assert "<!-- Subject: DTC Money Minute #1: the secret -->" in result

    def test_includes_preview_comment(self):
        """Markdown includes preview text as comment."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="Subject",
            preview_text="The preview text hook",
            sections={},
            markdown="",
        )

        result = format_as_markdown(output)

        assert "<!-- Preview: The preview text hook -->" in result

    def test_includes_issue_number(self):
        """Markdown includes issue number comment."""
        output = NewsletterOutput(
            issue_number=42,
            subject_line="Subject",
            preview_text="Preview",
            sections={},
            markdown="",
        )

        result = format_as_markdown(output)

        assert "<!-- Issue: 42 -->" in result

    def test_includes_all_sections(self):
        """Markdown includes all sections in order."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="Subject",
            preview_text="Preview",
            sections={
                "section_1": "Section one content",
                "section_2": "Section two content",
                "section_3": "Section three content",
                "section_4": "Section four content",
                "section_5": "PS: Section five",
            },
            markdown="",
        )

        result = format_as_markdown(output)

        # Check all sections present
        assert "Section one content" in result
        assert "Section two content" in result
        assert "Section three content" in result
        assert "Section four content" in result
        assert "PS: Section five" in result

        # Check order (section 1 before 2, etc.)
        assert result.index("Section one") < result.index("Section two")
        assert result.index("Section two") < result.index("Section three")

    def test_sections_separated_by_blank_lines(self):
        """Sections are separated by blank lines."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="Subject",
            preview_text="Preview",
            sections={
                "section_1": "First",
                "section_2": "Second",
            },
            markdown="",
        )

        result = format_as_markdown(output)

        # Should have blank line between sections
        assert "First\n\nSecond" in result

    def test_handles_missing_sections(self):
        """Handles missing sections gracefully."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="Subject",
            preview_text="Preview",
            sections={
                "section_1": "Only first",
                # Missing 2, 3, 4, 5
            },
            markdown="",
        )

        result = format_as_markdown(output)

        assert "Only first" in result
        # Should not error


class TestGenerateNewsletter:
    """Tests for generate_newsletter function."""

    @pytest.fixture
    def mock_all_section_generators(self):
        """Mock all section generators and client."""
        with (
            patch("execution.newsletter_generator.ClaudeClient") as mock_client,
            patch("execution.newsletter_generator.generate_section_1") as mock_s1,
            patch("execution.newsletter_generator.generate_section_2") as mock_s2,
            patch("execution.newsletter_generator.generate_section_3") as mock_s3,
            patch("execution.newsletter_generator.generate_section_4") as mock_s4,
            patch("execution.newsletter_generator.generate_section_5") as mock_s5,
            patch(
                "execution.newsletter_generator.generate_subject_line"
            ) as mock_subject,
            patch(
                "execution.newsletter_generator.generate_preview_text"
            ) as mock_preview,
        ):
            mock_client.return_value = MagicMock()
            mock_s1.return_value = "Section 1 content with instant reward."
            mock_s2.return_value = "Section 2 tactical content " * 50
            mock_s3.return_value = "Section 3 breakdown content " * 30
            mock_s4.return_value = "Section 4 tool recommendation here."
            mock_s5.return_value = "PS: Check out next week's reveal."
            mock_subject.return_value = "DTC Money Minute #1: the secret"
            mock_preview.return_value = (
                "The strategy that changed everything for brands"
            )

            yield {
                "client": mock_client,
                "s1": mock_s1,
                "s2": mock_s2,
                "s3": mock_s3,
                "s4": mock_s4,
                "s5": mock_s5,
                "subject": mock_subject,
                "preview": mock_preview,
            }

    @pytest.fixture
    def sample_content(self):
        """Sample aggregated content."""
        return [
            {
                "title": "How I grew to $50k/mo",
                "summary": "Tactical growth strategy",
                "source": "reddit",
                "outlier_score": 5.5,
            },
            {
                "title": "The email hack that works",
                "summary": "Email marketing tip",
                "source": "youtube",
                "outlier_score": 4.2,
            },
            {
                "title": "My journey from 0 to $1M",
                "summary": "Story of growth",
                "source": "reddit",
                "outlier_score": 3.8,
            },
        ]

    def test_generates_all_sections(self, mock_all_section_generators, sample_content):
        """Generates all 5 sections."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
        )

        assert "section_1" in output.sections
        assert "section_2" in output.sections
        assert "section_3" in output.sections
        assert "section_4" in output.sections
        assert "section_5" in output.sections

    def test_generates_subject_line(self, mock_all_section_generators, sample_content):
        """Generates subject line."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
        )

        assert output.subject_line
        assert "DTC Money Minute #1:" in output.subject_line

    def test_generates_preview_text(self, mock_all_section_generators, sample_content):
        """Generates preview text."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
        )

        assert output.preview_text
        assert len(output.preview_text) > 0

    def test_generates_markdown(self, mock_all_section_generators, sample_content):
        """Generates markdown output."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
        )

        assert output.markdown
        assert "<!-- Subject:" in output.markdown

    def test_tracks_sources_used(self, mock_all_section_generators, sample_content):
        """Tracks which sources were used."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
        )

        assert "sources_used" in output.metadata
        assert isinstance(output.metadata["sources_used"], list)

    def test_tracks_word_counts(self, mock_all_section_generators, sample_content):
        """Tracks word counts per section."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
        )

        assert "word_counts" in output.metadata
        assert "section_1" in output.metadata["word_counts"]

    def test_tracks_generation_time(self, mock_all_section_generators, sample_content):
        """Tracks generation time."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
        )

        assert "generation_time" in output.metadata
        assert output.metadata["generation_time"] >= 0

    def test_uses_tool_info_if_provided(
        self, mock_all_section_generators, sample_content
    ):
        """Uses provided tool_info for Section 4."""
        tool_info = {
            "name": "Klaviyo",
            "description": "Email marketing platform",
            "why_it_helps": "2x email revenue",
        }

        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
            tool_info=tool_info,
        )

        # Section 4 should be generated
        assert "section_4" in output.sections

    def test_uses_placeholder_without_tool_info(
        self, mock_all_section_generators, sample_content
    ):
        """Uses placeholder when no tool_info provided."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
            tool_info=None,
        )

        # Should still generate Section 4
        assert "section_4" in output.sections

    def test_respects_ps_type(self, mock_all_section_generators, sample_content):
        """Passes ps_type to section 5 generator."""
        output = generate_newsletter(
            aggregated_content=sample_content,
            issue_number=1,
            ps_type="cta",
        )

        assert output.metadata.get("ps_type") == "cta"

    def test_handles_empty_content(self, mock_all_section_generators):
        """Handles empty content list."""
        output = generate_newsletter(
            aggregated_content=[],
            issue_number=1,
        )

        # Should still generate (with placeholders)
        assert output.sections


class TestSaveNewsletter:
    """Tests for save_newsletter function."""

    def test_saves_markdown_file(self, tmp_path):
        """Saves newsletter to markdown file."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="Subject",
            preview_text="Preview",
            sections={},
            markdown="# Newsletter Content",
            metadata={},
        )

        filepath = save_newsletter(output, tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".md"
        assert "issue-1" in filepath.name

    def test_saves_metadata_json(self, tmp_path):
        """Saves metadata to JSON file."""
        output = NewsletterOutput(
            issue_number=1,
            subject_line="Subject",
            preview_text="Preview",
            sections={},
            markdown="# Newsletter",
            metadata={"key": "value"},
        )

        save_newsletter(output, tmp_path)

        # Find meta file
        meta_files = list(tmp_path.glob("*-meta.json"))
        assert len(meta_files) == 1

        with open(meta_files[0]) as f:
            data = json.load(f)

        assert data["issue_number"] == 1
        assert data["subject_line"] == "Subject"

    def test_creates_output_dir(self, tmp_path):
        """Creates output directory if it doesn't exist."""
        output_dir = tmp_path / "nested" / "dir"
        output = NewsletterOutput(
            issue_number=1,
            subject_line="Subject",
            preview_text="Preview",
            sections={},
            markdown="# Newsletter",
        )

        filepath = save_newsletter(output, output_dir)

        assert output_dir.exists()
        assert filepath.exists()

    def test_filename_format(self, tmp_path):
        """Filename follows expected format."""
        output = NewsletterOutput(
            issue_number=42,
            subject_line="Subject",
            preview_text="Preview",
            sections={},
            markdown="# Newsletter",
        )

        filepath = save_newsletter(output, tmp_path)

        # Should be {date}-issue-{number}.md
        assert "issue-42" in filepath.name
        assert filepath.suffix == ".md"


class TestCLIArguments:
    """Tests for CLI argument parsing."""

    def test_help_shows_options(self):
        """--help shows all options."""
        import subprocess

        result = subprocess.run(
            ["python", "execution/newsletter_generator.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "--content-file" in result.stdout
        assert "--issue-number" in result.stdout
        assert "--tool-name" in result.stdout
        assert "--ps-type" in result.stdout
        assert "--dry-run" in result.stdout

    def test_requires_content_file(self):
        """Requires --content-file argument."""
        import subprocess

        result = subprocess.run(
            ["python", "execution/newsletter_generator.py", "--issue-number", "1"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode != 0
        assert (
            "content-file" in result.stderr.lower()
            or "required" in result.stderr.lower()
        )

    def test_requires_issue_number(self):
        """Requires --issue-number argument."""
        import subprocess

        result = subprocess.run(
            [
                "python",
                "execution/newsletter_generator.py",
                "--content-file",
                "data.json",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode != 0
        assert (
            "issue-number" in result.stderr.lower()
            or "required" in result.stderr.lower()
        )


class TestIntegration:
    """Integration tests for newsletter generation."""

    @pytest.fixture
    def mock_all_generators(self):
        """Mock all generator functions and content selector."""
        from execution.content_selector import ContentSelection

        # Create a mock selection with content for all sections
        mock_selection = ContentSelection(
            section_1={"title": "Quick stat", "source": "reddit", "outlier_score": 3.0},
            section_2={
                "title": "Tactical how-to",
                "source": "youtube",
                "outlier_score": 4.0,
            },
            section_3={"title": "Deep story", "source": "reddit", "outlier_score": 5.0},
            sources_used=["reddit", "youtube"],
        )

        with (
            patch("execution.newsletter_generator.ClaudeClient") as mock_client,
            patch(
                "execution.newsletter_generator.select_content_for_sections"
            ) as mock_selector,
            patch("execution.newsletter_generator.generate_section_1") as mock_s1,
            patch("execution.newsletter_generator.generate_section_2") as mock_s2,
            patch("execution.newsletter_generator.generate_section_3") as mock_s3,
            patch("execution.newsletter_generator.generate_section_4") as mock_s4,
            patch("execution.newsletter_generator.generate_section_5") as mock_s5,
            patch(
                "execution.newsletter_generator.generate_subject_line"
            ) as mock_subject,
            patch(
                "execution.newsletter_generator.generate_preview_text"
            ) as mock_preview,
        ):
            mock_client.return_value = MagicMock()
            mock_selector.return_value = mock_selection
            mock_s1.return_value = "Section 1 content"
            mock_s2.return_value = "Section 2 content"
            mock_s3.return_value = "Section 3 content"
            mock_s4.return_value = "Section 4 content"
            mock_s5.return_value = "PS: Section 5 content"
            mock_subject.return_value = "DTC Money Minute #1: hook"
            mock_preview.return_value = "Preview text for email"

            yield {
                "client": mock_client,
                "selector": mock_selector,
                "s1": mock_s1,
                "s2": mock_s2,
                "s3": mock_s3,
                "s4": mock_s4,
                "s5": mock_s5,
                "subject": mock_subject,
                "preview": mock_preview,
            }

    def test_calls_all_generators(self, mock_all_generators):
        """Calls all section generators."""
        content = [{"title": "Test", "source": "reddit", "outlier_score": 3.0}]

        generate_newsletter(content, issue_number=1)

        mock_all_generators["s1"].assert_called_once()
        mock_all_generators["s2"].assert_called_once()
        mock_all_generators["s3"].assert_called_once()
        mock_all_generators["s4"].assert_called_once()
        mock_all_generators["s5"].assert_called_once()
        mock_all_generators["subject"].assert_called_once()
        mock_all_generators["preview"].assert_called_once()

    def test_passes_prior_sections_context(self, mock_all_generators):
        """Passes prior sections to later generators."""
        content = [{"title": "Test", "source": "reddit", "outlier_score": 3.0}]

        generate_newsletter(content, issue_number=1)

        # Section 2 should get section 1 context
        s2_call = mock_all_generators["s2"].call_args
        assert "prior_sections" in s2_call.kwargs
        assert "section_1" in s2_call.kwargs["prior_sections"]

        # Section 3 should get sections 1 and 2 context
        s3_call = mock_all_generators["s3"].call_args
        assert "section_1" in s3_call.kwargs["prior_sections"]
        assert "section_2" in s3_call.kwargs["prior_sections"]

    def test_content_selector_integration(self, mock_all_generators):
        """Integrates with content selector."""
        content = [
            {
                "title": "Tactical how-to guide",
                "source": "reddit",
                "outlier_score": 5.0,
            },
            {
                "title": "Quick stat: $1M revenue",
                "source": "youtube",
                "outlier_score": 3.5,
            },
        ]

        generate_newsletter(content, issue_number=1)

        # Should have called generators with selected content
        mock_all_generators["s1"].assert_called_once()
        mock_all_generators["s2"].assert_called_once()
