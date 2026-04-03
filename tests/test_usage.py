import json
import pytest
from src.usage import UsageTracker, MILESTONES


class TestUsageTracker:
    def test_starts_at_zero(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        assert tracker.total_uses == 0

    def test_increment_persists(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker.increment()
        tracker.increment()
        assert tracker.total_uses == 2

        # Reload from disk
        tracker2 = UsageTracker(data_dir=str(tmp_path))
        assert tracker2.total_uses == 2

    def test_no_prompt_before_first_milestone(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        for _ in range(499):
            tracker.increment()
        assert tracker.should_prompt() is False

    def test_prompt_at_500(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        assert tracker.should_prompt() is True

    def test_no_double_prompt_at_same_milestone(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        assert tracker.should_prompt() is True
        tracker.mark_prompted()
        assert tracker.should_prompt() is False

    def test_prompt_at_1500(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 1500
        tracker._data["last_prompt_at"] = 500
        tracker._save()
        assert tracker.should_prompt() is True

    def test_dismissed_forever_suppresses(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        tracker.dismiss_forever()
        assert tracker.should_prompt() is False

    def test_get_milestone_message(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 500
        tracker._save()
        msg = tracker.get_prompt_message()
        assert "500" in msg
        assert "coffee" in msg.lower() or "tool" in msg.lower()

    def test_milestones_are_ordered(self):
        assert MILESTONES == sorted(MILESTONES)

    def test_recurring_milestones_after_5000(self, tmp_path):
        tracker = UsageTracker(data_dir=str(tmp_path))
        tracker._data["total_uses"] = 10000
        tracker._data["last_prompt_at"] = 5000
        tracker._save()
        assert tracker.should_prompt() is True
