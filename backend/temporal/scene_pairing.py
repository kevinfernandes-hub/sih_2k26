"""Selection of before/after scenes from a geographic timeline."""

from datetime import date
from typing import Optional, Tuple

from .timeline import SceneTimeline


class PairingError(ValueError):
    """Raised when a requested temporal scene pair cannot be selected."""


def pair_scenes(
    timeline: SceneTimeline,
    *,
    mode: str = "latest",
    before_date: Optional[str] = None,
    after_date: Optional[str] = None,
) -> Tuple[object, object]:
    """Return a chronological before/after pair from a timeline.

    Custom dates select the closest available scene on or before each requested
    date, preserving chronology and preventing an after scene before the before
    scene.
    """

    scenes = timeline.scenes
    if len(scenes) < 2:
        raise PairingError("At least two overlapping scenes are required")
    if mode not in {"latest", "previous", "custom"}:
        raise PairingError("Pairing mode must be latest, previous, or custom")
    if mode == "custom":
        if not before_date or not after_date:
            raise PairingError("Custom pairing requires before_date and after_date")
        before = _scene_on_or_before(timeline, before_date)
        after = _scene_on_or_before(timeline, after_date)
    elif mode == "previous":
        before, after = _last_two_date_groups(scenes)
    else:
        before, after = _last_two_date_groups(scenes)
    if date.fromisoformat(before.date) >= date.fromisoformat(after.date):
        raise PairingError("Selected scenes must have increasing dates")
    return before, after


def _last_two_date_groups(scenes):
    dates = sorted({scene.date for scene in scenes})
    if len(dates) < 2:
        raise PairingError("At least two distinct scene dates are required")
    before_date, after_date = dates[-2], dates[-1]
    before = next(scene for scene in scenes if scene.date == before_date)
    after = next(scene for scene in scenes if scene.date == after_date)
    return before, after


def _scene_on_or_before(timeline: SceneTimeline, requested: str):
    requested_date = date.fromisoformat(requested)
    eligible = [scene for scene in timeline.scenes if date.fromisoformat(scene.date) <= requested_date]
    if not eligible:
        raise PairingError("No scene is available on or before " + requested)
    return eligible[-1]