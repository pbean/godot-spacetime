"""
Story 6.5: Communicate Release Changes and Maintain Support Continuity
Static existence and content verification tests for all deliverables,
plus regression guards for Epic 6 artifacts from stories 6.1–6.4.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_PROCESS = ROOT / "docs" / "release-process.md"
INSTALL_DOC = ROOT / "docs" / "install.md"
CHANGELOG_TEXT = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else ""
RELEASE_PROCESS_TEXT = (
    RELEASE_PROCESS.read_text(encoding="utf-8") if RELEASE_PROCESS.exists() else ""
)
INSTALL_TEXT = INSTALL_DOC.read_text(encoding="utf-8") if INSTALL_DOC.exists() else ""


# ── Task 4.1: Existence tests ────────────────────────────────────────────────

def test_changelog_exists():
    assert CHANGELOG.exists(), "CHANGELOG.md must exist at the repo root"


def test_release_process_exists():
    assert RELEASE_PROCESS.exists(), "docs/release-process.md must exist"


# ── Task 4.2: CHANGELOG content tests ───────────────────────────────────────


def test_changelog_has_initial_version():
    assert "[0.1.0-dev]" in CHANGELOG_TEXT


def test_changelog_has_unreleased_section():
    assert "[Unreleased]" in CHANGELOG_TEXT


def test_changelog_references_compatibility_matrix():
    assert "compatibility-matrix" in CHANGELOG_TEXT.lower()


def test_changelog_has_migration_section():
    assert "migration" in CHANGELOG_TEXT.lower()


def test_changelog_uses_keep_a_changelog_format():
    assert "keepachangelog" in CHANGELOG_TEXT.lower()


def test_changelog_has_added_section_header():
    assert "### Added" in CHANGELOG_TEXT


def test_changelog_has_compatibility_section_header():
    assert "### Compatibility" in CHANGELOG_TEXT


def test_changelog_has_migration_section_header():
    assert "### Migration" in CHANGELOG_TEXT


def test_changelog_has_semver_reference():
    assert "Semantic Versioning" in CHANGELOG_TEXT


def test_changelog_has_release_date():
    assert "2026-04-15" in CHANGELOG_TEXT


def test_changelog_has_unreleased_footer_link():
    assert (
        "[Unreleased]: https://github.com/clockworklabs/godot-spacetime/compare/v0.1.0-dev...HEAD"
        in CHANGELOG_TEXT
    )


def test_changelog_has_release_footer_link():
    assert (
        "[0.1.0-dev]: https://github.com/clockworklabs/godot-spacetime/releases/tag/v0.1.0-dev"
        in CHANGELOG_TEXT
    )


def test_changelog_migration_section_references_migration_guide():
    """AC1: migration action must point adopters to the migration guide."""
    assert "migration-from-community-plugin.md" in CHANGELOG_TEXT


# ── Task 4.3: Release-process content tests ─────────────────────────────────


def test_release_process_references_compatibility_matrix():
    assert "compatibility-matrix" in RELEASE_PROCESS_TEXT


def test_release_process_references_changelog():
    assert "CHANGELOG" in RELEASE_PROCESS_TEXT


def test_release_process_has_initial_version_row():
    assert "0.1.0-dev" in RELEASE_PROCESS_TEXT


def test_release_process_references_package_script():
    assert "package-release" in RELEASE_PROCESS_TEXT


def test_release_process_references_validate_script():
    assert "validate-release-candidate" in RELEASE_PROCESS_TEXT


def test_release_process_references_publish_script():
    assert "publish-release" in RELEASE_PROCESS_TEXT


def test_release_process_references_github_releases():
    assert "GitHub Releases" in RELEASE_PROCESS_TEXT


def test_release_process_has_release_checklist_section():
    assert "## Release Checklist" in RELEASE_PROCESS_TEXT


def test_release_process_has_canonical_sources_section():
    assert "## Canonical Sources" in RELEASE_PROCESS_TEXT


def test_release_process_has_release_history_section():
    assert "## Release History" in RELEASE_PROCESS_TEXT


def test_release_process_release_history_has_communication_step_column():
    """AC3: the Release History table must record the communication step used per version."""
    assert "Communication Step" in RELEASE_PROCESS_TEXT


def test_release_process_has_exact_initial_release_history_row():
    assert (
        "| 0.1.0-dev | 2026-04-15 | CHANGELOG.md (§ Added, § Compatibility, § Migration) "
        "+ GitHub Release notes via publish-release.py |"
        in RELEASE_PROCESS_TEXT
    )


def test_release_process_references_release_validation_workflow():
    assert ".github/workflows/release-validation.yml" in RELEASE_PROCESS_TEXT


def test_release_process_references_release_workflow():
    assert ".github/workflows/release.yml" in RELEASE_PROCESS_TEXT


def test_release_process_mentions_auto_populated_github_release_notes():
    assert "GitHub Release notes are auto-populated by `publish-release.py`" in RELEASE_PROCESS_TEXT


def test_release_process_does_not_claim_repository_history_generated_notes():
    assert "from the repository history" not in RELEASE_PROCESS_TEXT


# ── Task 4.4: install.md reference tests ────────────────────────────────────

def test_install_md_references_compatibility_matrix():
    assert "compatibility-matrix" in INSTALL_TEXT


def test_install_md_compatibility_matrix_in_foundation_baseline_section():
    """Verifies the compatibility-matrix reference lands in the Supported Foundation Baseline section."""
    section_start = INSTALL_TEXT.find("## Supported Foundation Baseline")
    assert section_start != -1, "Supported Foundation Baseline section must exist"
    next_section = INSTALL_TEXT.find("\n##", section_start + 1)
    section_text = INSTALL_TEXT[section_start:next_section] if next_section != -1 else INSTALL_TEXT[section_start:]
    assert "compatibility-matrix.md" in section_text, (
        "compatibility-matrix.md must be referenced in the Supported Foundation Baseline section"
    )


def test_install_md_compatibility_matrix_in_see_also_section():
    """Verifies the compatibility-matrix reference is present in the See Also section."""
    see_also_start = INSTALL_TEXT.find("## See Also")
    assert see_also_start != -1, "See Also section must exist"
    assert "compatibility-matrix.md" in INSTALL_TEXT[see_also_start:], (
        "compatibility-matrix.md must be listed in the See Also section"
    )


# ── Task 4.5: Regression guards for stories 6.1–6.4 ─────────────────────────

def test_regression_compatibility_matrix_exists():
    assert (ROOT / "docs" / "compatibility-matrix.md").exists()


def test_regression_package_release_script_exists():
    assert (ROOT / "scripts" / "packaging" / "package-release.py").exists()


def test_regression_validate_release_candidate_script_exists():
    assert (ROOT / "scripts" / "packaging" / "validate-release-candidate.py").exists()


def test_regression_publish_release_script_exists():
    assert (ROOT / "scripts" / "packaging" / "publish-release.py").exists()


def test_regression_release_validation_workflow_exists():
    assert (ROOT / ".github" / "workflows" / "release-validation.yml").exists()


def test_regression_release_workflow_exists():
    assert (ROOT / ".github" / "workflows" / "release.yml").exists()


def test_regression_support_baseline_json_exists():
    assert (ROOT / "scripts" / "compatibility" / "support-baseline.json").exists()


def test_regression_validate_foundation_script_exists():
    assert (ROOT / "scripts" / "compatibility" / "validate-foundation.py").exists()


def test_regression_install_md_exists():
    assert (ROOT / "docs" / "install.md").exists()


def test_regression_migration_guide_exists():
    assert (ROOT / "docs" / "migration-from-community-plugin.md").exists()
