# 🏛 Standard Library Imports
from datetime import datetime  # Changed from `import datetime`
import importlib.util
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

# 🛠 Third-Party Library Imports
import ipynbname
import ipywidgets as widgets
import networkx as nx
import numpy as np
import pandas as pd
from IPython.display import HTML, display
from pyvis.network import Network

# 📂 Project-Specific Imports
from informant_class import *

class TaskManager:
    def __init__(self, project_manager_path, notebook_path=None, trial_id=None, ontology_name=None, project_build=None, discount_rate=0.1):
        """Initialize TaskManager with paths to task storage files and a discount rate for time-sensitive tasks."""
        self.base_path = project_manager_path
        self.tasks_file = os.path.join(self.base_path, 'tasks.json')
        self.completed_tasks_file = os.path.join(self.base_path, 'completed_tasks.json')
        self.active_task = None  # Currently checked out task
        self.notebook_path = notebook_path  # Path to the current notebook
        self.trial_id = trial_id  # Trial ID
        self.ontology_name = ontology_name  # Ontology name
        self.project_build = project_build  # Project build
        self.discount_rate = discount_rate  # Discount rate for time-sensitive tasks
        
        # Initialize files if they don't exist
        for file in [self.tasks_file, self.completed_tasks_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)  # Initialize with an empty dictionary
    
    def _load_tasks(self):
        """Load active tasks from JSON file with error handling and enforce impact score and due date propagation."""
        try:
            with open(self.tasks_file, 'r') as f:
                # Check if the file is empty
                content = f.read().strip()
                if not content:
                    return {}  # Return an empty dictionary if the file is empty
                tasks = json.loads(content)
                
                # Enforce that if due_date is defined (i.e. non-empty and not "nan"), time_sensitive is True.
                for task_id, task in tasks.items():
                    due_date = task.get("due_date")
                    if due_date not in [None, "", "nan"]:
                        task["time_sensitive"] = True
                    else:
                        task["time_sensitive"] = False
                
                # Enforce that each child task's due date is at least as soon as its parent's.
                # That is, if a parent's due_date is defined and the child's due_date is missing or later than the parent's,
                # update the child's due_date to match the parent's.
                changed = True
                while changed:
                    changed = False
                    for task_id, task in tasks.items():
                        parent_id = task.get("parent_task")
                        if parent_id and parent_id in tasks:
                            parent_due = tasks[parent_id].get("due_date")
                            if parent_due not in [None, "", "nan"]:
                                try:
                                    parent_due_dt = datetime.fromisoformat(parent_due)
                                except ValueError:
                                    continue  # Skip if parent's due_date is invalid.
                                
                                child_due = task.get("due_date")
                                # If child's due_date is missing, set it to parent's due_date.
                                if child_due in [None, "", "nan"]:
                                    task["due_date"] = parent_due
                                    changed = True
                                else:
                                    try:
                                        child_due_dt = datetime.fromisoformat(child_due)
                                    except ValueError:
                                        continue  # Skip if child's due_date is invalid.
                                    # If the child's due date is later than the parent's, update it.
                                    if child_due_dt > parent_due_dt:
                                        task["due_date"] = parent_due
                                        changed = True
                
                # Enforce that each child task's impact_score is at least as high as its parent's,
                # propagating recursively up the chain.
                memo = {}
                def get_max_impact(tid, visited=None):
                    """Recursively return the maximum impact score along the parent chain for task tid."""
                    if visited is None:
                        visited = set()
                    if tid in memo:
                        return memo[tid]
                    if tid in visited:
                        # Cycle detected (shouldn't happen in a DAG); return current impact.
                        return tasks[tid].get("impact_score", 0)
                    visited.add(tid)
                    
                    task = tasks[tid]
                    own_impact = task.get("impact_score", 0)
                    parent_id = task.get("parent_task")
                    if parent_id and parent_id in tasks:
                        parent_max = get_max_impact(parent_id, visited)
                        max_impact = max(own_impact, parent_max)
                    else:
                        max_impact = own_impact
                    memo[tid] = max_impact
                    return max_impact
                
                # Update each task's impact_score using the recursive function.
                for tid in tasks:
                    tasks[tid]["impact_score"] = get_max_impact(tid)
            
                return tasks
        except json.JSONDecodeError:
            print(f"Error: {self.tasks_file} contains invalid JSON. Initializing with an empty dictionary.")
            return {}
        except FileNotFoundError:
            print(f"Error: {self.tasks_file} not found. Initializing with an empty dictionary.")
            return {}    

    def _save_tasks(self, tasks):
        """Save active tasks to JSON file, ensuring Path objects are converted to strings."""
        def convert_paths(obj):
            """Recursively convert Path objects to strings."""
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(v) for v in obj]
            elif isinstance(obj, Path):
                return str(obj)
            else:
                return obj
        
        # Convert any Path objects to strings
        tasks = convert_paths(tasks)
        
        with open(self.tasks_file, 'w') as f:
            json.dump(tasks, f, indent=4)
    
    def compute_effective_priority(self, task, discount_rate=None):
        """
        Compute effective priority for a task.
        - For time sensitive tasks with a valid due_date, effective priority = impact_score * exp(-discount_rate * time_until_due_days)
        - Otherwise, returns impact_score.
        
        Parameters:
        task: dict representing the task.
        discount_rate: Optional; if provided, use this discount rate. Otherwise, use self.discount_rate.
        """
        if discount_rate is None:
            discount_rate = self.discount_rate

        # Only attempt discounting if the task is marked time sensitive
        if task.get("time_sensitive", False):
            due_date_str = task.get("due_date")
            # If due_date is missing or not a valid string, treat the task as time-insensitive.
            if not isinstance(due_date_str, str) or not due_date_str.strip():
                return task.get("impact_score", 0)
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except ValueError as e:
                raise ValueError(f"Invalid due date format: '{due_date_str}'. Expected ISO format, e.g., '2025-02-25T17:00:00'.") from e
            # Calculate time until due in days
            time_until_due = (due_date - datetime.now()).total_seconds() / (60 * 60 * 24)
            return task["impact_score"] * math.exp(-discount_rate * time_until_due)
        else:
            return task.get("impact_score", 0)
    
    def sort_tasks_by_effective_priority(self, discount_rate=None):
        """
        Sorts tasks so that time sensitive tasks are shown first, ordered by their effective priority (descending),
        followed by time insensitive tasks ordered by their impact score.
        
        Parameters:
        discount_rate: Optional; if provided, this discount rate is used for computing effective priority.
                        Otherwise, self.discount_rate is used.
        """
        tasks = self._load_tasks()
        used_discount_rate = discount_rate if discount_rate is not None else self.discount_rate

        def sort_key(task):
            # Boolean flag: 1 if time_sensitive, else 0 (we want True first)
            is_time_sensitive = task.get("time_sensitive", False)
            effective_priority = self.compute_effective_priority(task, discount_rate=used_discount_rate)
            # Negative values so that higher priorities come first
            return (-int(is_time_sensitive), -effective_priority)

        # Convert tasks to a list for sorting
        tasks_list = list(tasks.values())
        tasks_list.sort(key=sort_key)
        return tasks_list
    
    def create_task(self, name=None, description=None, impact_score=None, parent_task=None):
        """
        Create a new task with metadata.
        If name, description, or impact_score are not provided, the user will be prompted interactively.
        Automatically infers project_build, explorer, trial_id, and ontology from the provided context.
        Also prompts for time sensitivity and due date (if applicable) as well.
        """
        # Use the provided project_build or infer it from the base path
        project_build = self.project_build if self.project_build else os.path.basename(os.path.dirname(self.base_path))
        explorer = os.path.basename(self.notebook_path) if self.notebook_path else "unknown"  # Current notebook name
        trial_id = self.trial_id  # Trial ID from initialization
        ontology = self.ontology_name  # Ontology name from initialization
        
        # Prompt for task name if not provided
        if name is None:
            name = input("Enter task name: ").strip()
            if not name:
                print("Task name cannot be empty. Please try again.")
                return None
        
        # Prompt for task description if not provided
        if description is None:
            description = input("Enter task description: ").strip()
            if not description:
                print("Task description cannot be empty. Please try again.")
                return None
        
        # Prompt for task priority if not provided
        if impact_score is None:
            impact_score_input = input("Enter task impact score (default 0): ").strip()
            impact_score = float(impact_score_input) if impact_score_input else 0
        
        # Prompt for time sensitivity
        time_sensitive_input = input("Is this task time sensitive? (y/n, default n): ").strip().lower()
        time_sensitive = time_sensitive_input in ('y', 'yes')
        
        # If time sensitive, prompt for due date (in ISO format, e.g., 2025-02-25T17:00:00)
        due_date_str = None
        if time_sensitive:
            due_date_str = input("Enter due date (ISO format, e.g., 2025-02-25T17:00:00): ").strip()
            if not due_date_str:
                print("Due date is required for time sensitive tasks. Please try again.")
                return None

        # Load existing tasks
        tasks = self._load_tasks()
        
        # Define the ID length and maximum possible IDs
        id_length = 8
        MAX_IDS = 16 ** id_length  # Total possible unique IDs with the given length
        
        # Check if the task list is saturated
        if len(tasks) >= MAX_IDS:
            raise Exception("Task list saturated: maximum unique IDs reached. Please increase the ID length.")
        
        # Generate a unique task ID with a limited number of attempts
        attempts = 0
        max_attempts = 10000
        task_id = str(uuid.uuid4()).replace('-', '')[:id_length]
        while task_id in tasks:
            attempts += 1
            if attempts >= max_attempts:
                raise Exception("Failed to generate a unique task ID after many attempts. Consider using a longer ID.")
            task_id = str(uuid.uuid4()).replace('-', '')[:id_length]
        
        # Create the new task dictionary including the new fields
        new_task = {
            "task_id": task_id,
            "name": name,
            "description": description,
            "impact_score": impact_score,
            "time_sensitive": time_sensitive,
            "due_date": due_date_str,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "parent_task": parent_task,
            "child_tasks": [],
            "project_build": project_build,
            "explorer": explorer,
            "trial_id": trial_id,
            "ontology": ontology,
            "history": [{
                "action": "created",
                "timestamp": datetime.now().isoformat(),
                "explorer": explorer,
                "trial_id": trial_id
            }],
            "checked_out": False,
            "last_checkout": None
        }
        
        # Update parent task's children if parent exists
        if parent_task and parent_task in tasks:
            tasks[parent_task]["child_tasks"].append(task_id)
            tasks[parent_task]["history"].append({
                "action": "child_task_added",
                "child_task_id": task_id,
                "timestamp": datetime.now().isoformat()
            })
        
        # Save the new task
        tasks[task_id] = new_task
        self._save_tasks(tasks)
        
        print(f"Task created with ID: {task_id}")
        return task_id
        
    import functools
    import networkx as nx

    def show_task_table(self, filter_expr=None, discount_rate=None, suppress_discount_annotation=False, reverse_order=False, scroll_height="400px"):
        """
        Display tasks in a searchable/sortable table format inside a scrollable container.

        This version builds a task graph to enforce that a child task appears before its parent,
        while preserving the overall order defined by:
        - Time sensitivity (time-sensitive tasks come first)
        - Discounted priority (for time-sensitive tasks, computed as impact_score * exp(-discount_rate * time_until_due); 
            for time-insensitive tasks, simply the impact_score)

        Optionally, a discount_rate can be provided; otherwise the task manager's discount_rate is used.
        If reverse_order is True, the final ordering is reversed.
        scroll_height: CSS height of the scrollable container (default "400px").
        """
        tasks = self._load_tasks()
        if not tasks:
            print("No active tasks found.")
            return

        # Determine discount rate to use.
        used_discount_rate = discount_rate if discount_rate is not None else self.discount_rate

        # Ensure each task has proper time_sensitive flag and compute discounted_priority.
        for tid, task in tasks.items():
            due = task.get("due_date")
            # If due_date is defined and not empty or "nan", mark as time sensitive.
            if due not in [None, "", "nan"]:
                task["time_sensitive"] = True
            else:
                task["time_sensitive"] = False
            # Compute discounted priority (for time-insensitive tasks, this returns the impact_score).
            task["discounted_priority"] = self.compute_effective_priority(task, discount_rate=used_discount_rate)

        if not suppress_discount_annotation:
            print(f"Discount rate used for computing effective priority: {used_discount_rate}")

        # Build the directed graph with reversed edge direction:
        # For each task, if it has a parent, add an edge from child to parent.
        G = nx.DiGraph()
        for tid in tasks:
            G.add_node(tid)
        for tid, task in tasks.items():
            parent = task.get("parent_task")
            if parent and parent in tasks:
                # Reversed edge: from child (tid) to parent.
                G.add_edge(tid, parent)

        # Perform lexicographical topological sort.
        # The key orders tasks so that time-sensitive tasks come first and, among those,
        # higher discounted_priority tasks come first.
        order = list(nx.lexicographical_topological_sort(
            G,
            key=lambda tid: (not tasks[tid].get("time_sensitive", False), -tasks[tid].get("discounted_priority", 0))
        ))

        if reverse_order:
            order = order[::-1]

        # Reorder tasks according to the computed topological order.
        ordered_tasks = [tasks[tid] for tid in order]

        # Convert to DataFrame.
        df_final = pd.DataFrame(ordered_tasks)

        # Apply filter if provided.
        if filter_expr:
            try:
                df_final = df_final.query(filter_expr)
            except Exception as e:
                print(f"Invalid filter expression: {filter_expr}")

        # Specify columns to display.
        display_cols = [
            'task_id', 'name', 'description', 'impact_score', 'due_date', 'time_sensitive', 'discounted_priority',
            'status', 'created_at', 'checked_out', 'parent_task', 
            'project_build', 'explorer', 'trial_id', 'ontology'
        ]
        df_final = df_final[display_cols]

        # Wrap the table in a scrollable container.
        styled_df = df_final.style.set_properties(**{
            'text-align': 'left',
            'white-space': 'pre-wrap'
        }).set_table_styles([{
            'selector': 'th',
            'props': [('text-align', 'left')]
        }])

        html_table = styled_df.to_html()
        scrollable_html = f"""
        <div style="height: {scroll_height}; overflow-y: auto; border: 1px solid #ccc; padding: 5px;">
            {html_table}
        </div>
        """

        from IPython.display import HTML, display
        display(HTML(scrollable_html))
        return df_final

    def search_tasks(self, query=None):
        """Interactive task search with filtering."""
        if query is None:
            query = input("Enter search filter (e.g., 'impact_score > 5' or 'status == \"active\"'): ")
        return self.show_task_table(query)
    
    def checkout_task(self, task_id=None, discount_rate=None):
        """Check out a task to work on."""
        if task_id is None:
            print("Available tasks:")
            # Display the table in reverse order for easier selection of high-priority tasks
            self.show_task_table(reverse_order=False, discount_rate=discount_rate)
            task_id = input("\nEnter task ID to check out: ").strip()
        
        tasks = self._load_tasks()
        if task_id in tasks:
            # If there's already a checked out task, check it back in
            if self.active_task:
                self._checkin_task_internal(self.active_task)
            
            tasks[task_id]["checked_out"] = True
            tasks[task_id]["last_checkout"] = datetime.now().isoformat()
            tasks[task_id]["history"].append({
                "action": "checked_out",
                "timestamp": datetime.now().isoformat()
            })
            
            self.active_task = task_id
            self._save_tasks(tasks)
            print(f"Checked out task: {tasks[task_id]['name']}")
            return True
        else:
            print("Task not found!")
            return False
    
    def checkin_task(self):
        """Check in the currently active task."""
        if self.active_task:
            self._checkin_task_internal(self.active_task)
            self.active_task = None
            print("Task checked in.")
        else:
            print("No task currently checked out.")
    
    def _checkin_task_internal(self, task_id):
        """Internal method for checking in a task."""
        tasks = self._load_tasks()
        if task_id in tasks:
            tasks[task_id]["checked_out"] = False
            tasks[task_id]["history"].append({
                "action": "checked_in",
                "timestamp": datetime.now().isoformat()
            })
            self._save_tasks(tasks)
    
    def shelve_this_task(self):
        """Shelve the currently checked out task."""
        if self.active_task:
            self.shelve_task(self.active_task)
        else:
            print("No task currently checked out.")
    
    def shelve_task(self, task_id=None):
        """Move a task to the completed file with 'shelved' status."""
        if task_id is None:
            print("Available tasks:")
            self.show_task_table()
            task_id = input("\nEnter task ID to shelve: ").strip()
        
        tasks = self._load_tasks()
        completed_tasks = self._load_completed_tasks()
        
        if task_id in tasks:
            task = tasks[task_id]
            shelve_time = datetime.now().isoformat()
            task["shelved_at"] = shelve_time
            task["status"] = "shelved"
            task["history"].append({
                "action": "shelved",
                "timestamp": shelve_time
            })
            
            completed_tasks[task_id] = task
            del tasks[task_id]
            
            if self.active_task == task_id:
                self.active_task = None
            
            self._save_tasks(tasks)
            self._save_completed_tasks(completed_tasks)
            print(f"Task '{task['name']}' has been shelved.")
            return True
        else:
            print("Task not found!")
            return False
    
    def get_task_graph(self, include_completed=False):
        """Generate a networkx graph of tasks and their relationships."""
        G = nx.DiGraph()
        
        # Add active tasks
        tasks = self._load_tasks()
        for task_id, task in tasks.items():
            G.add_node(task_id, **task)
            
            # Add edges for parent-child relationships
            if task["parent_task"]:
                G.add_edge(task["parent_task"], task_id)
        
        # Optionally add completed tasks
        if include_completed:
            completed_tasks = self._load_completed_tasks()
            for task_id, task in completed_tasks.items():
                G.add_node(task_id, **task)
                if task["parent_task"]:
                    G.add_edge(task["parent_task"], task_id)
        
        return G
    
    def visualize_tasks(self, output_path=None, include_completed=False):
        """Create an interactive visualization of the task network."""
        G = self.get_task_graph(include_completed)
        net = Network(height="750px", width="100%", directed=True)
        
        # Add nodes with formatting
        for node in G.nodes(data=True):
            node_id = node[0]
            node_data = node[1]
            
            # Format node title (hover text)
            title = f"""
            Name: {node_data['name']}
            Priority: {node_data['impact_score']}
            Status: {node_data['status']}
            Created: {node_data['created_at']}
            """
            
            # Color based on status and priority
            if node_data['status'] == 'completed':
                color = '#aaaaaa'
            else:
                # Color intensity based on priority
                priority = float(node_data['priority'])
                color = f'rgb(0, 0, {min(255, max(100, 255 - abs(priority) * 10))})'
            
            net.add_node(node_id, title=title, label=node_data['name'], color=color)
        
        # Add edges
        for edge in G.edges():
            net.add_edge(edge[0], edge[1])
        
        if output_path:
            net.save(output_path)
        return net
    
    def filter_tasks(self, priority_min=None, priority_max=None, 
                    project_build=None, explorer=None, trial_id=None,
                    start_date=None, end_date=None):
        """Filter tasks based on various criteria."""
        tasks = self._load_tasks()
        filtered_tasks = {}
        
        for task_id, task in tasks.items():
            include = True
            
            if priority_min is not None and task['priority'] < priority_min:
                include = False
            if priority_max is not None and task['priority'] > priority_max:
                include = False
            if project_build and task['project_build'] != project_build:
                include = False
            if explorer and task['explorer'] != explorer:
                include = False
            if trial_id and task['trial_id'] != trial_id:
                include = False
            
            task_date = datetime.fromisoformat(task['created_at'])
            if start_date and task_date < datetime.fromisoformat(start_date):
                include = False
            if end_date and task_date > datetime.fromisoformat(end_date):
                include = False
            
            if include:
                filtered_tasks[task_id] = task
        
        return filtered_tasks
    
    def _load_completed_tasks(self):
        """Load completed tasks from JSON file."""
        with open(self.completed_tasks_file, 'r') as f:
            return json.load(f)
    
    def _save_completed_tasks(self, tasks):
        """Save completed tasks to JSON file."""
        with open(self.completed_tasks_file, 'w') as f:
            json.dump(tasks, f, indent=4)

