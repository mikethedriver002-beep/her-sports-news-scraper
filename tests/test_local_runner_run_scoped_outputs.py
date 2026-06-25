from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WRAPPER = REPO / "hsd.ps1"
RUNNER = REPO / "scripts" / "hsd_local.ps1"
DOC = REPO / "LOCAL_DEVELOPMENT.md"


def test_local_runner_creates_run_scoped_output_context() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert "function New-HsdRunContext" in text
    assert "function Resolve-HsdArtifactSource" in text
    assert "outputs\\local\\$stamp" in text
    assert "generated_state" in text
    assert "generated_state_manifest.json" in text
    assert "local_run_manifest.json" in text
    assert "$env:HSD_LOCAL_RUN_ROOT" in text
    assert "$env:HSD_RUN_OUTPUT_DIR" in text
    assert '$env:HSD_OUTPUT_MODE = "run_scoped_local"' in text
    assert "function Test-HsdPreserveGeneratedPath" in text


def test_local_runner_archives_generated_state_before_root_restore() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    finally_block = text[text.index("    } finally {") : text.index("function Open-Dashboard")]

    assert "Copy-HsdGeneratedRunState $runContext $generatedBaseline" in finally_block
    assert "Collect-HsdArtifacts $runContext" in finally_block
    assert "Restore-GeneratedGitState $generatedBaseline" in finally_block
    assert finally_block.index("Copy-HsdGeneratedRunState") < finally_block.index("Collect-HsdArtifacts")
    assert finally_block.index("Collect-HsdArtifacts") < finally_block.index("Restore-GeneratedGitState")


def test_generated_state_quarantine_preserves_run_output_folder() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    remove_function = text[text.index("function Remove-GeneratedUntrackedFiles") : text.index("function Restore-GeneratedGitState")]

    assert 'StartsWith("outputs/local/", [StringComparison]::OrdinalIgnoreCase)' in remove_function
    assert "continue" in remove_function


def test_generated_state_quarantine_covers_daily_pipeline_outputs() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    required_pathspecs = [
        "operator_command_center.*",
        "render_prep_packets.*",
        "render_handoff_top_packet/**",
        "manual_review_renderer_*",
        "manual_visual_qa_*",
        "manual_visual_qa_approval_intake.*",
        "manual_post_approval_render_staging.*",
        "publish_guard_report.*",
        "results_desk_v5_manifest.json",
        "results_dashboard/**",
        "studio_dashboard/**",
        "news_dashboard/**",
        "news_fact_packets.csv",
        "studio_bundle_*",
        "bebe_*",
        "manual_workflow_*",
        "source_coverage_map.csv",
        "source_registry_audit.*",
        "source_registry_intake_template.*",
        "source_registry_proposal_review.*",
        "source_registry_proposal_draft.*",
        "source_registry_proposal_promotion_checklist.*",
        "source_registry_update_worksheet.*",
        "source_registry_diff_review.*",
        "source_registry_same_domain_resolution.*",
        "source_registry_verification_log.*",
        "source_registry_approval_packet.*",
        "source_registry_patch_preview.*",
        "source_registry_post_edit_validation.*",
        "trusted_registry_operator_playbook.md",
        "source_proposal_pack_readiness.*",
        "source_proposal_packs.*",
        "*_source_proposal_pack.*",
        "pwhl_source_proposal_pack.*",
        "morning_source_discovery_board.*",
        "morning_lead_promotion_recommendations.*",
        "hsd_pipeline_lite_review/**",
        "outputs/latest/**",
        "assets/leagues/wnba/athletes/*/headshot.png",
        "config/hsd_expected_games_v5.csv",
    ]

    for pathspec in required_pathspecs:
        assert f'"{pathspec}"' in text


def test_local_run_manifest_preserves_free_manual_policy() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert 'output_mode = "run_scoped_local"' in text
    assert "Resolve-HsdArtifactSource $Relative $DestinationDir" in text
    assert "$env:HSD_RUN_OUTPUT_DIR" in text
    assert "manual_only = $true" in text
    assert "paid_apis_disabled = $true" in text
    assert '$env:HSD_PAID_APIS_DISABLED = "1"' in text
    assert '$env:HSD_SOURCE_COST_MODE = "free_first"' in text


