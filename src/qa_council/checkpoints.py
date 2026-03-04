"""Checkpoint system — pause execution for human review at configured points."""

from __future__ import annotations

from enum import Enum
from typing import Optional


class CheckpointLevel(Enum):
    """Checkpoint verbosity levels."""

    NONE = "none"  # Never pause
    PHASE = "phase"  # Pause after every major phase
    CRITICAL = "critical"  # Pause only at critical decision points
    FULL = "full"  # Pause after every task

    @classmethod
    def from_string(cls, value: str) -> CheckpointLevel:
        """Parse a checkpoint level from string."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.CRITICAL


# Which phases trigger checkpoints at each level
CHECKPOINT_TRIGGERS = {
    CheckpointLevel.NONE: set(),
    CheckpointLevel.CRITICAL: {
        "after_recon",  # After Scout's initial exploration
        "after_strategy",  # After test strategy is designed
    },
    CheckpointLevel.PHASE: {
        "after_recon",
        "after_critique_recon",
        "after_strategy",
        "after_critique_strategy",
        "after_implementation",
        "after_critique_code",
    },
    CheckpointLevel.FULL: {
        "after_recon",
        "after_critique_recon",
        "after_revised_recon",
        "after_strategy",
        "after_critique_strategy",
        "after_implementation",
        "after_critique_code",
        "after_fix",
        "after_report",
    },
}


class CheckpointManager:
    """Manages checkpoint pauses during council execution.

    Usage:
        manager = CheckpointManager(level="critical")
        # ... after each phase ...
        manager.check("after_recon", summary="Scout found 15 endpoints...")
    """

    def __init__(self, level: str = "critical"):
        self.level = CheckpointLevel.from_string(level)
        self.triggers = CHECKPOINT_TRIGGERS[self.level]
        self.history: list[dict] = []

    def should_pause(self, phase: str) -> bool:
        """Check if execution should pause at this phase."""
        return phase in self.triggers

    def check(self, phase: str, summary: str = "") -> Optional[str]:
        """Check if we should pause, and if so, prompt the user.

        Args:
            phase: The checkpoint identifier (e.g., "after_recon").
            summary: Brief summary of what happened in this phase.

        Returns:
            User's response if paused, None if skipped.
        """
        self.history.append({"phase": phase, "summary": summary})

        if not self.should_pause(phase):
            return None

        return self._prompt_user(phase, summary)

    def _prompt_user(self, phase: str, summary: str) -> str:
        """Display checkpoint info and prompt for user input."""
        phase_label = phase.replace("_", " ").replace("after ", "After ").title()

        print("\n" + "=" * 60)
        print(f"⏸️  CHECKPOINT: {phase_label}")
        print("=" * 60)

        if summary:
            print(f"\n📋 Summary:\n{summary}\n")

        print("Options:")
        print("  [Enter] Continue to next phase")
        print("  [s]     Skip remaining checkpoints")
        print("  [q]     Quit the session")
        print()

        try:
            response = input("Your choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = "q"

        if response == "s":
            self.level = CheckpointLevel.NONE
            self.triggers = set()
            print("⏩ Checkpoints disabled — running to completion.")
        elif response == "q":
            print("🛑 Session ended by user.")
            raise SystemExit(0)

        return response

    def get_summary(self) -> str:
        """Get a summary of all checkpoints hit during the session."""
        if not self.history:
            return "No checkpoints recorded."

        lines = [f"Checkpoint Level: {self.level.value}", ""]
        for entry in self.history:
            paused = "⏸️" if entry["phase"] in self.triggers else "⏩"
            lines.append(f"  {paused} {entry['phase']}: {entry['summary'][:80]}")
        return "\n".join(lines)
