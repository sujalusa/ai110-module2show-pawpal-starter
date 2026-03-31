"""Core logic layer for PawPal+ backend classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OwnerProfile:
    """Represents the pet owner's preferences and constraints."""

    owner_name: str
    contact_info: str
    daily_time_budget: int
    preference_tags: List[str] = field(default_factory=list)

    def update_preferences(self, tags: List[str]) -> None:
        """Refresh the owner's stored preference tags."""

    def calculate_available_minutes(self, commitments: Optional[List[int]] = None) -> int:
        """Return minutes available after subtracting other commitments."""

    def summarize_context(self) -> str:
        """Provide a one-line summary of the owner's constraints."""


@dataclass
class PetProfile:
    """Contains per-pet details that influence scheduling."""

    pet_name: str
    species: str
    age: int
    care_notes: List[str] = field(default_factory=list)
    linked_tasks: List[str] = field(default_factory=list)

    def add_task_reference(self, task_id: str) -> None:
        """Associate a task identifier with this pet."""

    def needs_summary(self) -> str:
        """Summarize key needs for scheduling explanations."""

    def sync_with_owner(self, owner: OwnerProfile) -> None:
        """Align the pet care plan with owner preferences."""


@dataclass
class CareTask:
    """Tracks an individual pet care responsibility."""

    task_id: str
    title: str
    duration_minutes: int
    priority_level: int
    frequency: str
    notes: str = ""

    def is_due_today(self, current_day: str) -> bool:
        """Return True when the task should appear on the plan today."""

    def score(self, priority_weights: Dict[str, int]) -> int:
        """Compute a weighted priority score for scheduling."""

    def describe_reasoning(self) -> str:
        """Explain why the task was included in the plan."""


@dataclass
class SchedulePlanner:
    """Coordinates owner, pet, and tasks to form a daily plan."""

    owner_profile: OwnerProfile
    pet_profile: PetProfile
    tasks_queue: List[CareTask] = field(default_factory=list)
    planning_rules: Dict[str, str] = field(default_factory=dict)

    def generate_daily_plan(self) -> List[CareTask]:
        """Select and order tasks based on constraints and priorities."""

    def explain_decisions(self, plan: List[CareTask]) -> List[str]:
        """Return human-readable explanations for each scheduled task."""

    def rebalance_when_overbooked(self, plan: List[CareTask]) -> List[CareTask]:
        """Adjust the plan if the total duration exceeds the available time."""
