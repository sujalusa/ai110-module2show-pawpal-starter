"""Basic tests for the PawPal+ logic layer."""

from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from pawpal_system import Pet, Task


def test_task_completion_changes_status() -> None:
    task = Task(task_id="feed-1", description="Feed the cat", duration_minutes=10)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True
    assert task.last_completed_on == date.today()


def test_adding_task_increases_pet_task_count() -> None:
    pet = Pet(name="Riley", species="Dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(task_id="walk-1", description="Morning walk", duration_minutes=30))
    assert len(pet.tasks) == 1

    pet.add_task(Task(task_id="walk-2", description="Evening walk", duration_minutes=25))
    assert len(pet.tasks) == 2
