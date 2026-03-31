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


def test_sorting_tasks_by_time() -> None:
    from datetime import date

    owner = __import__("pawpal_system", fromlist=["Owner"]).Owner(name="Test", contact_info="x", daily_time_budget=120)
    pet = __import__("pawpal_system", fromlist=["Pet"]).Pet(name="Riley", species="Dog")
    owner.add_pet(pet)

    task_1 = __import__("pawpal_system", fromlist=["Task"]).Task(
        task_id="t1",
        description="Morning feed",
        duration_minutes=10,
        time="09:00",
    )
    task_2 = __import__("pawpal_system", fromlist=["Task"]).Task(
        task_id="t2",
        description="Breakfast",
        duration_minutes=15,
        time="07:30",
    )
    task_3 = __import__("pawpal_system", fromlist=["Task"]).Task(
        task_id="t3",
        description="Evening treat",
        duration_minutes=5,
        time="19:00",
    )

    pet.add_task(task_1)
    pet.add_task(task_2)
    pet.add_task(task_3)

    scheduler = __import__("pawpal_system", fromlist=["Scheduler"]).Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time([(pet, task_1), (pet, task_2), (pet, task_3)])

    assert [t.task_id for _, t in sorted_tasks] == ["t2", "t1", "t3"]


def test_recurring_daily_mark_complete_creates_next_occurrence() -> None:
    from datetime import date, timedelta

    Owner = __import__("pawpal_system", fromlist=["Owner"]).Owner
    Pet = __import__("pawpal_system", fromlist=["Pet"]).Pet
    Task = __import__("pawpal_system", fromlist=["Task"]).Task
    Scheduler = __import__("pawpal_system", fromlist=["Scheduler"]).Scheduler

    owner = Owner(name="Test", contact_info="x", daily_time_budget=120)
    pet = Pet(name="Riley", species="Dog")
    owner.add_pet(pet)

    today = date.today()
    daily_task = Task(
        task_id="daily-feed",
        description="Feed the dog",
        duration_minutes=15,
        frequency="daily",
        due_date=today,
        time="08:00",
    )
    pet.add_task(daily_task)

    scheduler = Scheduler(owner)
    assert scheduler.mark_task_complete("daily-feed", completed_on=today)

    assert pet.tasks["daily-feed"].completed is True

    next_day_id = f"daily-feed_{today.isoformat()}"
    assert next_day_id in pet.tasks
    next_task = pet.tasks[next_day_id]
    assert next_task.frequency == "daily"
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_conflict_detection_duplicate_task_times() -> None:
    from datetime import date

    Owner = __import__("pawpal_system", fromlist=["Owner"]).Owner
    Pet = __import__("pawpal_system", fromlist=["Pet"]).Pet
    Task = __import__("pawpal_system", fromlist=["Task"]).Task
    Scheduler = __import__("pawpal_system", fromlist=["Scheduler"]).Scheduler

    owner = Owner(name="Test", contact_info="x", daily_time_budget=300)
    pet = Pet(name="Riley", species="Dog")
    owner.add_pet(pet)

    today = date.today()
    # Two tasks at the exact same start time should conflict
    task_a = Task(task_id="tA", description="A", duration_minutes=20, time="09:00", due_date=today)
    task_b = Task(task_id="tB", description="B", duration_minutes=20, time="09:00", due_date=today)
    pet.add_task(task_a)
    pet.add_task(task_b)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts(today)

    assert len(conflicts) == 1
    pet1, c1, pet2, c2 = conflicts[0]
    assert {c1.task_id, c2.task_id} == {"tA", "tB"}

