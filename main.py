import tkinter as tk
from tkinter import messagebox
import requests

AUTH_URL = "http://127.0.0.1:5001"
PRIORITY_URL = "http://127.0.0.1:5002"
TIME_TRACKING_URL = "http://127.0.0.1:5003"
SUMMARY_URL = "http://127.0.0.1:5009"

tasks = []

def login_user(username, password):
    try:
        response = requests.post(
            f"{AUTH_URL}/auth/login",
            json={
                "username": username,
                "password": password
            },
            timeout=3
        )

        data = response.json()

        if response.status_code == 200:
            return True, data

        return False, data.get("message", "Login failed.")

    except requests.RequestException:
        return False, "Auth microservice is not available."

def get_task_priority(due_date, importance):
    try:
        response = requests.post(
            f"{PRIORITY_URL}/priority",
            json={
                "due_date": due_date,
                "importance": importance
            },
            timeout=3
        )

        data = response.json()

        if response.status_code == 200:
            return True, data["priority"]

        return False, data.get("message", "Could not calculate priority.")

    except requests.RequestException:
        return False, "Priority Scoring microservice is not available."

def start_task_timer(task_id):
    try:
        response = requests.post(
            f"{TIME_TRACKING_URL}/timer/start",
            json={"task_id": task_id},
            timeout=3
        )

        data = response.json()

        if response.status_code == 200:
            return True, data

        return False, data.get("message", "Could not start timer.")

    except requests.RequestException:
        return False, "Time Tracking microservice is not available."

def stop_task_timer(task_id):
    try:
        response = requests.post(
            f"{TIME_TRACKING_URL}/timer/stop",
            json={"task_id": task_id},
            timeout=3
        )

        data = response.json()

        if response.status_code == 200:
            return True, data

        return False, data.get("message", "Could not stop timer.")

    except requests.RequestException:
        return False, "Time Tracking microservice is not available."

def start_selected_timer():
    selection = task_listbox.curselection()

    if not selection:
        view_status_label.config(
            text="Please select a task first.",
            fg="red"
        )
        return

    task = tasks[selection[0]]

    success, result = start_task_timer(task["name"])

    if success:
        view_status_label.config(
            text=f'Timer started for "{task["name"]}".',
            fg="green"
        )
    else:
        view_status_label.config(text=str(result), fg="red")

def stop_selected_timer():
    selection = task_listbox.curselection()

    if not selection:
        view_status_label.config(
            text="Please select a task first.",
            fg="red"
        )
        return

    task = tasks[selection[0]]

    success, result = stop_task_timer(task["name"])

    if success:
        view_status_label.config(
            text=(
                f'Timer stopped for "{task["name"]}". '
                f'Session: {result["time_spent_seconds"]} sec | '
                f'Total: {result["total_time_seconds"]} sec'
            ),
            fg="green"
        )
    else:
        view_status_label.config(text=str(result), fg="red")

def get_task_summary():
    try:
        records = [
            1 if task["completed"] else 0
            for task in tasks
        ]

        response = requests.post(
            f"{SUMMARY_URL}/summary",
            json={"records": records},
            timeout=3
        )

        data = response.json()

        if response.status_code == 200:
            return True, data

        return False, data.get("error", "Could not calculate summary.")

    except requests.RequestException:
        return False, "Record Summary microservice is not available."

def show_progress_summary():
    success, result = get_task_summary()

    if not success:
        messagebox.showerror("Progress Summary", str(result))
        return

    completed = result["total"]
    total = result["count"]
    percent = result["average"] * 100

    messagebox.showinfo(
        "Progress Summary",
        f"Completed Tasks: {completed}/{total}\n"
        f"Progress: {percent:.0f}%"
    )

def show_frame(frame):
    welcome_frame.pack_forget()
    login_frame.pack_forget()
    main_menu_frame.pack_forget()
    add_task_frame.pack_forget()
    view_tasks_frame.pack_forget()
    complete_task_frame.pack_forget()
    frame.pack(fill="both", expand=True)

def open_main_menu():
    show_frame(main_menu_frame)

def open_login():
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)
    login_status_label.config(text="")
    show_frame(login_frame)


