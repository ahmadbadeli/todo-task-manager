import streamlit as st
import pandas as pd
from datetime import datetime
from functions import save_file, add_task, toggle_done, delete_task, edit_task, remove_category, add_category, upcoming_tasks, pin_task,load_file
from functions import table_headers, modal
import time

st.set_page_config(page_title="To Do List",page_icon="📋")

# Global Variables
data = load_file()
categories = data["Categories"]
tasks = data["Tasks"]   
original_tasks = tasks
reminder = data["Reminder"]
is_filtered = False

# this part of inintializing happened bacause of sending functions in a seperate file then they cant share st.session_state directly
# and because we have to keep the values of input in Reminder section we cant do it without se.session_state otherwise it won't be live completely
# variable for auto update
tasks_len = len(tasks)
if "prev_tasks_len" not in st.session_state:
    st.session_state["prev_tasks_len"] = tasks_len
if 'edited' not in st.session_state:
    st.session_state['edited'] = False

# initialize Reminder inputs
if 'toggle-reminder' not in st.session_state:
    st.session_state['toggle-reminder'] = data["Reminder"]["status"]
if 'reminder-days-input' not in st.session_state:
    st.session_state['reminder-days-input'] = data["Reminder"]["days"]
if 'reminder-auto-update' not in st.session_state:
    st.session_state['reminder-auto-update'] = data["Reminder"]["auto_update"]

states = {
    "status" : st.session_state['toggle-reminder'],
    "days" : st.session_state["reminder-days-input"],
    "auto_update" : st.session_state['reminder-auto-update']
    }

# reset reminder check box and update states
if not states["status"]:
    # reset reminder
    save_file(original_tasks,states_dict={"status": False, "days": 1, "auto_update": False},reminder_tasks=[],expired_tasks=[])
else:
    # update states
    save_file(original_tasks,states_dict=states)

# css
with open("styles.css",'r') as f:
    css_file = f.read()
st.markdown(f"<style>{css_file}</style>",unsafe_allow_html=True)

# main program
st.title("To-Do List")

# overall Statistics
if original_tasks:
    tasks_status = [task["done"] for task in original_tasks]
    tasks_status_done = [i for i in tasks_status if i is True]
    st.info(f"**Progress: {len(tasks_status_done)} / {len(tasks_status)} is done. Progression: {(len(tasks_status_done)/len(tasks_status))*100:.2f}%**")
    today = datetime.today().date()
    today_tasks = [t for t in original_tasks if not t["done"] and pd.to_datetime(t["due_date"]).date() == today]
    st.success(f"Tasks remaining for today: {len(today_tasks)}")

# Filter Section
if tasks:
    with st.container(key='filter-section'):
        st.markdown(f"##### Filter section")
        output_categories = [task["category"] for task in tasks]
        output_categories = list(set(output_categories)) # change it to unique values
        cols = st.columns(2)
        due_dates = [pd.to_datetime(task["due_date"]).date() for task in tasks]
        with cols[0]:
            selected_categories = st.multiselect("Select category",options=output_categories,key="filter-category")
            start_date = st.date_input("From:",value=min(due_dates),key="filter-start-date")
        # Filter by Category
        if selected_categories:
            tasks = [task for task in tasks if task["category"] in selected_categories]
            is_filtered = True

        with cols[1]:
            status = st.multiselect("Status:",options=["pending","done"],key="filter-status")
            status = [stat == "done" for stat in status]
            end_date = st.date_input("To:",value=max(due_dates),key="filter-end-date")
        # Filter by Status
        if status:
            tasks = [task for task in tasks if task["done"] in status]
            is_filtered = True
        # Filter by Date
        tasks = [task for task in tasks if start_date <= pd.to_datetime(task['due_date']).date() <= end_date]
        due_dates_filtered = [pd.to_datetime(task["due_date"]).date() for task in tasks]
        if len(due_dates) != len(due_dates_filtered):
            is_filtered = True
        # Filter by Task Name
        search_task = st.text_input("Search Task:",key="search-task")
        if search_task:
            tasks = [task for task in tasks if task["title"].lower().find(search_task.lower()) != -1]
            is_filtered = True
        
        # Sort Pinned
        tasks.sort(key=lambda x: x["pinned"],reverse=True)

