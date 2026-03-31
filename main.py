"""Temporary CLI script to exercise the PawPal+ logic layer."""

from __future__ import annotations

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def seed_owner() -> Owner:
    """Create an owner with two pets and a handful of tasks."""
    owner = Owner(name="Alex Chen", contact_info="alex@example.com", daily_time_budget=120)

    dog = Pet(name="Riley", species="Dog", age=4, notes="Needs long walks")
    dog.add_task(
        Task(
            task_id="dog-enrichment",
            description="Puzzle feeder session",
            duration_minutes=20,
            frequency="weekly",
            priority=2,
            time="11:00",
        )
    )
    dog.add_task(
        Task(
            task_id="dog-walk-am",
            description="Morning walk around the block",
            duration_minutes=30,
            frequency="daily",
            priority=3,
            time="08:00",
        )
    )
    dog.add_task(
        Task(
            task_id="dog-med",
            description="Give medication",
            duration_minutes=10,
            frequency="daily",
            priority=5,
            time="07:30",
        )
    )
    dog.add_task(
        Task(
            task_id="dog-breakfast",
            description="Breakfast feeding",
            duration_minutes=10,
            frequency="daily",
            priority=4,
            time="08:00",
        )
    )

    cat = Pet(name="Miso", species="Cat", age=2, notes="Prefers quiet play")
    cat.add_task(
        Task(
            task_id="cat-play",
            description="Interactive toy time",
            duration_minutes=15,
            frequency="daily",
            priority=3,
            time="18:30",
        )
    )
    cat.add_task(
        Task(
            task_id="cat-feeding-pm",
            description="Evening feeding",
            duration_minutes=10,
            frequency="daily",
            priority=4,
            time="19:00",
        )
    )
    cat.add_task(
        Task(
            task_id="cat-groom",
            description="Quick brush session",
            duration_minutes=10,
            frequency="weekly",
            priority=2,
            time="17:45",
        )
    )
    cat.add_task(
        Task(
            task_id="cat-morning",
            description="Morning play",
            duration_minutes=20,
            frequency="daily",
            priority=3,
            time="08:00",
        )
    )

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


def print_schedule(plan_date: date) -> None:
    """Build and print a simple schedule for the chosen date."""
    owner = seed_owner()
    scheduler = Scheduler(owner)

    plan = scheduler.build_daily_plan(plan_date)

    print("Today's Schedule")
    print("----------------")
    if not plan:
        print("No tasks scheduled.")
        return

    for idx, (pet, task) in enumerate(plan, start=1):
        print(f"{idx}. {pet.name}: {task.description} ({task.duration_minutes} min, priority {task.priority})")


def demo_sort_and_filter() -> None:
    owner = seed_owner()
    scheduler = Scheduler(owner)

    print("\n=== All Tasks (Unsorted) ===")
    for pet, task in scheduler._all_tasks_with_pets(include_completed=True):
        print(f"{pet.name}: {task.summary()}")

    print("\n=== Marking dog-walk-am complete ===")
    scheduler.mark_task_complete("dog-walk-am")
    print("Marked complete. Now all tasks:")
    for pet, task in scheduler._all_tasks_with_pets(include_completed=True):
        print(f"{pet.name}: {task.summary()}")

    print("\n=== Sorted by Time ===")
    sorted_tasks = scheduler.sort_by_time(scheduler._all_tasks_with_pets(include_completed=True))
    for pet, task in sorted_tasks:
        print(f"{task.time or '??'} {pet.name}: {task.description}")

    print("\n=== Filtered for pet=Riley, incomplete ===")
    filtered = scheduler.filter_tasks(pet_name="Riley", completed=False)
    for pet, task in filtered:
        print(f"{pet.name}: {task.summary()}")

    print("\n=== Conflict detection Today ===")
    conflicts = scheduler.detect_conflicts(date.today())
    if not conflicts:
        print("No conflicts detected")
    else:
        for p1, t1, p2, t2 in conflicts:
            print(f"Warning: {p1.name}'s {t1.description} overlaps with {p2.name}'s {t2.description}")


if __name__ == "__main__":
    print_schedule(date.today())
    demo_sort_and_filter()