def handle_login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if username == "" or password == "":
        login_status_label.config(
            text="Please enter a username and password.",
            fg="red"
        )
        return

    success, result = login_user(username, password)

    if success:
        login_status_label.config(
            text="Login successful.",
            fg="green"
        )
        open_main_menu()
    else:
        login_status_label.config(
            text=str(result),
            fg="red"
        )

def open_add_task():
    task_entry.delete(0, tk.END)
    due_date_entry.delete(0, tk.END)
    importance_var.set("Medium")
    add_status_label.config(text="")
    show_frame(add_task_frame)

def add_task():
    task_name = task_entry.get().strip()
    due_date = due_date_entry.get().strip()
    importance = importance_var.get()

    if task_name == "":
        add_status_label.config(
            text="Please enter a task name.",
            fg="red"
        )
        return

    if due_date == "":
        add_status_label.config(
            text="Please enter a due date.",
            fg="red"
        )
        return

    success, result = get_task_priority(due_date, importance)

    if not success:
        add_status_label.config(
            text=str(result),
            fg="red"
        )
        return

    tasks.append({
        "name": task_name,
        "due_date": due_date,
        "importance": importance,
        "priority": result,
        "completed": False
    })

    task_entry.delete(0, tk.END)
    due_date_entry.delete(0, tk.END)

    add_status_label.config(
        text=f'"{task_name}" was added with {result} priority.',
        fg="green"
    )

def open_view_tasks():
    task_listbox.delete(0, tk.END)

    if len(tasks) == 0:
        view_status_label.config(
            text="No tasks have been added yet."
        )
    else:
        view_status_label.config(text="")

        for task in tasks:
            if task["completed"]:
                status = "[Completed]"
            else:
                status = "[Not Completed]"

            task_listbox.insert(
                tk.END,
                f"{status} {task['name']} | Due: {task['due_date']} | "
                f"Importance: {task['importance']} | Priority: {task['priority']}"
            )

    show_frame(view_tasks_frame)

def open_complete_task():
    selected_task_index.set(-1)
    complete_status_label.config(text="")

    for widget in task_options_frame.winfo_children():
        widget.destroy()

    unfinished_tasks = 0

    for index, task in enumerate(tasks):
        if not task["completed"]:
            task_option = tk.Radiobutton(
                task_options_frame,
                text=task["name"],
                variable=selected_task_index,
                value=index,
                font=("Arial", 11)
            )
            task_option.pack(anchor="w", pady=4)
            unfinished_tasks += 1

    if unfinished_tasks == 0:
        no_tasks_label = tk.Label(
            task_options_frame,
            text="No unfinished tasks are available.",
            font=("Arial", 11)
        )
        no_tasks_label.pack(pady=10)

        mark_complete_button.config(state="disabled")
    else:
        mark_complete_button.config(state="normal")

    show_frame(complete_task_frame)


def complete_selected_task():
    task_index = selected_task_index.get()

    if task_index == -1:
        complete_status_label.config(
            text="Please select a task.",
            fg="red"
        )
        return

    task_name = tasks[task_index]["name"]

    confirmed = messagebox.askyesno(
        "Confirm Completion",
        f'Mark "{task_name}" as complete?'
    )

    if confirmed:
        tasks[task_index]["completed"] = True
        open_complete_task()

        complete_status_label.config(
            text=f'"{task_name}" was marked as complete.',
            fg="green"
        )
    else:
        complete_status_label.config(
            text="No changes were made.",
            fg="black"
        )

root = tk.Tk()
root.title("Student Task Tracker")
root.geometry("500x500")

# Welcome page
welcome_frame = tk.Frame(root, padx=30, pady=30)
welcome_frame.pack(fill="both", expand=True)

title_label = tk.Label(
    welcome_frame,
    text="Student Task Tracker",
    font=("Arial", 22, "bold")
)
title_label.pack(pady=30)

description_label = tk.Label(
    welcome_frame,
    text=(
        "Keep your school tasks organized in one place.\n"
        "Add tasks, view your workload, and track completed work."
    ),
    font=("Arial", 12),
    justify="center"
)
description_label.pack(pady=20)

