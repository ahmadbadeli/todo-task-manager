import streamlit as st
import pandas as pd
from datetime import datetime
from functions import save_file, add_task, toggle_done, delete_task, edit_task, remove_category, add_category, upcoming_tasks
from functions import pin_task,load_file,validate_task_data,temp_msg,csv_to_task
from functions import table_headers, modal
import time

st.set_page_config(page_title="To Do List",page_icon="📋")

# initialize
data = load_file()
layers = data["Layers"]

# layer control states
if 'current-layer' not in st.session_state:
    st.session_state['current-layer'] = layers[0]
current_layer = st.session_state['current-layer']

if 'prev-layer' not in st.session_state:
    st.session_state['prev-layer'] = current_layer

if st.session_state['prev-layer'] != current_layer:
    # reset session_state
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state['current-layer'] = current_layer
    st.session_state['prev-layer'] = current_layer

# Global Variables
categories = data[current_layer]["Categories"]
tasks = data[current_layer]["Tasks"]   
original_tasks = tasks
reminder = data[current_layer]["Reminder"]
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
    st.session_state['toggle-reminder'] = data[current_layer]["Reminder"]["status"]
if 'reminder-days-input' not in st.session_state:
    st.session_state['reminder-days-input'] = data[current_layer]["Reminder"]["days"]
if 'reminder-auto-update' not in st.session_state:
    st.session_state['reminder-auto-update'] = data[current_layer]["Reminder"]["auto_update"]

states = {
    "status" : st.session_state['toggle-reminder'],
    "days" : st.session_state["reminder-days-input"],
    "auto_update" : st.session_state['reminder-auto-update']
    }
# reset reminder check box and update states
if not states["status"]:
    # reset reminder
    save_file(original_tasks,current_layer,states_dict={"status": False, "days": 1, "auto_update": False},reminder_tasks=[],expired_tasks=[])
else:
    # update states
    save_file(original_tasks,current_layer,states_dict=states)

# reset inputs
if st.session_state.get('reset-inputs',False):
    st.session_state['priority-input'] = "No Priority"
    st.session_state['title-input'] = ''
    st.session_state['due-date-input'] = datetime.today()
    st.session_state.pop('reset-inputs')

# reset file
if st.session_state.get('reset-file',False):
    st.session_state.pop('import-file-upload')
    st.session_state.pop('reset-file')


# css
with open("styles.css",'r') as f:
    css_file = f.read()
st.markdown(f"<style>{css_file}</style>",unsafe_allow_html=True)

# sidebar
container = st.sidebar.empty()

st.sidebar.selectbox("Select Current Layer:",key="current-layer",options=layers)

layer_name = st.sidebar.text_input("Layer Name:",key='layer-input')
add_layer = st.sidebar.button("Add",key='add-layer-button')
if add_layer:
    if layer_name:
        if layer_name.lower() not in [layer.lower() for layer in layers]:
            layers.append(layer_name.title())
            container.success("Layer Added Successfully")
            time.sleep(1.5)
            container.empty()
            save_file(original_tasks,current_layer,layers=layers)
            st.rerun(scope='app')
        else:
            container.error("Layer Already Existed!!")
    else:
        container.error("Please enter a layer")

selected_layer = st.sidebar.selectbox("Select Layer:",key='layer-remove',options=layers)
remove_layer = st.sidebar.button("Remove",key='remove-layer-button')
if remove_layer:
    layers.remove(selected_layer)
    container.success("Layer Removed Successfully")
    time.sleep(1.5)
    container.empty()
    save_file(original_tasks,current_layer,layers=layers)
    st.rerun(scope='app')

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