def initialize_task_manager(project_manager_path, notebook_path=None, trial_id=None, ontology_name=None, project_build=None):
    """Initialize the TaskManager with the project manager path, notebook path, trial ID, ontology name, and project build."""
    return TaskManager(project_manager_path, notebook_path, trial_id, ontology_name, project_build)

##########################################################################################

# Function to import module from file path
def import_module_from_path(module_name, path):
    if path not in sys.path:
        sys.path.append(os.path.dirname(path))
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module # Register the module
    return module

# Function to save informant dataframes
def save_informant_dataframes(idfs, formatted_date, trial_id, informants_dir):
    #informants_dir = this_project_directory + '/informants'
    for inf_df_name in idfs.keys():
        # Construct the file path
        this_df_pkl_path = os.path.join(informants_dir, formatted_date, trial_id, inf_df_name + '.pkl')
        # Get the directory part of the file path
        output_dir = os.path.dirname(this_df_pkl_path)

        # Debugging statement for output_dir
        print(f'Output directory: {output_dir}')

        try:
            # Ensure the directory exists
            os.makedirs(output_dir, exist_ok=True)
            print(f'Directory created or already exists: {output_dir}')
        except Exception as e:
            print(f'Error creating directory: {e}')

        # Save the DataFrame to the file path
        idfs[inf_df_name].df.to_pickle(this_df_pkl_path)