get_started_button = tk.Button(
    welcome_frame,
    text="Get Started",
    font=("Arial", 12),
    command=open_login
)
get_started_button.pack(pady=20)

# Login page
login_frame = tk.Frame(root, padx=30, pady=30)

login_title = tk.Label(
    login_frame,
    text="Login",
    font=("Arial", 22, "bold")
)
login_title.pack(pady=20)

username_label = tk.Label(
    login_frame,
    text="Username:",
    font=("Arial", 12)
)
username_label.pack(pady=5)

username_entry = tk.Entry(
    login_frame,
    width=30,
    font=("Arial", 12)
)
username_entry.pack(pady=5)

password_label = tk.Label(
    login_frame,
    text="Password:",
    font=("Arial", 12)
)
password_label.pack(pady=5)

password_entry = tk.Entry(
    login_frame,
    width=30,
    font=("Arial", 12),
    show="*"
)
password_entry.pack(pady=5)

login_button = tk.Button(
    login_frame,
    text="Login",
    width=20,
    font=("Arial", 12),
    command=handle_login
)
login_button.pack(pady=15)

login_status_label = tk.Label(
    login_frame,
    text="",
    font=("Arial", 11)
)
login_status_label.pack(pady=5)

# Main menu page
main_menu_frame = tk.Frame(root, padx=30, pady=30)

menu_title = tk.Label(
    main_menu_frame,
    text="Student Task Tracker",
    font=("Arial", 22, "bold")
)
menu_title.pack(pady=20)

menu_description = tk.Label(
    main_menu_frame,
    text=(
        "Keep your school tasks organized in one place.\n"
        "Add tasks, view your workload, and track completed work."
    ),
    font=("Arial", 11),
    justify="center"
)
menu_description.pack(pady=10)

add_task_button = tk.Button(
    main_menu_frame,
    text="Add Task",
    width=20,
    font=("Arial", 12),
    command=open_add_task
)
add_task_button.pack(pady=8)

view_tasks_button = tk.Button(
    main_menu_frame,
    text="View Tasks",
    width=20,
    font=("Arial", 12),
    command=open_view_tasks
)
view_tasks_button.pack(pady=8)

complete_task_button = tk.Button(
    main_menu_frame,
    text="Complete Task",
    width=20,
    font=("Arial", 12),
    command=open_complete_task
)
complete_task_button.pack(pady=8)

instructions_label = tk.Label(
    main_menu_frame,
    text=(
        "How It Works:\n"
        "1. Add a task.\n"
        "2. View your task list.\n"
        "3. Mark finished tasks as complete."
    ),
    font=("Arial", 11),
    justify="left"
)

def toggle_instructions():
    if instructions_label.winfo_ismapped():
        instructions_label.pack_forget()
        how_it_works_button.config(text="How It Works")
    else:
        instructions_label.pack(pady=10)
        how_it_works_button.config(text="Hide Instructions")


how_it_works_button = tk.Button(
    main_menu_frame,
    text="How It Works",
    width=20,
    font=("Arial", 12),
    command=toggle_instructions
)
how_it_works_button.pack(pady=8)

progress_button = tk.Button(
    main_menu_frame,
    text="View Progress",
    width=22,
    font=("Arial", 12),
    command=show_progress_summary
)
progress_button.pack(pady=8)

exit_button = tk.Button(
    main_menu_frame,
    text="Exit",
    width=20,
    font=("Arial", 12),
    command=root.destroy
)
exit_button.pack(pady=8)

# Add Task page
add_task_frame = tk.Frame(root, padx=30, pady=30)

add_task_title = tk.Label(
    add_task_frame,
    text="Add Task",
    font=("Arial", 22, "bold")
)
add_task_title.pack(pady=20)

task_cost_label = tk.Label(
    add_task_frame,
    text=(
    "Adding a task takes only a few seconds. "
    "Only a task name is required. No personal information is collected."
    ),
    font=("Arial", 10),
    wraplength=400
)
task_cost_label.pack(pady=10)

task_name_label = tk.Label(
    add_task_frame,
    text="Enter task name:",
    font=("Arial", 12)
)
task_name_label.pack(pady=5)

