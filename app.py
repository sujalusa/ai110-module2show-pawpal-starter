from datetime import date
from uuid import uuid4

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        contact_info="jordan@example.com",
        daily_time_budget=180,
    )

owner: Owner = st.session_state.owner

st.subheader("Owner Profile")
with st.form("owner_form", clear_on_submit=False):
    owner_name = st.text_input("Owner name", value=owner.name)
    contact_info = st.text_input("Contact info", value=owner.contact_info)
    time_budget = st.number_input(
        "Daily time budget (minutes)", min_value=15, max_value=720, value=owner.daily_time_budget
    )
    if st.form_submit_button("Save owner profile"):
        owner.name = owner_name.strip() or owner.name
        owner.contact_info = contact_info.strip()
        owner.daily_time_budget = int(time_budget)
        st.success("Owner profile updated.")

st.divider()

st.subheader("Pets")
with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"], index=0)
    pet_age = st.number_input("Age (years)", min_value=0, max_value=40, value=2, step=1)
    pet_notes = st.text_input("Notes", value="Loves long walks")
    if st.form_submit_button("Add / Update Pet"):
        if pet_name.strip():
            owner.add_pet(
                Pet(name=pet_name.strip(), species=species, age=int(pet_age), notes=pet_notes)
            )
            st.success(f"Stored pet profile for {pet_name.strip()}.")
        else:
            st.error("Please provide a pet name.")

pet_names = [pet.name for pet in owner.list_pets()]
if not pet_names:
    st.info("No pets yet. Add one using the form above to begin scheduling.")

st.divider()

st.subheader("Add Tasks")
priority_map = {"Low": 1, "Medium": 2, "High": 3}
if pet_names:
    with st.form("task_form"):
        selected_pet = st.selectbox("Assign to pet", pet_names)
        task_title = st.text_input("Task title", value="Morning walk")
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, value=30)
        priority_label = st.selectbox("Priority", list(priority_map.keys()), index=2)
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=1)
        notes = st.text_input("Notes", value="Auto-generated from UI")
        submitted = st.form_submit_button("Add task")
        if submitted:
            pet = owner.get_pet(selected_pet)
            if pet:
                task = Task(
                    task_id=f"{selected_pet}-{uuid4().hex[:6]}",
                    description=task_title.strip() or "Untitled",
                    duration_minutes=int(duration),
                    priority=priority_map[priority_label],
                    frequency=frequency,
                    notes=notes,
                )
                pet.add_task(task)
                st.success(f"Added task '{task.description}' to {selected_pet}.")
else:
    st.info("Add at least one pet to start attaching tasks.")

if pet_names:
    st.markdown("### Current Tasks by Pet")
    for pet in owner.list_pets():
        st.markdown(f"**{pet.name}** ({len(pet.tasks)} tasks)")
        if pet.tasks:
            st.table(
                [
                    {
                        "Task": task.description,
                        "Duration": f"{task.duration_minutes} min",
                        "Priority": task.priority,
                        "Frequency": task.frequency,
                    }
                    for task in pet.list_tasks()
                ]
            )
        else:
            st.caption("No tasks yet.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a plan using the current owner, pets, and tasks.")

plan_date = st.date_input("Plan date", value=date.today())
if st.button("Generate schedule"):
    if not pet_names:
        st.warning("Add at least one pet before generating a schedule.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.build_daily_plan(plan_date)
        if not plan:
            st.info("No tasks fit into today's schedule. Try adding tasks or increasing the time budget.")
        else:
            st.success(f"Built plan for {plan_date.isoformat()}")
            for idx, (pet, task) in enumerate(plan, start=1):
                st.write(
                    f"{idx}. **{pet.name}** — {task.description} "
                    f"({task.duration_minutes} min, priority {task.priority})"
                )
