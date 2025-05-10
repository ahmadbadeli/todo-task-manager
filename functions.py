import pandas as pd
import time
import json
from uuid import uuid4 as uuid
from datetime import timedelta, datetime
from streamlit_modal import Modal

# Static Variables
table_headers = ["📌","Task","Delete","Edit","Done"]
file_path = 'tasks.json'
modal = Modal(title="Edit Task",key='edit-task')

# Initialize
def load_file(filename=file_path):
    try:
        with open(filename,'r') as f:
            return json.load(f)

    except:
        return {'Tasks':[],'Categories':['Work','Personal'],'Reminder':{'status':False,'auto_update':False,'days':1,'tasks':[],'expired':[]}}

# functions
def save_file(tasks,categories=None,states_dict=None,filename=file_path,reminder_tasks=None,expired_tasks=None):
    # initialize
    if categories is None:
        categories = load_file()["Categories"]
    # initialize reminder
    if states_dict is None:
        status = load_file()["Reminder"]["status"]
        days = load_file()["Reminder"]["days"]
        auto_update = load_file()["Reminder"]["auto_update"]
    if states_dict:
        status = states_dict["status"]
        days = states_dict["days"]
        auto_update =   states_dict ["auto_update"]
    if reminder_tasks is None:
        reminder_tasks = load_file()["Reminder"]["tasks"]
    if expired_tasks is None:
        expired_tasks = load_file()["Reminder"]["expired"]
    # main
    tasks.sort(key=lambda x: x["due_date"]) # sort by date by default
    with open(filename,'w') as f:
        file = {'Tasks':tasks,'Categories':categories,'Reminder':{'status':status,'auto_update':auto_update,'days':days,'tasks':reminder_tasks,'expired':expired_tasks}}
        json.dump(file,f,indent=2)

def add_task(title,category,due_date):
    original_tasks = load_file()["Tasks"]
    new_task = {"title":title,'pinned':False,"done":False,"category":category,"due_date":due_date, "ID":str(uuid())}  
    original_tasks.append(new_task)
    save_file(original_tasks)

def toggle_done(tasks, task_id, is_filtered):
    original_tasks = load_file()["Tasks"]
    target_tasks = original_tasks if is_filtered else tasks
    index = next(i for i, t in enumerate(target_tasks) if t["ID"] == task_id)
    target_tasks[index]["done"] = not target_tasks[index]["done"]
    print(target_tasks[index]["done"])
    save_file(target_tasks)

def delete_task(tasks,index,is_filtered):
    original_tasks = load_file()["Tasks"]
    target_tasks = original_tasks if is_filtered else tasks
    tasks_id = tasks[index]["ID"]
    if is_filtered:
        index = [i for i, task in enumerate(original_tasks) if task["ID"] == tasks_id][0]
    del target_tasks[index]
    save_file(target_tasks)

def edit_task(tasks,title,index,status,category,due_date,is_filtered,pinned):
    original_tasks = load_file()["Tasks"]
    my_id = tasks[index]["ID"] # don't use it directly
    tasks_id = tasks[index]["ID"] # to prevent some error
    target_tasks = original_tasks if is_filtered else tasks
    if is_filtered:
        index = [i for i, task in enumerate(original_tasks) if task["ID"] == tasks_id][0]
    target_tasks[index]= {"title":title,"pinned":pinned,"done":True if status == "done" else False, "category":category, "due_date":due_date, "ID":my_id}
    save_file(target_tasks)

def temp_msg(container, msg, type=0):
    msg_types = {0: "success", 1: "error", 2: "warning"}
    getattr(container, msg_types[type])(msg)
    if type == 0:  
        time.sleep(1.5)
    else:
        time.sleep(2)

def remove_category(category,container,categories=None,tasks=None):
    # initialize
    if categories is None:
        categories = load_file()["Categories"]
    if tasks is None:
        tasks = load_file()["Tasks"]
    # function
    if len(categories) > 1:
        categories.remove(category)
        tasks = [task for task in tasks if task["category"] in categories]
        save_file(tasks,categories=categories)
        temp_msg(container,"Category Removed Seccessfully")
    else:
        temp_msg(container,"You can't delete all categories. 1 must be left.",type=1)

def add_category(category,container,categories=None,tasks=None):
    # initialize
    if categories is None:
        categories = load_file()["Categories"]
    if tasks is None:
        tasks = load_file()["Tasks"]
    # function
    if category:
        categories_lower = [i.lower() for i in categories]
        if category.lower() not in categories_lower:
            categories.append(category.title())
            save_file(tasks,categories=categories)
            temp_msg(container,"Category Added Successfully")
        else:
            temp_msg(container,"Category already existed",type=1)
    else:
        temp_msg(container,"You have to enter a category first",type=2)

def upcoming_tasks(days):
    original_tasks = load_file()["Tasks"]
    today = datetime.today().date()
    upcoming_tasks = [
        task for task in original_tasks
        if not task["done"] and today <= pd.to_datetime(task["due_date"]).date() <= today + timedelta(days=days)
    ]
    expired_tasks =[task for task in original_tasks if not task["done"] and pd.to_datetime(task["due_date"]).date()<today]
    save_file(original_tasks,reminder_tasks=upcoming_tasks,expired_tasks=expired_tasks)

def pin_task(tasks, task_id, is_filtered):
    original_tasks = load_file()["Tasks"]
    target_tasks = original_tasks if is_filtered else tasks
    index = next(i for i, t in enumerate(target_tasks) if t["ID"] == task_id)
    target_tasks[index]["pinned"] = not target_tasks[index]["pinned"]
    save_file(target_tasks)