def test_review_stage_refreshes_source_registry_audit_for_command_center() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    review_stage = runner[runner.index("function Invoke-ReviewStage") : runner.index("function Resolve-HsdArtifactSource")]
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_source_registry_audit_v2.py" -Optional' in review_stage
    assert 'Invoke-ScriptIfPresent $Python "normalize_hsd_manual_story_inbox_v1.py" -Optional' in review_stage
    assert 'Invoke-ScriptIfPresent $Python "ingest_hsd_discovery_sources_v1.py" -Optional' in review_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_morning_source_discovery_board_v1.py" -Optional' in review_stage
    assert "source_registry_audit.csv" in runner
    assert "source_registry_audit.md" in runner
    assert "source_registry_audit.json" in runner
    assert "source_coverage_map.csv" in runner
    assert "source_registry_intake_template.md" in runner
    assert "source_registry_intake_template.csv" in runner
    assert "source_registry_proposal_review.md" in runner
    assert "source_registry_proposal_review.csv" in runner
    assert "source_registry_proposal_draft.md" in runner
    assert "source_registry_proposal_draft.csv" in runner
    assert "source_registry_proposal_promotion_checklist.md" in runner
    assert "source_registry_proposal_promotion_checklist.csv" in runner
    assert "source_registry_update_worksheet.md" in runner
    assert "source_registry_update_worksheet.csv" in runner
    assert "source_registry_diff_review.md" in runner
    assert "source_registry_diff_review.csv" in runner
    assert "source_registry_same_domain_resolution.md" in runner
    assert "source_registry_same_domain_resolution.csv" in runner
    assert "source_registry_verification_log.md" in runner
    assert "source_registry_verification_log.csv" in runner
    assert "source_registry_approval_packet.md" in runner
    assert "source_registry_approval_packet.csv" in runner
    assert "source_registry_patch_preview.md" in runner
    assert "source_registry_patch_preview.csv" in runner
    assert "source_registry_post_edit_validation.md" in runner
    assert "source_registry_post_edit_validation.csv" in runner
    assert "trusted_registry_operator_playbook.md" in runner
    assert "source_proposal_pack_readiness.md" in runner
    assert "source_proposal_pack_readiness.csv" in runner
    assert "source_proposal_packs.md" in runner
    assert "source_proposal_packs.csv" in runner
    assert "wnba_source_proposal_pack.md" in runner
    assert "wnba_source_proposal_pack.csv" in runner
    assert "nwsl_source_proposal_pack.md" in runner
    assert "nwsl_source_proposal_pack.csv" in runner
    assert "lpga_source_proposal_pack.md" in runner
    assert "lpga_source_proposal_pack.csv" in runner
    assert "pwhl_source_proposal_pack.md" in runner
    assert "pwhl_source_proposal_pack.csv" in runner
    assert "manual_story_inbox_report.md" in runner
    assert "story_candidates_manual.csv" in runner
    assert "story_candidates_manual.jsonl" in runner
    assert "discovery_sources_report.md" in runner
    assert "story_candidates_discovery.csv" in runner
    assert "story_candidates_discovery.jsonl" in runner
    assert "morning_source_discovery_board.csv" in runner
    assert "morning_source_discovery_board.md" in runner
    assert "morning_source_discovery_board.json" in runner
    assert "morning_lead_promotion_recommendations.csv" in runner
    assert "morning_lead_promotion_recommendations.md" in runner
    assert "morning_lead_promotion_recommendations.json" in runner
    assert "source registry audit, operator status" in doc
    assert "morning source discovery board" in doc


def test_manual_render_mode_is_explicit_review_only() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    render_stage = runner[runner.index("function Invoke-RenderStage") : runner.index("function Invoke-DecisionInboxStarterStage")]

    assert '"render"' in wrapper
    assert '"decision-inbox"' in wrapper
    assert "function Invoke-RenderStage" in runner
    assert "function Invoke-DecisionInboxStarterStage" in runner
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_review_renderer_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_visual_qa_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_visual_qa_approval_intake_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_visual_qa_operator_decision_draft_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_visual_qa_operator_decision_template_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_visual_qa_operator_decision_intake_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_post_approval_render_staging_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_visual_qa_operator_decision_walkthrough_v1.py" -Optional' in render_stage
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_operator_command_center_v2.py" -Optional' in render_stage
    assert render_stage.index('Invoke-ScriptIfPresent $Python "generate_hsd_manual_visual_qa_operator_decision_walkthrough_v1.py" -Optional') < render_stage.index('Invoke-ScriptIfPresent $Python "generate_hsd_operator_command_center_v2.py" -Optional')
    assert 'Invoke-ScriptIfPresent $Python "create_hsd_manual_visual_qa_operator_decision_inbox_starter_v1.py" -Optional' in runner
    assert '$env:HSD_EXPLICIT_OPERATOR_INBOX_STARTER = "1"' in runner
    assert '"decision-inbox" { Invoke-DecisionInboxStarterStage $python }' in runner
    assert 'operator/inbox/manual_visual_qa_operator_decisions.csv' in runner
    assert '"render" { Invoke-RenderStage $python }' in runner
    assert "render_handoff_top_packet/draft_preview.png" in runner
    assert "manual_review_renderer_report.md" in runner
    assert "manual_review_renderer_manifest.json" in runner
    assert "manual_visual_qa_report.md" in runner
    assert "manual_visual_qa_manifest.json" in runner
    assert "manual_visual_qa_checklist.csv" in runner
    assert "manual_visual_qa_approval_intake.md" in runner
    assert "manual_visual_qa_approval_intake.csv" in runner
    assert "manual_visual_qa_approval_intake.json" in runner
    assert "manual_visual_qa_operator_decision_draft.md" in runner
    assert "manual_visual_qa_operator_decision_draft.csv" in runner
    assert "manual_visual_qa_operator_decision_draft.json" in runner
    assert "manual_visual_qa_operator_decision_template.md" in runner
    assert "manual_visual_qa_operator_decision_template.csv" in runner
    assert "manual_visual_qa_operator_decision_template.json" in runner
    assert "manual_visual_qa_operator_decision_intake.md" in runner
    assert "manual_visual_qa_operator_decision_intake.csv" in runner
    assert "manual_visual_qa_operator_decision_intake.json" in runner
    assert "manual_post_approval_render_staging.md" in runner
    assert "manual_post_approval_render_staging.csv" in runner
    assert "manual_post_approval_render_staging.json" in runner
    assert "manual_visual_qa_operator_decision_walkthrough.md" in runner
    assert "manual_visual_qa_operator_decision_walkthrough.csv" in runner
    assert "manual_visual_qa_operator_decision_walkthrough.json" in runner
    assert "manual_visual_qa_operator_decision_inbox_starter.md" in runner
    assert "manual_visual_qa_operator_decision_inbox_starter.csv" in runner
    assert "manual_visual_qa_operator_decision_inbox_starter.json" in runner
    assert ".\\hsd.cmd run -Mode render" in doc
    assert ".\\hsd.cmd run -Mode decision-inbox" in doc