def create_symlink(target, link_name):
    """
    Create a symbolic link pointing to target named link_name.
    If the link_name already exists, prompt the user to overwrite or rename.

    Parameters:
    target (str): The path to the target directory.
    link_name (str): The path to the symbolic link to be created.
    """
    try:
        # Ensure the directory structure exists
        link_dir = os.path.dirname(link_name)
        os.makedirs(link_dir, exist_ok=True)

        if os.path.exists(link_name) or os.path.islink(link_name):
            while True:
                user_input = input(f"Symbolic link {link_name} already exists. Do you want to overwrite it (O) or rename the new link (R)? ").strip().lower()
                if user_input == 'o':
                    if os.path.isdir(link_name):
                        shutil.rmtree(link_name)
                    else:
                        os.remove(link_name)
                    os.symlink(target, link_name)
                    print(f"Symbolic link overwritten: {link_name} -> {target}")
                    break
                elif user_input == 'r':
                    new_link_name = input("Please enter a new name for the symbolic link: ").strip()
                    os.symlink(target, new_link_name)
                    print(f"Symbolic link created: {new_link_name} -> {target}")
                    break
                else:
                    print("Invalid input. Please enter 'O' to overwrite or 'R' to rename.")
        else:
            os.symlink(target, link_name)
            print(f"Symbolic link created: {link_name} -> {target}")
    except OSError as e:
        print(f"Error creating symbolic link: {e}")