task_entry = tk.Entry(
    add_task_frame,
    width=35,
    font=("Arial", 12)
)
task_entry.pack(pady=10)

due_date_label = tk.Label(
    add_task_frame,
    text="Due date (YYYY-MM-DD):",
    font=("Arial", 12)
)
due_date_label.pack(pady=5)

due_date_entry = tk.Entry(
    add_task_frame,
    width=35,
    font=("Arial", 12)
)
due_date_entry.pack(pady=10)

importance_label = tk.Label(
    add_task_frame,
    text="Importance:",
    font=("Arial", 12)
)
importance_label.pack(pady=5)

importance_var = tk.StringVar(value="Medium")

importance_menu = tk.OptionMenu(
    add_task_frame,
    importance_var,
    "High",
    "Medium",
    "Low"
)
importance_menu.config(width=15, font=("Arial", 11))
importance_menu.pack(pady=10)

submit_task_button = tk.Button(
    add_task_frame,
    text="Add",
    width=20,
    font=("Arial", 12),
    command=add_task
)
submit_task_button.pack(pady=8)

cancel_button = tk.Button(
    add_task_frame,
    text="Cancel / Main Menu",
    width=20,
    font=("Arial", 12),
    command=open_main_menu
)
cancel_button.pack(pady=8)

add_status_label = tk.Label(
    add_task_frame,
    text="",
    font=("Arial", 11),
    wraplength=400
)
add_status_label.pack(pady=15)

# View Tasks page
view_tasks_frame = tk.Frame(root, padx=30, pady=30)

view_tasks_title = tk.Label(
    view_tasks_frame,
    text="View Tasks",
    font=("Arial", 22, "bold")
)
view_tasks_title.pack(pady=20)

task_listbox = tk.Listbox(
    view_tasks_frame,
    width=45,
    height=10,
    font=("Arial", 11)
)
task_listbox.pack(pady=10)

view_status_label = tk.Label(
    view_tasks_frame,
    text="",
    font=("Arial", 11)
)
view_status_label.pack(pady=10)

start_timer_button = tk.Button(
    view_tasks_frame,
    text="Start Timer",
    width=20,
    font=("Arial", 12),
    command=start_selected_timer
)
start_timer_button.pack(pady=5)

stop_timer_button = tk.Button(
    view_tasks_frame,
    text="Stop Timer",
    width=20,
    font=("Arial", 12),
    command=stop_selected_timer
)
stop_timer_button.pack(pady=5)

view_complete_task_button = tk.Button(
    view_tasks_frame,
    text="Complete a Task",
    width=20,
    font=("Arial", 12),
    command=open_complete_task
)
view_complete_task_button.pack(pady=5)

view_main_menu_button = tk.Button(
    view_tasks_frame,
    text="Main Menu",
    width=20,
    font=("Arial", 12),
    command=open_main_menu
)
view_main_menu_button.pack(pady=10)

# Complete Task page
complete_task_frame = tk.Frame(root, padx=30, pady=30)

complete_task_title = tk.Label(
    complete_task_frame,
    text="Complete Task",
    font=("Arial", 22, "bold")
)
complete_task_title.pack(pady=20)

complete_task_instructions = tk.Label(
    complete_task_frame,
    text="Select one unfinished task:",
    font=("Arial", 12)
)
complete_task_instructions.pack(pady=5)

selected_task_index = tk.IntVar(value=-1)

task_options_frame = tk.Frame(complete_task_frame)
task_options_frame.pack(pady=10)

mark_complete_button = tk.Button(
    complete_task_frame,
    text="Mark as Complete",
    width=20,
    font=("Arial", 12),
    command=complete_selected_task
)
mark_complete_button.pack(pady=8)

complete_main_menu_button = tk.Button(
    complete_task_frame,
    text="Main Menu",
    width=20,
    font=("Arial", 12),
    command=open_main_menu
)
complete_main_menu_button.pack(pady=8)

complete_status_label = tk.Label(
    complete_task_frame,
    text="",
    font=("Arial", 11),
    wraplength=400
)
complete_status_label.pack(pady=10)

root.mainloop()
