"""Core logic layer for PawPal+ backend classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


@dataclass
class Task:
    """Represents a single pet-care activity."""

    task_id: str
    description: str
    duration_minutes: int
    frequency: str = "once"  # once, daily, weekly, custom
    priority: int = 0  # higher means more urgent
    completed: bool = False
    last_completed_on: Optional[date] = None
    custom_days: Optional[List[int]] = None  # weekdays 0=Mon .. 6=Sun
    time: Optional[str] = None  # HH:MM 24-hour format for task scheduling
    due_date: Optional[date] = None  # specific date when task is due
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate task invariants after initialization."""
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be a positive number of minutes.")
        if self.frequency not in {"once", "daily", "weekly", "custom"}:
            raise ValueError("Frequency must be one of: once, daily, weekly, custom.")
        if self.time:
            parts = self.time.split(":")
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                raise ValueError("Time must be in 'HH:MM' format")
            hour = int(parts[0])
            minute = int(parts[1])
            if hour not in range(24) or minute not in range(60):
                raise ValueError("Time must be in 'HH:MM' 24-hour range")
        if self.frequency in {"daily", "weekly"} and self.due_date is None:
            self.due_date = date.today()

    def mark_complete(self, completed_on: Optional[date] = None) -> None:
        """Mark the task complete and store the completion date."""
        self.completed = True
        self.last_completed_on = completed_on or date.today()

    def reset_completion(self) -> None:
        """Mark the task as incomplete while preserving the history note."""
        self.completed = False

    def is_due_on(self, target_date: date) -> bool:
        """Return True when the task should appear on the plan for target_date."""
        if self.frequency == "once":
            return not self.completed
        if self.frequency == "daily":
            return self.due_date and target_date >= self.due_date and not self.completed
        if self.frequency == "weekly":
            return self.due_date and target_date >= self.due_date and not self.completed
        # custom weekdays
        if not self.custom_days:
            return True
        return target_date.weekday() in self.custom_days

    def priority_tuple(self) -> Tuple[int, int]:
        """Return a tuple that helps sort tasks by priority then duration."""
        return (-self.priority, self.duration_minutes)

    def summary(self) -> str:
        """Provide a one-line description useful for UI explanations."""
        time_info = f" at {self.time}" if self.time else ""
        due_info = f" on {self.due_date}" if self.due_date else ""
        status_info = "complete" if self.completed else "pending"
        return f"{self.description}{time_info}{due_info} ({self.duration_minutes} min, priority {self.priority}, {status_info})"


@dataclass
class Pet:
    """Stores pet details and the tasks assigned to that pet."""

    name: str
    species: str
    age: Optional[int] = None
    notes: str = ""
    tasks: Dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet, replacing any task that shares the ID."""
        self.tasks[task.task_id] = task

    def remove_task(self, task_id: str) -> Optional[Task]:
        """Remove a task by ID and return it if found."""
        return self.tasks.pop(task_id, None)

    def list_tasks(self, include_completed: bool = True) -> List[Task]:
        """Return this pet's tasks, optionally filtering out completed ones."""
        if include_completed:
            return list(self.tasks.values())
        return [task for task in self.tasks.values() if not task.completed]

    def due_tasks(self, target_date: date, include_completed: bool = False) -> List[Task]:
        """Return tasks that should run on target_date."""
        tasks = []
        for task in self.tasks.values():
            if not include_completed and task.completed:
                if task.frequency == "once":
                    continue
                if task.last_completed_on and task.last_completed_on >= target_date:
                    continue
            if task.is_due_on(target_date):
                tasks.append(task)
        return tasks


@dataclass
class Owner:
    """Manages multiple pets and exposes their tasks."""

    name: str
    contact_info: str
    daily_time_budget: int
    pets: Dict[str, Pet] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure the owner starts with a positive daily time budget."""
        if self.daily_time_budget <= 0:
            raise ValueError("daily_time_budget must be a positive number of minutes.")

    def add_pet(self, pet: Pet) -> None:
        """Register or replace a pet by name."""
        self.pets[pet.name] = pet

    def remove_pet(self, pet_name: str) -> Optional[Pet]:
        """Remove a pet and return it."""
        return self.pets.pop(pet_name, None)

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Fetch a pet by name."""
        return self.pets.get(pet_name)

    def list_pets(self) -> List[Pet]:
        """Return every pet object."""
        return list(self.pets.values())

    def all_tasks(self, include_completed: bool = True) -> List[Tuple[Pet, Task]]:
        """Return every task paired with its pet for easy aggregation."""
        paired: List[Tuple[Pet, Task]] = []
        for pet in self.list_pets():
            for task in pet.list_tasks(include_completed=include_completed):
                paired.append((pet, task))
        return paired