# Import / Export Section
with st.container(key='import-export-section'):
    # Import
    st.markdown("##### Import from a CSV file",unsafe_allow_html=True)
    msg = st.empty()
    uploaded_file = st.file_uploader("Upload tasks file (csv only)", type=["csv"], key='import-file-upload')
    if uploaded_file: 
        if st.button('Import',key='import-button'):
            upload_status,imported_tasks,df = csv_to_task(uploaded_file)
            if upload_status:
                valid,message = validate_task_data(imported_tasks)
                if valid:
                    save_file(imported_tasks,current_layer,categories=list(df["category"].unique()))
                    st.session_state['reset-file'] = True
                    temp_msg(msg,"Data Imported Successfully")
                    st.rerun(scope='app')
                else:
                    st.error(message)
            else:
                st.error(imported_tasks)

    # Export
    if tasks:
        st.markdown("##### Export to CSV file",unsafe_allow_html=True)
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
        st.markdown("##### Tasks")
        with st.container(key="task-headers"):
            # st.markdown(' ')
            cols = st.columns([0.2,5,0.9,0.7,0.6])
            for i,table_header in enumerate(table_headers):
                cols[i].markdown(f"**{table_header}**")
        
        for i,task in enumerate(tasks):
            status = "done" if task["done"] else "pending"
            with st.container(key=f"task-container_{i}"):
                cols = st.columns([0.2,5,0.9,0.7,0.6])
                with cols[0]:
                    st.checkbox(" ", value=task["pinned"], key=f"pin_{task['ID']}", on_change=pin_task, args=(tasks, task["ID"], is_filtered, current_layer))
                    st.checkbox("📌", value=task["pinned"], key=f"min_pinned_{task['ID']}", on_change=pin_task, args=(tasks, task["ID"], is_filtered, current_layer))

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
                        <td style="width:10.5rem">{task['title']}</td>
                        <td style="width:5.7rem">{task['category']}</td>
                        <td style="white-space: nowrap;">{task['due_date']}</td>
                        <td>{status}</td>
                    </tr>
                    </table>
                    """
                    # for small screens
                    row_min = f"""
                    <div class="task-table-min" style="color:{color};">
                        <div class="task-table-min-title">{task['title']}</div>
                        <div style="color:black;font-weight:bold;width:50%;text-align:right">
                            <div>Category:</div>
                            <div>Due Date:</div>
                            <div>Status:</div>
                        </div>
                        <div style="width:50%;">
                            <div>{task['category']}</div>
                            <div>{task['due_date']}</div>
                            <div>{status}</div>
                        </div>
                    </div>
                    """
                    st.markdown(row, unsafe_allow_html=True)
                    st.markdown(row_min, unsafe_allow_html=True)

                with cols[2]:
                    st.button("❌",key=f'delete_{i}',on_click=delete_task,args=(tasks,i,is_filtered,current_layer))

                with cols[3]:
                    if st.button("📝",key=f'edit_{i}'):
                        st.session_state['edit_index'] = i
                        modal.open()

                with cols[4]:
                    prev_toggle_done_button = task["done"]
                    toggle_done_button = st.toggle(" ", value=task["done"], key=f'checkbox_{task["ID"]}')
                    if prev_toggle_done_button is not None and prev_toggle_done_button != toggle_done_button:
                        toggle_done(tasks, task["ID"], is_filtered,current_layer)
                        st.session_state["toggle_done_button"] = True
                        st.rerun(scope='app')
            
            
# Reminder
if st.toggle("Add a Reminder",key="toggle-reminder"):   
    with st.container(key='reminder-section'):
        st.markdown("##### Reminder:")
        cols = st.columns([4,1.2,1.7])
        with cols[0]:
            days = st.number_input("days until due date:",min_value = 1, step= 1, key = "reminder-days-input")
            st.session_state['reminder-days'] = days
            states["days"] = days
        
        with cols[1]:
            st.button("Set Days",key="reminder-run-button",on_click=upcoming_tasks,args=(days,current_layer,))

        with cols[2]:
            if st.toggle("auto update",key="reminder-auto-update"):
                if st.session_state["prev_tasks_len"] != tasks_len:
                    upcoming_tasks(days,current_layer)
                    st.session_state.pop("prev_tasks_len")
                    st.rerun(scope='app')
                
                elif st.session_state["edited"]:
                    upcoming_tasks(days,current_layer)
                    st.session_state.pop("edited")
                    st.rerun(scope='app')

                elif st.session_state.get("toggle_done_button",False):
                    upcoming_tasks(days,current_layer)
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
                    <td style="width:300px">{task['title']}</td>
                    <td style="width:100px">{task['category']}</td>
                    <td style="white-space: nowrap;">{task['due_date']}</td>
                    <td>{status}</td>
                </tr>
                </table>
                """
                # for Small Screens
                row_min = f"""
                <table class="reminder-table-min" style="color:{color};text-align:center;">
                <tr>
                    <td colspan='3' style="font-weight:bold">{task['title']}</td>
                </tr>
                <tr>
                    <td>{task['category']}</td>
                    <td style="white-space: nowrap;">{task['due_date']}</td>
                    <td>{status}</td>
                </tr>
                </table>
                """
                st.markdown(row_min, unsafe_allow_html=True)
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
                    <td style="width:300px">{task['title']}</td>
                    <td style="width:100px">{task['category']}</td>
                    <td style="white-space: nowrap;">{task['due_date']}</td>
                    <td>{status}</td>
                </tr>
                </table>
                """
                # for Small Screens
                row_min = f"""
                <table class="reminder-table-min" style="color:red;text-align:center;">
                <tr>
                    <td colspan='3' style="font-weight:bold">{task['title']}</td>
                </tr>
                <tr>
                    <td>{task['category']}</td>
                    <td style="white-space: nowrap;">{task['due_date']}</td>
                    <td>{status}</td>
                </tr>
                </table>
                """
                st.markdown(row_min, unsafe_allow_html=True)
                st.markdown(row, unsafe_allow_html=True)


with st.container(key="input-section"):
    # add or remove a category
    msg = st.empty()
    with st.container(key='edit-category-section'):
        st.markdown("##### add or remove a category")
        cols = st.columns([3,1.4,3,1])
        with cols[0]:
            category = st.selectbox("select",options=categories,key='remove-category')
        with cols[1]:
            st.button('remove',key='remove-category-button',on_click=remove_category,args=(category,msg,current_layer))
        with cols[2]:
            category = st.text_input("Write a category",key='add-category')
        with cols[3]:
            st.button('add',key='add-category-button',on_click=add_category,args=(category,msg,current_layer))

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
        msg = st.empty()
        if st.button("Add Task",key=f'add-task-button'):
            if title:
                due_date = pd.to_datetime(due_date).strftime("%Y-%m-%d")
                priority_symbol = {"🔴High":"🔴","🟡Medium":"🟡","🟢Low":"🟢","No Priority":""}
                title = f"{priority_symbol[priority]} {title}"
                add_task(title,category,due_date,msg,current_layer)
                st.session_state["reset-inputs"] = True
                st.rerun(scope='app')
            else:
                st.warning("Please enter a task before add it!!")

# Modal
if modal.is_open():
    with modal.container():
        index = st.session_state["edit_index"]
        pinned = st.toggle("Pin:",value = tasks[index]["pinned"])
        title = st.text_input("Edit Task: ",key='title-edit',value=tasks[index]["title"])
        category = st.selectbox("Edit Category",key='category-edit',options=categories,index=categories.index(tasks[index]["category"]))
        due_date = st.date_input("Edit Due Date",key='due-date-edit',value=pd.to_datetime(tasks[index]["due_date"]).date())
        status = st.radio("Change status:",key='edit-status',options=["pending","done"],index=1 if tasks[index]["done"] else 0)
        msg = st.empty()
        with st.container(key="modal-buttons-container"):
            with st.container(key="edit-task-container"):
                if st.button("Edit Task",key='edit-task-button'):
                    if title:
                        due_date = due_date.strftime("%Y-%m-%d")
                        edit_task(tasks,title,index,status,category,due_date,is_filtered,pinned,current_layer)
                        st.session_state["edit-task-opened"] = False
                        st.session_state["edited"] = True
                        st.rerun(scope='app')
                    else:
                        msg.warning("Task can not be empty!!")
            with st.container(key="cancel-modal-container"):
                if st.button("Cancel",key='cancel-btn'):
                    st.session_state["edit-task-opened"] = False
                    st.rerun(scope='app')