def test_legacy_scraper_is_retired_from_active_local_runner() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert '"scraper"' not in runner
    assert "womens_sports_scraper.py" not in runner
    assert "generate_hsd_dashboard.py" not in runner
    assert '"scraper"' not in wrapper
    assert "no longer an active local runner mode" in doc


def test_manual_handoff_mode_is_explicit_and_run_scoped() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert '"handoff"' in wrapper
    assert '"handoff"' in runner
    assert "function Invoke-HandoffStage" in runner
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_manual_workflow_merge_v1.py" -Optional' in runner
    assert '"handoff" { Invoke-HandoffStage $python; Invoke-ReviewStage $python }' in runner
    assert "manual inbox to handoff packs" in doc


def test_final_score_stories_mode_is_explicit_and_run_scoped() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert '"stories"' in wrapper
    assert '"stories"' in runner
    assert "function Invoke-StoriesStage" in runner
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_final_score_stories_v1.py" -Optional' in runner
    assert '"stories" { Invoke-StoriesStage $python; Invoke-ReviewStage $python }' in runner
    assert "ig_story_results_queue.csv" in runner
    assert "final-score IG Story packs" in doc


def test_multi_post_mode_is_explicit_and_run_scoped() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert '"posts"' in wrapper
    assert '"posts"' in runner
    assert "function Invoke-PostsStage" in runner
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_multi_post_desk_v1.py" -Optional' in runner
    assert '"posts" { Invoke-PostsStage $python; Invoke-ReviewStage $python }' in runner
    assert "multi_post_daily_board.md" in runner
    assert "post_slot_status.csv" in runner
    assert "multi-post daily board" in doc


def test_launch_mode_is_explicit_and_run_scoped() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert '"launch"' in wrapper
    assert '"launch"' in runner
    assert "function Invoke-LaunchStage" in runner
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_launch_control_v1.py" -Optional' in runner
    assert '"launch" { Invoke-LaunchStage $python; Invoke-ReviewStage $python }' in runner
    assert "launch_command_center.md" in runner
    assert "launch_instagram_publish_queue.csv" in runner
    assert "Launch Control runbook" in doc


def test_drilldown_dashboards_mode_is_explicit_and_run_scoped() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert '"dashboards"' in wrapper
    assert '"dashboards"' in runner
    assert "function Invoke-DrilldownDashboardsStage" in runner
    assert 'Invoke-ScriptIfPresent $Python "generate_results_dashboard_v4.py" -Optional' in runner
    assert 'Invoke-ScriptIfPresent $Python "generate_hsd_studio_dashboard_v1.py" -Optional' in runner
    assert '"dashboards" { Invoke-DrilldownDashboardsStage $python; Invoke-ReviewStage $python }' in runner
    assert '"results_dashboard/index.html"' in runner
    assert '"studio_dashboard/index.html"' in runner
    assert "run -Mode dashboards" in doc
    assert "It does not publish, call paid APIs, or run as part of `full`." in doc


def test_local_development_docs_describe_run_scoped_outputs() -> None:
    doc = DOC.read_text(encoding="utf-8")

    assert "outputs/local/<timestamp>/files/" in doc
    assert "outputs/local/<timestamp>/generated_state/" in doc
    assert "generated_state_manifest.json" in doc
    assert "-KeepGeneratedState" in doc