class Scheduler:
    """Brain that retrieves, organizes, and manages tasks across pets."""

    def __init__(self, owner: Owner) -> None:
        """Store the owner reference the scheduler will operate on."""
        self.owner = owner

    def _all_tasks_with_pets(
        self, *, include_completed: bool = True, target_date: Optional[date] = None
    ) -> List[Tuple[Pet, Task]]:
        """Helper that returns (pet, task) tuples optionally filtered by due date."""
        tasks: List[Tuple[Pet, Task]] = []
        for pet in self.owner.list_pets():
            if target_date:
                pet_tasks = pet.due_tasks(target_date, include_completed=include_completed)
            else:
                pet_tasks = pet.list_tasks(include_completed=include_completed)
            for task in pet_tasks:
                tasks.append((pet, task))
        return tasks

    def build_daily_plan(
        self, target_date: date, available_minutes: Optional[int] = None
    ) -> List[Tuple[Pet, Task]]:
        """Return an ordered list of (pet, task) tuples that fit into the day."""
        minutes_budget = available_minutes or self.owner.daily_time_budget
        due_tasks = self._all_tasks_with_pets(include_completed=False, target_date=target_date)
        # Sort by priority then duration so urgent work comes first
        due_tasks.sort(key=lambda pair: pair[1].priority_tuple())

        plan: List[Tuple[Pet, Task]] = []
        total_minutes = 0
        for pet, task in due_tasks:
            if total_minutes + task.duration_minutes > minutes_budget:
                continue
            plan.append((pet, task))
            total_minutes += task.duration_minutes
        return plan

    def overdue_tasks(self, reference_date: date) -> List[Tuple[Pet, Task]]:
        """Return tasks due on or before reference_date that remain incomplete."""
        overdue: List[Tuple[Pet, Task]] = []
        cutoff = reference_date
        for pet in self.owner.list_pets():
            for task in pet.list_tasks(include_completed=False):
                if task.is_due_on(cutoff):
                    overdue.append((pet, task))
        return overdue

    def mark_task_complete(self, task_id: str, *, completed_on: Optional[date] = None) -> bool:
        """Mark a task complete and create a new instance for recurring tasks.

        For daily/weekly tasks, automatically creates a new task instance
        for the next occurrence using timedelta for date calculation.

        Args:
            task_id: The ID of the task to mark complete.
            completed_on: The date of completion. Defaults to today.

        Returns:
            True if the task was found and marked complete, False otherwise.
        """
        for pet in self.owner.list_pets():
            task = pet.tasks.get(task_id)
            if task:
                task.mark_complete(completed_on)
                # For recurring tasks, create a new instance for the next occurrence
                if task.frequency in {"daily", "weekly"}:
                    days_ahead = 1 if task.frequency == "daily" else 7
                    new_due_date = (completed_on or date.today()) + timedelta(days=days_ahead)
                    new_task_id = f"{task.task_id}_{(completed_on or date.today()).isoformat()}"
                    new_task = Task(
                        task_id=new_task_id,
                        description=task.description,
                        duration_minutes=task.duration_minutes,
                        frequency=task.frequency,
                        priority=task.priority,
                        completed=False,
                        last_completed_on=None,
                        custom_days=task.custom_days,
                        time=task.time,
                        due_date=new_due_date,
                        notes=task.notes,
                    )
                    pet.add_task(new_task)
                return True
        return False

    def collect_task_summaries(self, include_completed: bool = True) -> List[str]:
        """Return summarized strings for every task for UI rendering."""
        summaries: List[str] = []
        for pet, task in self._all_tasks_with_pets(include_completed=include_completed):
            summaries.append(f"{pet.name}: {task.summary()}")
        return summaries

    @staticmethod
    def _parse_time(time_str: Optional[str]) -> Tuple[int, int]:
        """Parse 'HH:MM' to tuple for sorted key; missing time goes last."""
        if not time_str:
            return (23, 59)
        hour, minute = map(int, time_str.split(":"))
        return (hour, minute)

    def sort_by_time(self, tasks: List[Tuple[Pet, Task]], reverse: bool = False) -> List[Tuple[Pet, Task]]:
        """Sort a list of (pet, task) tuples by the task's scheduled time.

        Uses Python's sorted() with a lambda key that parses 'HH:MM' strings.
        Tasks without a time are sorted to the end (23:59).

        Args:
            tasks: List of (Pet, Task) tuples to sort.
            reverse: If True, sort in descending order (latest first).

        Returns:
            Sorted list of (Pet, Task) tuples.
        """
        return sorted(tasks, key=lambda pair: self._parse_time(pair[1].time), reverse=reverse)

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        target_date: Optional[date] = None,
    ) -> List[Tuple[Pet, Task]]:
        """Filter tasks by pet name, completion status, and/or due date.

        Args:
            pet_name: If provided, only include tasks for pets with this name (case-insensitive).
            completed: If True/False, only include completed/incomplete tasks. If None, include all.
            target_date: If provided, only include tasks due on this date.

        Returns:
            List of (Pet, Task) tuples matching the filters.
        """
        include_completed = True if completed is None else completed
        tasks = self._all_tasks_with_pets(include_completed=include_completed, target_date=target_date)

        if pet_name:
            tasks = [(p, t) for (p, t) in tasks if p.name.lower() == pet_name.lower()]

        if completed is not None:
            tasks = [(p, t) for (p, t) in tasks if t.completed is completed]

        return tasks

    def detect_conflicts(self, target_date: date) -> List[Tuple[Pet, Task, Pet, Task]]:
        """Detect overlapping tasks on the given date and return conflicting pairs.

        Tasks are considered conflicting if their time intervals overlap.
        Only pending tasks are checked.

        Args:
            target_date: The date to check for conflicts.

        Returns:
            List of (pet1, task1, pet2, task2) tuples where tasks overlap.
        """
        due_tasks = self.sort_by_time(self._all_tasks_with_pets(include_completed=False, target_date=target_date))
        collisions: List[Tuple[Pet, Task, Pet, Task]] = []

        def bounds(task: Task) -> Tuple[int, int]:
            if not task.time:
                return (24*60, 24*60)
            h, m = self._parse_time(task.time)
            start = h * 60 + m
            return (start, start + task.duration_minutes)

        for i in range(len(due_tasks)):
            pet_i, task_i = due_tasks[i]
            start_i, end_i = bounds(task_i)
            if start_i >= 24 * 60:
                continue
            for j in range(i + 1, len(due_tasks)):
                pet_j, task_j = due_tasks[j]
                start_j, end_j = bounds(task_j)
                if start_j >= 24 * 60:
                    continue
                # treat tasks as conflicting if times overlap
                if start_j < end_i:
                    collisions.append((pet_i, task_i, pet_j, task_j))
        return collisions