def log_informant_accession(directory, project_build, explorer, trial_id, ontology, max_entries=500):
    """Logs informant access in a JSON file, storing the latest accesses first."""
    accession_record_path = os.path.join(directory, "accession_record.json")

    # Ensure accession_record is always a dictionary
    if os.path.exists(accession_record_path) and os.path.getsize(accession_record_path) > 0:
        try:
            with open(accession_record_path, "r") as f:
                accession_record = json.load(f)

            # If the loaded log is a list (corrupt format), reset it
            if not isinstance(accession_record, dict):
                print(f"⚠ Warning: Incorrect JSON format detected at {accession_record_path}. Resetting accession record.")
                accession_record = {"explorers": {}}

        except json.JSONDecodeError:
            print(f"⚠ Warning: Corrupt JSON file detected at {accession_record_path}. Resetting accession record.")
            accession_record = {"explorers": {}}  # Reset log if it's corrupt
    else:
        accession_record = {"explorers": {}}  # Initialize structure

    # Ensure "explorers" key exists
    if "explorers" not in accession_record:
        accession_record["explorers"] = {}

    # Get or initialize explorer log list
    if explorer not in accession_record["explorers"]:
        accession_record["explorers"][explorer] = []

    # Create new log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "project_build": project_build,
        "trial_id": trial_id,
        "ontology": ontology
    }

    # Insert new entry at the beginning (reverse chronological order)
    accession_record["explorers"][explorer].insert(0, log_entry)

    # Keep only last N entries for this explorer
    accession_record["explorers"][explorer] = accession_record["explorers"][explorer][:max_entries]

    # Save updated log
    with open(accession_record_path, "w") as f:
        json.dump(accession_record, f, indent=4)

