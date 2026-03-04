"""Tests for the checkpoint system."""

from qa_council.checkpoints import CheckpointManager, CheckpointLevel


class TestCheckpointLevel:
    """Tests for CheckpointLevel enum."""

    def test_from_valid_string(self):
        assert CheckpointLevel.from_string("none") == CheckpointLevel.NONE
        assert CheckpointLevel.from_string("phase") == CheckpointLevel.PHASE
        assert CheckpointLevel.from_string("critical") == CheckpointLevel.CRITICAL
        assert CheckpointLevel.from_string("full") == CheckpointLevel.FULL

    def test_from_string_case_insensitive(self):
        assert CheckpointLevel.from_string("CRITICAL") == CheckpointLevel.CRITICAL

    def test_from_unknown_string_defaults_to_critical(self):
        assert CheckpointLevel.from_string("unknown") == CheckpointLevel.CRITICAL


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    def test_none_level_never_pauses(self):
        mgr = CheckpointManager(level="none")
        assert not mgr.should_pause("after_recon")
        assert not mgr.should_pause("after_strategy")
        assert not mgr.should_pause("after_implementation")

    def test_critical_level_pauses_at_key_points(self):
        mgr = CheckpointManager(level="critical")
        assert mgr.should_pause("after_recon")
        assert mgr.should_pause("after_strategy")
        assert not mgr.should_pause("after_critique_code")
        assert not mgr.should_pause("after_report")

    def test_phase_level_pauses_at_all_phases(self):
        mgr = CheckpointManager(level="phase")
        assert mgr.should_pause("after_recon")
        assert mgr.should_pause("after_critique_recon")
        assert mgr.should_pause("after_strategy")
        assert mgr.should_pause("after_implementation")

    def test_full_level_pauses_at_everything(self):
        mgr = CheckpointManager(level="full")
        assert mgr.should_pause("after_recon")
        assert mgr.should_pause("after_revised_recon")
        assert mgr.should_pause("after_fix")
        assert mgr.should_pause("after_report")

    def test_check_skips_when_not_triggered(self):
        mgr = CheckpointManager(level="none")
        result = mgr.check("after_recon", summary="Found 10 endpoints")
        assert result is None
        assert len(mgr.history) == 1

    def test_history_records_all_checks(self):
        mgr = CheckpointManager(level="none")
        mgr.check("after_recon", summary="Found 10 endpoints")
        mgr.check("after_strategy", summary="Planned 20 tests")
        assert len(mgr.history) == 2
        assert mgr.history[0]["phase"] == "after_recon"
        assert mgr.history[1]["summary"] == "Planned 20 tests"

    def test_get_summary(self, monkeypatch):
        mgr = CheckpointManager(level="critical")
        monkeypatch.setattr("builtins.input", lambda _: "")
        mgr.check("after_recon", summary="Found endpoints")
        summary = mgr.get_summary()
        assert "critical" in summary
        assert "after_recon" in summary