# Export Section
if tasks:
    cols = st.columns(2)
    with cols[0]:
        df = pd.DataFrame(original_tasks)
        st.download_button("Download Original Tasks",df.to_csv(index=False),file_name="tasks.csv",mime="text/csv")
    with cols[1]:
        df2 = pd.DataFrame(tasks)
        st.download_button("Download Filtered Tasks",df2.to_csv(index=False),file_name="tasks.csv",mime="text/csv")

# show tasks with edit and delete key and Pin
if tasks:
    with st.container(key="show-tasks"):
        st.markdown("##### Tasks:")
        cols = st.columns([0.2,5,0.9,0.7,0.6])
        for i,table_header in enumerate(table_headers):
            cols[i].markdown(f"**{table_header}**")
        
        for i,task in enumerate(tasks):
            status = "done" if task["done"] else "pending"
            with cols[0]:
                st.checkbox(" ", value=task["pinned"], key=f"pin_{task['ID']}", on_change=pin_task, args=(tasks, task["ID"], is_filtered))

            with cols[1]:
                show_date = pd.to_datetime(task["due_date"]).strftime("%B %d, %Y")
                due_date = pd.to_datetime(task["due_date"]).date()
                today_date = datetime.today().date()

                if due_date == today_date:
                    if task["done"]:
                        color = "green"
                    else:
                        color = "orange"
                elif due_date < today_date:
                    if task["done"]:
                        color = "gray"
                    else:
                        color = "red"
                else:
                    if task["done"]:
                        color = "green"
                    else:
                        color = "black"
                
                # due_date = due_date.strftime("%Y-%m-%d")

                row = f"""
                <table class="task-table" style="color:{color};">
                <tr>
                    <td style="width:45%;">{task['title']}</td>
                    <td style="width:5rem;">{task['category']}</td>
                    <td style="width:10rem;">{task['due_date']}</td>
                    <td style="width:5rem;">{status}</td>
                </tr>
                </table>
                """
                st.markdown(row, unsafe_allow_html=True)

            with cols[2]:
                st.button("delete",key=f'delete_{i}',on_click=delete_task,args=(tasks,i,is_filtered))

            with cols[3]:
                if st.button("Edit",key=f'edit_{i}'):
                    st.session_state['edit_index'] = i
                    modal.open()

            with cols[4]:
                prev_toggle_done_button = task["done"] if not None else None
                toggle_done_button = st.toggle(" ", value=task["done"], key=f'checkbox_{task["ID"]}')
                if prev_toggle_done_button is not None and prev_toggle_done_button != toggle_done_button:
                    toggle_done(tasks, task["ID"], is_filtered)
                    st.session_state["toggle_done_button"] = True

# Reminder
if st.toggle("Add a Reminder",key="toggle-reminder"):   
    with st.container(key='reminder-section'):
        st.markdown("##### Reminder:")
        cols = st.columns([4,1.5,1])
        with cols[0]:
            days = st.number_input("days until due date:",min_value = 1, step= 1, key = "reminder-days-input")
            st.session_state['reminder-days'] = days
            states["days"] = days
        
        with cols[1]:
            st.button("Set Days",key="reminder-run-button",on_click=upcoming_tasks,args=(days,))

        with cols[2]:
            if st.toggle("auto update",key="reminder-auto-update"):
                if (st.session_state["prev_tasks_len"] != tasks_len):
                    upcoming_tasks(days)
                    st.session_state.pop("prev_tasks_len")
                    st.rerun(scope='app')
                
                elif st.session_state["edited"]:
                    upcoming_tasks(days)
                    st.session_state.pop("edited")
                    st.rerun(scope='app')
                
                elif st.session_state.get("toggle_done_button",False):
                    upcoming_tasks(days)
                    st.session_state.pop("toggle_done_button")
                    st.rerun(scope='app')
                
        # Show Upcoming Tasks
        if reminder["tasks"]:
            st.markdown("**upcoming tasks:**")
            for i,task in enumerate(reminder["tasks"]):
                status = "done" if task["done"] else "pending"
                show_date = pd.to_datetime(task["due_date"]).strftime("%B %d, %Y")
                due_date = pd.to_datetime(task["due_date"]).date()
                today_date = datetime.today().date()

                if due_date == today_date:
                    color = "orange"
                elif due_date < today_date:
                    color = "red"
                else:
                    color = "black"

                row = f"""
                <table class="reminder-table" style="color:{color};">
                <tr>
                    <td style="width:45%;">{task['title']}</td>
                    <td style="width:5rem;">{task['category']}</td>
                    <td style="width:10rem;">{task['due_date']}</td>
                    <td style="width:5rem;">{status}</td>
                </tr>
                </table>
                """
                st.markdown(row, unsafe_allow_html=True)
        # show Expired Tasks
        if reminder["expired"]:
            st.markdown("**expired tasks:**")
            for i,task in enumerate(reminder["expired"]):
                status = "done" if task["done"] else "pending"
                show_date = pd.to_datetime(task["due_date"]).strftime("%B %d, %Y")
                due_date = pd.to_datetime(task["due_date"]).date()
                today_date = datetime.today().date()

                row = f"""
                <table class="reminder-table" style="color:red;">
                <tr>
                    <td style="width:45%;">{task['title']}</td>
                    <td style="width:5rem;">{task['category']}</td>
                    <td style="width:10rem;">{task['due_date']}</td>
                    <td style="width:5rem;">{status}</td>
                </tr>
                </table>
                """
                st.markdown(row, unsafe_allow_html=True)