def inspect_accession_record(directory, explorer=None, project_build=None, trial_id=None, start_date=None, end_date=None, ontology=None, verbose=False):
    """
    Inspect and filter the accession_record.json file.
    
    Parameters:
        - directory (str): Path to the accession_record.json file.
        - explorer (str, optional): Filter by explorer path.
        - project_build (str, optional): Filter by project_build name.
        - trial_id (str, optional): Filter by trial ID.
        - start_date (str, optional): Filter by start date (YYYY-MM-DD).
        - end_date (str, optional): Filter by end date (YYYY-MM-DD).
        - verbose (bool, optional): If True, prints records in a readable format.

    Returns:
        - A Pandas DataFrame with filtered results.
        - A list of filtered access records (JSON-like).
    """
    accession_record_path = os.path.join(directory, "accession_record.json")

    # Check if the log file exists
    if not os.path.exists(accession_record_path) or os.path.getsize(accession_record_path) == 0:
        print(f"⚠ No access log found at {accession_record_path}.")
        return pd.DataFrame(), []

    # Load access log
    try:
        with open(accession_record_path, "r") as f:
            accession_record = json.load(f)
    except json.JSONDecodeError:
        print(f"⚠ Corrupt JSON detected at {accession_record_path}. Reset or fix manually.")
        return pd.DataFrame(), []

    # Flatten the log entries into a list for filtering
    records = []
    for explorer_key, entries in accession_record.get("explorers", {}).items():
        for entry in entries:
            records.append({
                "timestamp": entry["timestamp"],
                "explorer": explorer_key,
                "project_build": entry["project_build"],
                "trial_id": entry["trial_id"],
                "ontology": entry["ontology"]
            })

    # Convert to Pandas DataFrame
    df = pd.DataFrame(records)

    # Ensure timestamp is in datetime format
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Apply filters
    if explorer:
        df = df[df["explorer"] == explorer]
    if project_build:
        df = df[df["project_build"] == project_build]
    if trial_id:
        df = df[df["trial_id"] == trial_id]
    if start_date:
        df = df[df["timestamp"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["timestamp"] <= pd.to_datetime(end_date)]
    if ontology:
        df = df[df["ontology"] == ontology]

    # Sort by timestamp (most recent first)
    df = df.sort_values(by="timestamp", ascending=False)

    # Convert back to list of dictionaries for JSON-like output
    filtered_records = df.to_dict(orient="records")

    # Display results if verbose mode is enabled
    if verbose:
        if df.empty:
            print("⚠ No matching access log entries found.")
        else:
            print(df.to_string(index=False))  # Print in a readable format

    return df, filtered_records

def load_pickles_to_dict(directory):
    # Initialize an empty dictionary to store the dataframes
    idfs = {}
    
    # Iterate over all files in the given directory
    for filename in os.listdir(directory):
        # Check if the file has a .pkl extension
        if filename.endswith('.pkl'):
            # Construct the full file path
            file_path = os.path.join(directory, filename)
            # Load the pickle file into a pandas dataframe
            this_inf_dataframe = Informant_Dataframe()
            this_inf_dataframe.load_df(file_path)
            # Store the dataframe in the dictionary with the key as the filename without .pkl suffix
            key = filename[:-4]
            idfs[key] = this_inf_dataframe
    
    return idfs

def construct_parameter_combinations_df(algorithm, parameter_combination_generators):
    """
    Constructs an Informant Dataframe of parameter combinations for the Algorithm.
    parameter_combination_generators will be a dictionary containing lists of values for each parameter.
        Note: In general, it is possible to construct parameter combinations separately.
    """
    if parameter_combination_generators is not None:
        keys = list(parameter_combination_generators.keys())
        values = [parameter_combination_generators[key] for key in keys]

        # Generate all combinations of parameters using numpy
        parameter_combinations_array = np.array(np.meshgrid(*values)).T.reshape(-1, len(values))
        parameter_combinations_list = [dict(zip(keys, combination)) for combination in parameter_combinations_array]
    else:
        parameter_combinations_list = []

    # Define a function to create Parameters
    def create_parameters(param_combination):
        return ont.Parameters(
            algorithm=algorithm,
            tags=[algorithm.name],
            parameter_descriptions=algorithm.parameter_descriptions,
            parameters=param_combination
        )

    # Using ThreadPoolExecutor to parallelize the creation of Parameters
    with ThreadPoolExecutor() as executor:
        parameters_list = list(executor.map(create_parameters, parameter_combinations_list))

    parameters_informant_dataframe = Informant_Dataframe()
    parameters_informant_dataframe.append(parameters_list)
    return parameters_informant_dataframe

def unpack_informant_params(param_combo, algorithm):
    # Get the algorithm's parameter descriptions
    parameter_descriptions = algorithm.parameter_descriptions
    #print('parameter_descriptions: ', parameter_descriptions)

    # Initialize the unpacked parameters dictionary
    unpacked_params = param_combo.parameters

    #print('param_combo: ', param_combo)

    #print('param_combo.parameters: ', param_combo.parameters)

    this_informant = param_combo.parameters['informant']

    # Iterate over the parameter descriptions
    for param_key, description in parameter_descriptions.items():
        if param_key in this_informant.__dict__:
            #print('param_key: ', param_key)
            # Extract the attribute from the informant if it exists
            unpacked_params[param_key] = this_informant.__dict__[param_key]
    #print('unpacked_params: ', unpacked_params)
    return ont.Parameters(algorithm=algorithm, parameters=unpacked_params)

def get_basename(path, num_parents=0):
    parts = []
    current_path = path

    # Collect the specified number of parent directories
    for _ in range(num_parents + 1):  # +1 to include the basename itself
        current_path, tail = os.path.split(current_path)
        if tail:
            parts.append(tail)
        else:
            break

    # Reverse the parts to get the correct order and join them with the OS separator
    return os.path.join(*reversed(parts))

# To build commands that will construct the file for each output informant, we can first format the Parameters into a command line string:
def build_command_line_params(params_dict, use_keys=True):
    def get_location(value):
        return getattr(value, 'location', value) if not isinstance(value, str) else value

    params_list = []
    if use_keys:
        for key, value in params_dict.items():
            if key != 'informant':
                param_value = get_location(value)
                if isinstance(param_value, str):
                    # For the 'sep' parameter, convert the tab character to '\t'
                    if key == 'sep':
                        param_value = repr(param_value)[1:-1]  # Converts '\t' to '\\t'
                params_list.append(f"--{key.replace('_', '-')} {param_value}")
    else:
        for value in params_dict.values():
            param_value = get_location(value)
            params_list.append(f"{param_value}")
    return ' '.join(params_list)

# We can also define a function that will run a command, although this may not be necessary at the moment:
def run_command(command):
    try:
        print(f"Executing: {command}")
        result = subprocess.run(command, shell=True, check=True)
        return f"Command succeeded: {command}"
    except subprocess.CalledProcessError as e:
        return f"Command failed: {command} with return code {e.returncode}"

# Define a function to remove a directory
def remove_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
        return f"Removed: {directory}"
    else:
        return f"Directory not found: {directory}"

