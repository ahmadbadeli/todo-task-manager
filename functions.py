import pandas as pd
import time
import json
from uuid import uuid4 as uuid
from datetime import timedelta, datetime
from streamlit_modal import Modal

# Static Variables
table_headers = ["📌","Task","Delete","Edit","done"]
file_path = 'tasks.json'
modal = Modal(title="Edit Task",key='edit-task')

# Initialize
def load_file(filename=file_path):
    try:
        with open(filename,'r') as f:
            return json.load(f)

    except:
        return {
            'Layers':["Layer1","Layer2"],
            'Layer1':{'Tasks':[],'Categories':['Work','Personal'],'Reminder':{'status':False,'auto_update':False,'days':1,'tasks':[],'expired':[]}},
            'Layer2':{'Tasks':[],'Categories':['Work','Personal'],'Reminder':{'status':False,'auto_update':False,'days':1,'tasks':[],'expired':[]}}
            }

# functions
def save_file(tasks, current_layer, categories=None, states_dict=None, filename=file_path,
              reminder_tasks=None, expired_tasks=None, layers=None):
    # Load current data
    full_data = load_file()

    # Update layers if explicitly provided
    if layers is not None:
        prev_layers = full_data["Layers"]
        full_data["Layers"] = layers
        if len(layers) > len(prev_layers):
            added_layer = next(i for i in layers if i not in prev_layers)
            updated_layer ={added_layer:{'Tasks':[],'Categories':['Work','Personal'],'Reminder':{'status':False,'auto_update':False,'days':1,'tasks':[],'expired':[]}}}
            full_data.update(updated_layer)
        else:
            removed_layer = next(i for i in prev_layers if i not in layers)
            del full_data[removed_layer]
    else:
        layers = full_data["Layers"]  # use existing layers

    # Initialize categories
    if categories is None:
        categories = full_data.get(current_layer, {}).get("Categories", [])

    # Reminder setup
    if states_dict is not None:
        status = states_dict["status"]
        days = states_dict["days"]
        auto_update = states_dict["auto_update"]
    else:
        reminder_data = full_data.get(current_layer, {}).get("Reminder", {})
        status = reminder_data.get("status", False)
        days = reminder_data.get("days", 0)
        auto_update = reminder_data.get("auto_update", False)

    if reminder_tasks is None:
        reminder_tasks = full_data.get(current_layer, {}).get("Reminder", {}).get("tasks", [])
    if expired_tasks is None:
        expired_tasks = full_data.get(current_layer, {}).get("Reminder", {}).get("expired", [])

    # Sort tasks
    tasks.sort(key=lambda x: x["due_date"])

    # Update current layer
    full_data[current_layer] = {
        "Tasks": tasks,
        "Categories": categories,
        "Reminder": {
            "status": status,
            "auto_update": auto_update,
            "days": days,
            "tasks": reminder_tasks,
            "expired": expired_tasks
        }
    }

    # Save back to file
    with open(filename, 'w') as f:
        json.dump(full_data, f, indent=2)


def add_task(title,category,due_date,container,current_layer):
    original_tasks = load_file()[current_layer]["Tasks"]
    new_task = {"title":title,'pinned':False,"done":False,"category":category,"due_date":due_date, "ID":str(uuid())}  
    original_tasks.append(new_task)
    save_file(original_tasks,current_layer)
    temp_msg(container,"Task Added Successfully")

def toggle_done(tasks, task_id, is_filtered,current_layer):
    original_tasks = load_file()[current_layer]["Tasks"]
    target_tasks = original_tasks if is_filtered else tasks
    index = next(i for i, t in enumerate(target_tasks) if t["ID"] == task_id)
    target_tasks[index]["done"] = not target_tasks[index]["done"]
    save_file(target_tasks,current_layer)

def delete_task(tasks,index,is_filtered,current_layer):
    original_tasks = load_file()[current_layer]["Tasks"]
    target_tasks = original_tasks if is_filtered else tasks
    tasks_id = tasks[index]["ID"]
    if is_filtered:
        index = [i for i, task in enumerate(original_tasks) if task["ID"] == tasks_id][0]
    del target_tasks[index]
    save_file(target_tasks,current_layer)

def edit_task(tasks,title,index,status,category,due_date,is_filtered,pinned,current_layer):
    original_tasks = load_file()[current_layer]["Tasks"]
    my_id = tasks[index]["ID"] # don't use it directly
    tasks_id = tasks[index]["ID"] # to prevent some error
    target_tasks = original_tasks if is_filtered else tasks
    if is_filtered:
        index = [i for i, task in enumerate(original_tasks) if task["ID"] == tasks_id][0]
    target_tasks[index]= {"title":title,"pinned":pinned,"done":True if status == "done" else False, "category":category, "due_date":due_date, "ID":my_id}
    save_file(target_tasks,current_layer)

def temp_msg(container, msg, type=0):
    msg_types = {0: "success", 1: "error", 2: "warning"}
    getattr(container, msg_types[type])(msg)
    if type == 0:  
        time.sleep(1.5)
    else:
        time.sleep(2)

def remove_category(category,container,current_layer,categories=None,tasks=None):
    # initialize
    if categories is None:
        categories = load_file()[current_layer]["Categories"]
    if tasks is None:
        tasks = load_file()[current_layer]["Tasks"]
    # function
    if len(categories) > 1:
        categories.remove(category)
        tasks = [task for task in tasks if task["category"] in categories]
        save_file(tasks,current_layer,categories=categories)
        temp_msg(container,"Category Removed Seccessfully")
    else:
        temp_msg(container,"You can't delete all categories. 1 must be left.",type=1)

def add_category(category,container,current_layer,categories=None,tasks=None):
    # initialize
    if categories is None:
        categories = load_file()[current_layer]["Categories"]
    if tasks is None:
        tasks = load_file()[current_layer]["Tasks"]
    # function
    if category:
        categories_lower = [i.lower() for i in categories]
        if category.lower() not in categories_lower:
            categories.append(category.title())
            save_file(tasks,current_layer,categories=categories)
            temp_msg(container,"Category Added Successfully")
        else:
            temp_msg(container,"Category already existed",type=1)
    else:
        temp_msg(container,"You have to enter a category first",type=2)

def upcoming_tasks(days,current_layer):
    original_tasks = load_file()[current_layer]["Tasks"]
    today = datetime.today().date()
    upcoming_tasks = [
        task for task in original_tasks
        if not task["done"] and today <= pd.to_datetime(task["due_date"]).date() <= today + timedelta(days=days)
    ]
    expired_tasks =[task for task in original_tasks if not task["done"] and pd.to_datetime(task["due_date"]).date()<today]
    save_file(original_tasks,current_layer,reminder_tasks=upcoming_tasks,expired_tasks=expired_tasks)

def pin_task(tasks, task_id, is_filtered,current_layer):
    original_tasks = load_file()[current_layer]["Tasks"]
    target_tasks = original_tasks if is_filtered else tasks
    index = next(i for i, t in enumerate(target_tasks) if t["ID"] == task_id)
    target_tasks[index]["pinned"] = not target_tasks[index]["pinned"]
    save_file(target_tasks,current_layer)