# add or remove a category
with st.container(key='edit-category-section'):
    st.markdown("##### add or remove a category")
    msg = st.empty()
    cols = st.columns([3,1.1,3,1])
    with cols[0]:
        category = st.selectbox("select",options=categories,key='remove-category')
    with cols[1]:
        st.button('remove',key='remove-category-button',on_click=remove_category,args=(category,msg,))
    with cols[2]:
        category = st.text_input("Write a category",key='add-category')
    with cols[3]:
        st.button('add',key='add-category-button',on_click=add_category,args=(category,msg,))

# add a task
with st.container(key="task-input"):
    st.markdown("##### Add a Task")
    cols = st.columns(2)
    with cols[0]:
        title = st.text_input("New Task: ",key='title-input')
        priority = st.selectbox("Priority:",key='priority-input',options=["🔴High","🟡Medium","🟢Low","No Priority"],index=3)
    with cols[1]:
        category = st.selectbox("Category:",key='category-input',options=categories)
        due_date = st.date_input("Due Date:",key="due-date-input",value=datetime.today())
    if st.button("Add Task",key=f'add-task-button'):
        if title:
            due_date = pd.to_datetime(due_date).strftime("%Y-%m-%d")
            priority_symbol = {"🔴High":"🔴","🟡Medium":"🟡","🟢Low":"🟢","No Priority":""}
            title = f"{priority_symbol[priority]} {title}"
            add_task(title,category,due_date)
            st.rerun(scope='app')
        else:
            st.warning("Please enter a task before add it!!")

if modal.is_open():
    with modal.container():
        index = st.session_state["edit_index"]
        pinned = st.toggle("Pin:",value = tasks[index]["pinned"])
        title = st.text_input("Edit Task: ",key='title-edit',value=tasks[index]["title"])
        category = st.selectbox("Edit Category",key='category-edit',options=categories,index=categories.index(tasks[index]["category"]))
        due_date = st.date_input("Edit Due Date",key='due-date-edit',value=pd.to_datetime(tasks[index]["due_date"]).date())
        status = st.radio("Change status:",key='edit-status',options=["pending","done"],index=1 if tasks[index]["done"] else 0)
        msg = st.empty()
        cols = st.columns(2)
        with cols[0]:
            if st.button("Edit Task",key='edit-task-button'):
                if title:
                    due_date = due_date.strftime("%Y-%m-%d")
                    edit_task(tasks,title,index,status,category,due_date,is_filtered,pinned)
                    st.session_state["edit-task-opened"] = False
                    st.session_state["edited"] = True
                    st.rerun(scope='app')
                else:
                    msg.warning("Task can not be empty!!")
        with cols[1]:
            if st.button("Cancel",key='cancel-btn'):
                st.session_state["edit-task-opened"] = False
                st.rerun(scope='app')

