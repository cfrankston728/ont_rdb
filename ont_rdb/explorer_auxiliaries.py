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

import re
import math
import textwrap
import base64
import math

def format_node_label(task_id, name):
    """
    Format the node label by including the task_id and wrapping the task name.
    Inserts zero-width spaces after dashes, slashes, and underscores to allow optional breaks.
    """
    if not name:
        return task_id  # fallback if no name provided

    # Use a lambda function to insert a zero-width space (U+200B) after special characters.
    new_name = re.sub(r'([/_-])', lambda m: m.group(1) + '\u200b', name)

    # Determine a wrap width as the square root of the length (at least a minimum width)
    wrap_width = max(15, int(2*math.sqrt(len(new_name))))

    # Wrap the text using textwrap; the zero-width spaces allow breaks without forcing them.
    wrapped_name = textwrap.fill(new_name, width=wrap_width, break_long_words=False)

    # Prepend the task_id with a newline.
    label = f"{task_id}\n{wrapped_name}"
    return label

def create_clock_svg(node_size, ratio, fill_color="orange"):
    radius = node_size / 2.0 - 2  # subtract a bit for stroke width
    circumference = 2 * math.pi * radius
    dash_length = ratio * circumference
    svg = f'''
    <svg width="{node_size}" height="{node_size}" xmlns="http://www.w3.org/2000/svg">
      <!-- Background circle filled with the node color -->
      <circle cx="{node_size/2}" cy="{node_size/2}" r="{radius}" fill="{fill_color}" />
      <!-- Red clock outline showing effective priority -->
      <circle cx="{node_size/2}" cy="{node_size/2}" r="{radius}"
              fill="none" stroke="red" stroke-width="4"
              stroke-dasharray="{dash_length} {circumference}" 
              transform="rotate(-90 {node_size/2} {node_size/2})" />
    </svg>
    '''
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("utf-8")

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
            if attempts % 100 == 0:
                print(f"Unique ID generation: {attempts} attempts so far.")
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

    def task_table(self, filter_expr=None, discount_rate=None, suppress_discount_annotation=False, 
                        reverse_order=False, scroll_height="400px", time_filter="all", display_output=False):
        """
        Display tasks in a searchable/sortable table format inside a scrollable container.
        
        Parameters:
          filter_expr: (optional) a Pandas query string to further filter the DataFrame.
          discount_rate: (optional) discount rate used for computing effective priority.
          suppress_discount_annotation: (optional) if True, does not print the discount rate.
          reverse_order: (optional) if True, reverses the final ordering.
          scroll_height: (optional) CSS height of the scrollable container.
          time_filter: (optional) 'all', 'sensitive', or 'insensitive' to show only tasks that are time sensitive or not.
        """
        tasks = self._load_tasks()
        
        # Filter tasks by time sensitivity if required.
        if time_filter not in ("all", "sensitive", "insensitive"):
            print("Invalid time_filter value. Must be 'all', 'sensitive', or 'insensitive'. Showing all tasks.")
            time_filter = "all"
        if time_filter == "sensitive":
            tasks = {tid: task for tid, task in tasks.items() if task.get("time_sensitive", False)}
        elif time_filter == "insensitive":
            tasks = {tid: task for tid, task in tasks.items() if not task.get("time_sensitive", False)}
        
        if not tasks:
            print("No active tasks found after applying the time filter.")
            return
    
        # Determine discount rate to use.
        used_discount_rate = discount_rate if discount_rate is not None else self.discount_rate
    
        # Ensure each task has proper time_sensitive flag and compute discounted_priority.
        for tid, task in tasks.items():
            due = task.get("due_date")
            if due not in [None, "", "nan"]:
                task["time_sensitive"] = True
            else:
                task["time_sensitive"] = False
            task["discounted_priority"] = self.compute_effective_priority(task, discount_rate=used_discount_rate)
    
        if not suppress_discount_annotation:
            print(f"Discount rate used for computing effective priority: {used_discount_rate}")
    
        # Build the directed graph with reversed edge direction.
        G = nx.DiGraph()
        for tid in tasks:
            G.add_node(tid)
        for tid, task in tasks.items():
            parent = task.get("parent_task")
            if parent and parent in tasks:
                G.add_edge(tid, parent)
    
        # Lexicographical topological sort based on time sensitivity and discounted priority.
        order = list(nx.lexicographical_topological_sort(
            G,
            key=lambda tid: (not tasks[tid].get("time_sensitive", False), -tasks[tid].get("discounted_priority", 0))
        ))
    
        if reverse_order:
            order = order[::-1]
    
        ordered_tasks = [tasks[tid] for tid in order]
        df_final = pd.DataFrame(ordered_tasks)
    
        # Apply additional filter if provided.
        if filter_expr:
            try:
                df_final = df_final.query(filter_expr)
            except Exception as e:
                print(f"Invalid filter expression: {filter_expr}")
    
        display_cols = [
            'task_id', 'name', 'description', 'impact_score', 'due_date', 'time_sensitive', 'discounted_priority',
            'status', 'created_at', 'checked_out', 'parent_task', 
            'project_build', 'explorer', 'trial_id', 'ontology'
        ]
        df_final = df_final[display_cols]
    
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
        if display_output:
            display(HTML(scrollable_html))
        return df_final

    def search_tasks(self, query=None):
        """Interactive task search with filtering."""
        if query is None:
            query = input("Enter search filter (e.g., 'impact_score > 5' or 'status == \"active\"'): ")
        return self.task_table(query)
    
    def checkout_task(self, task_id=None, discount_rate=None, display_output=True):
        """Check out a task to work on."""
        if task_id is None:
            print("Available tasks:")
            # Display the table in reverse order for easier selection of high-priority tasks
            self.task_table(reverse_order=False, discount_rate=discount_rate, display_output=display_output)
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
            self.task_table()
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
    
    def get_task_graph(self, include_completed=False, unify_under_root=True):
        # Load active tasks
        active_tasks = self._load_tasks()
        # Always load completed tasks for reference—even if not showing them
        reference_completed = self._load_completed_tasks()
        
        # Build the nodes dictionary:
        if include_completed:
            nodes = {**active_tasks, **reference_completed}
        else:
            nodes = active_tasks.copy()
        
        G = nx.DiGraph()
        
        # Define default attributes for nodes.
        default_attributes = {
            "name": "Unknown",
            "impact_score": 0,
            "status": "undefined",
            "created_at": "N/A"
        }
        
        # If not unifying under a single root, add a fallback node for missing parents.
        if not unify_under_root:
            fallback_node = "NONEXTANT_TASKS"
            fallback_attrs = default_attributes.copy()
            fallback_attrs.update({"name": "Nonextant Tasks", "status": "completed", "color": "blue"})
            G.add_node(fallback_node, **fallback_attrs)
        
        # Add all nodes we want to show (from the 'nodes' dictionary).
        for task_id, task in nodes.items():
            node_data = {**default_attributes, **task}
            # Set color based on status.
            if node_data.get("status") in ["completed", "shelved"]:
                node_data["color"] = "blue"
            else:
                node_data["color"] = "orange"
            G.add_node(task_id, **node_data)
        
        # Helper: traverse the chain from a task to find the closest extant (active or shown) ancestor.
        def find_extant_ancestor(task, nodes, reference_completed):
            parent_id = task.get("parent_task")
            while parent_id is not None:
                if parent_id in nodes:
                    return parent_id
                elif parent_id in reference_completed:
                    parent_task = reference_completed[parent_id]
                    parent_id = parent_task.get("parent_task")
                else:
                    break
            return None
    
        # For each task, add an edge based on parent-child relationship.
        for task_id, task in nodes.items():
            parent_id = task.get("parent_task")
            if parent_id:
                if parent_id in nodes:
                    # Parent exists among nodes, add edge normally.
                    G.add_edge(parent_id, task_id)
                else:
                    # Parent is missing. Try to find a closest extant ancestor.
                    ancestor = find_extant_ancestor(task, nodes, reference_completed)
                    if ancestor is not None:
                        G.add_edge(ancestor, task_id)
                    else:
                        # No extant ancestor found: attach to the central root (if unifying)
                        # or to the fallback node if not unifying.
                        if unify_under_root:
                            G.add_edge("TARGET", task_id)
                        else:
                            G.add_edge("NONEXTANT_TASKS", task_id)
        
        # Optionally unify the graph under a single root node ("TARGET").
        if unify_under_root:
            root_node = "TARGET"
            root_attrs = default_attributes.copy()
            root_attrs.update({"name": "TARGET", "status": "root", "color": "gray"})
            G.add_node(root_node, **root_attrs)
            # Attach orphan nodes (nodes with no incoming edges) to TARGET.
            orphan_tasks = [node for node in G.nodes if G.in_degree(node) == 0 and node != root_node]
            for orphan in orphan_tasks:
                G.add_edge(root_node, orphan)
        
        return G

    def visualize_tasks(self, output_path=None, include_completed=False, time_filter="all"):
        """
        Create an interactive visualization of the task network.
        
        Parameters:
          output_path: (optional) file path to save the network visualization.
          include_completed: (optional) if True, include completed tasks.
          time_filter: (optional) 'all', 'sensitive', or 'insensitive' to filter tasks based on time sensitivity.
                      The central node ("TARGET") is always included.
        """
        G = self.get_task_graph(include_completed)
        
        # If a time_filter is provided (other than "all"), remove nodes that do not match,
        # but always keep the central node "TARGET".
        if time_filter in ("sensitive", "insensitive"):
            nodes_to_remove = [
                node for node, data in G.nodes(data=True)
                if node != "TARGET" and data.get("time_sensitive", False) != (time_filter == "sensitive")
            ]
            G.remove_nodes_from(nodes_to_remove)
        
        net = Network(height="750px", width="100%", directed=True)
        
        for node in G.nodes(data=True):
            node_id = node[0]
            node_data = node[1]
            formatted_label = format_node_label(node_id, node_data['name'])
            title = f"""
            Name: {node_data['name']}
            Priority: {node_data['impact_score']}
            Status: {node_data['status']}
            Created: {node_data['created_at']}
            """
            color = node_data.get("color", "orange")
            impact = float(node_data.get('impact_score', 0))
            base_size = 20
            scaling_factor = 5
            node_size = base_size + scaling_factor * np.sqrt(impact)
            
            if node_data.get("time_sensitive", False):
                effective_priority = self.compute_effective_priority(node_data)
                ratio = effective_priority / impact if impact > 0 else 0
                node_image = create_clock_svg(node_size, ratio, fill_color=color)
                shape = 'circularImage'
            else:
                node_image = None
                shape = 'dot'
            
            text_length = np.sqrt(len(node_data['name']))
            mass_scaling_factor = 1.5
            node_mass = text_length * mass_scaling_factor
        
            if node_image:
                net.add_node(node_id,
                             title=title,
                             label=formatted_label,
                             shape=shape,
                             image=node_image,
                             size=node_size,
                             mass=node_mass)
            else:
                net.add_node(node_id,
                             title=title,
                             label=formatted_label,
                             shape=shape,
                             color=color,
                             size=node_size,
                             mass=node_mass)
        
        for edge in G.edges():
            net.add_edge(edge[0], edge[1])
        
        # OPTIONAL: For each leaf task, add an extra edge to the central node ("TARGET")
        # with a length proportional to its effective priority.
        base_length = 5  # Base distance value; adjust as needed.
        length_scaling = 10  # Scaling factor for effective priority.
        for node in G.nodes():
            # Skip the central node.
            if node == "TARGET":
                continue
            # If the node has no outgoing edges, it is a leaf.
            node_data = G.nodes[node]
            # Compute effective priority; adjust this call if you wish to use a different measure
            effective_priority = self.compute_effective_priority(node_data)
            edge_length = base_length + length_scaling * effective_priority
            # Adding an extra edge from the leaf to "TARGET"
            net.add_edge(node, "TARGET", length=edge_length, title=f"Effective Priority: {effective_priority}", hidden=True)
        
        if output_path:
            net.save(output_path)
        return net
    
    def visualize_tasks_with_tags(self, output_path=None, include_completed=False, time_filter="all", 
                                tag_edge_length=150, unify_under_root=True, show_tags=False, tag_font_color="#007ACC"):
        """
        Create an interactive visualization of the task network augmented with tag nodes.
        
        First, the method uses the same logic as visualize_tasks to construct a graph (G) of task nodes.
        If unify_under_root is True, a central "TARGET" node is added and attached to top‐level tasks (or tasks
        whose parent cannot be found). Then, a mapping from each tag to the tasks that have that tag is built,
        and for each tag a tag node is added along with hidden tag edges connecting that tag node to its tasks.
        
        Finally, extra (hidden) edges are added from each leaf task (non‐tag, non‐TARGET node with no children)
        to the TARGET node with a length proportional to its effective priority.
        
        Parameters:
          output_path (str, optional): File path to save the resulting HTML visualization.
          include_completed (bool, optional): Whether to include completed tasks.
          time_filter (str, optional): 'all', 'sensitive', or 'insensitive' to filter tasks based on time sensitivity.
          tag_edge_length (int, optional): Desired length for edges from tag nodes to tasks.
          unify_under_root (bool, optional): If True, add a central "TARGET" node and attach top‐level task nodes.
          show_tags (bool, optional): If True, tag nodes are visible with a label and custom font color;
                                      if False, tag nodes are invisible.
          tag_font_color (str, optional): Hex code for the tag node font color when tags are visible.
        
        Returns:
          A PyVis Network object.
        """
        # (1) Get the task graph using our usual logic (which adds TARGET and extra task edges)
        G = self.get_task_graph(include_completed, unify_under_root=True)
        
        # (2) Filter out nodes based on time sensitivity if requested.
        if time_filter in ("sensitive", "insensitive"):
            nodes_to_remove = [
                node for node, data in G.nodes(data=True)
                if node != "TARGET" and data.get("time_sensitive", False) != (time_filter == "sensitive")
            ]
            G.remove_nodes_from(nodes_to_remove)
        
        # (3) Build mapping: for each tag (from the tasks remaining in G), list the task IDs that have that tag.
        # Note: We ignore any nodes that already are not tasks (e.g. TARGET) – here we assume all nodes in G (except TARGET)
        # are task nodes.
        tag_to_tasks = {}
        for node_id, data in G.nodes(data=True):
            # Only consider task nodes (not tag nodes). In our get_task_graph, we did not mark tag nodes.
            if node_id == "TARGET":
                continue
            # For each task, look for a "tags" list.
            for tag in data.get("tags", []):
                tag_to_tasks.setdefault(tag, []).append(node_id)
        
        # (4) Add tag nodes and hidden tag edges.
        for tag, task_ids in tag_to_tasks.items():
            tag_node_id = f"tag_{tag}"
            # Set appearance based on show_tags toggle.
            if show_tags:
                node_label = tag
                node_color = "#ffffff"  # Background color for tag node (you can adjust)
                font_opts = {"color": tag_font_color}
            else:
                node_label = ""
                node_color = "rgba(0,0,0,0)"
                font_opts = {"color": "rgba(0,0,0,0)"}
            # Add the tag node.
            G.add_node(tag_node_id, name=tag, is_tag=True, color=node_color, size=5, font=font_opts)
            # Add an edge from the tag node to each task that has the tag.
            for tid in task_ids:
                # Use the custom length and mark the edge as a tag edge.
                G.add_edge(tag_node_id, tid, tag_edge=True, length=tag_edge_length)
        
        # (5) Now create the PyVis network.
        net = Network(height="750px", width="100%", directed=True)
        
        # (6) Add nodes to the PyVis network.
        for node_id, data in G.nodes(data=True):
            if data.get("is_tag", False):
                # Tag node.
                net.add_node(node_id,
                             label=data.get("name") if show_tags else "",
                             shape="dot",
                             color=data.get("color", "rgba(0,0,0,0)"),
                             size=data.get("size", 5),
                             font=data.get("font", {}))
            else:
                # Task node.
                formatted_label = format_node_label(node_id, data.get("name", ""))
                title = f"Name: {data.get('name', '')}\nPriority: {data.get('impact_score', 0)}\nStatus: {data.get('status', '')}\nCreated: {data.get('created_at', '')}"
                color = data.get("color", "orange")
                impact = float(data.get("impact_score", 0))
                base_size = 20
                scaling_factor = 5
                node_size = base_size + scaling_factor * math.sqrt(impact)
                
                if data.get("time_sensitive", False):
                    effective_priority = self.compute_effective_priority(data)
                    ratio = effective_priority / impact if impact > 0 else 0
                    node_image = create_clock_svg(node_size, ratio, fill_color=color)
                    shape = "circularImage"
                else:
                    node_image = None
                    shape = "dot"
                
                node_mass = 1.5 * math.sqrt(len(data.get("name", "")))
                
                if node_image:
                    net.add_node(node_id,
                                 title=title,
                                 label=formatted_label,
                                 shape=shape,
                                 image=node_image,
                                 size=node_size,
                                 mass=node_mass)
                else:
                    net.add_node(node_id,
                                 title=title,
                                 label=formatted_label,
                                 shape=shape,
                                 color=color,
                                 size=node_size,
                                 mass=node_mass)
        
        # (7) Add non-tag edges.
        for source, target, edge_data in G.edges(data=True):
            if edge_data.get("tag_edge", False):
                # Tag edges: use the custom length and hide them.
                net.add_edge(source, target, length=edge_data.get("length", tag_edge_length),
                             title=f"Tag: {source.replace('tag_','')}", hidden=True)
            else:
                net.add_edge(source, target)
        
        # (8) Add extra (hidden) edges from leaf task nodes to TARGET.
        # We loop over all nodes in G that are tasks (i.e. not tag nodes and not TARGET)
        base_length = 5
        length_scaling = 10
        for node in G.nodes():
            if node == "TARGET":
                continue
            # Skip tag nodes (we set is_tag==True for those we added)
            if G.nodes[node].get("is_tag", False):
                continue
            # If the node has no outgoing edges (or if its out_degree is 0), consider it a leaf.
            if G.out_degree(node) == 0:
                effective_priority = self.compute_effective_priority(G.nodes[node])
                edge_length = base_length + length_scaling * effective_priority
                net.add_edge(node, "TARGET", length=edge_length, title=f"Effective Priority: {effective_priority}", hidden=True)
        
        # (9) Set global physics options.
        net.set_options("""
        var options = {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -2000,
              "centralGravity": 0.3,
              "springLength": 95,
              "springConstant": 0.04,
              "damping": 0.09
            },
            "minVelocity": 0.75
          }
        }
        """)
        
        if output_path:
            net.save_graph(output_path)
        return net

    def visualize_tasks_with_collapse_controls_DRAFT(self, output_path=None, include_completed=False, 
                                               time_filter="all", leaf_only=False):
        """
        Create an interactive visualization of the task network with per-node collapse controls.
        Each node will have two toggles:
          - Collapse Lock: When true, the node cannot be collapsed by a parent.
          - Collapse Children: When true, the node will collapse all its collapsible children recursively.
        A floating control panel appears when a node is clicked and stays visible until closed.
        """
        # Build the task graph.
        G = self.get_task_graph(include_completed)
        
        # Filter nodes based on time sensitivity (if applicable).
        if time_filter in ("sensitive", "insensitive"):
            nodes_to_remove = [
                node for node, data in G.nodes(data=True)
                if node != "TARGET" and data.get("time_sensitive", False) != (time_filter == "sensitive")
            ]
            G.remove_nodes_from(nodes_to_remove)
        
        # Optionally filter to leaf nodes.
        if leaf_only:
            leaf_nodes = [node for node in G.nodes() if G.out_degree(node) == 0 or node == "TARGET"]
            G = G.subgraph(leaf_nodes).copy()
        
        # Create the PyVis network.
        net = Network(height="750px", width="100%", directed=True)
        
        # Add nodes with the original visualization style and our collapse control state.
        for node in G.nodes(data=True):
            node_id = node[0]
            node_data = node[1]
            
            # Initialize collapse state variables if not already set.
            if "collapse_lock" not in node_data:
                node_data["collapse_lock"] = False
            if "collapse_children" not in node_data:
                node_data["collapse_children"] = False
            
            formatted_label = format_node_label(node_id, node_data['name'])
            # Build the title with original details plus the collapse states.
            title = f"""
    Name: {node_data['name']}
    Priority: {node_data['impact_score']}
    Status: {node_data['status']}
    Created: {node_data['created_at']}
    Collapse Lock: {node_data['collapse_lock']}
    Collapse Children: {node_data['collapse_children']}
    """
            color = node_data.get("color", "orange")
            impact = float(node_data.get('impact_score', 0))
            base_size = 20
            scaling_factor = 5
            node_size = base_size + scaling_factor * np.sqrt(impact)
            
            # For time-sensitive tasks, compute effective priority and use a clock SVG.
            if node_data.get("time_sensitive", False):
                effective_priority = self.compute_effective_priority(node_data)
                ratio = effective_priority / impact if impact > 0 else 0
                node_image = create_clock_svg(node_size, ratio, fill_color=color)
                shape = 'circularImage'
            else:
                node_image = None
                shape = 'dot'
            
            text_length = np.sqrt(len(node_data['name']))
            mass_scaling_factor = 1.5
            node_mass = text_length * mass_scaling_factor
            
            if node_image:
                net.add_node(node_id,
                             title=title,
                             label=formatted_label,
                             shape=shape,
                             image=node_image,
                             size=node_size,
                             mass=node_mass)
            else:
                net.add_node(node_id,
                             title=title,
                             label=formatted_label,
                             shape=shape,
                             color=color,
                             size=node_size,
                             mass=node_mass)
        
        # Add edges.
        for edge in G.edges():
            net.add_edge(edge[0], edge[1])
        
        # Append custom JavaScript for the collapse controls with improved styling and behavior.
        custom_js = """
<script type="text/javascript">
  function initControlPanel() {
      // Add a style block to the head for our control panel
      const styleElement = document.createElement('style');
      styleElement.textContent = `
        #collapseControlPanel {
          position: fixed;
          top: 20px;
          right: 20px;
          background-color: #fff;
          border: 1px solid #ccc;
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
          padding: 15px;
          z-index: 10000;
          display: none;
          width: 250px;
          font-family: Arial, sans-serif;
        }
        #collapseControlPanel h4 {
          margin-top: 0;
          margin-bottom: 15px;
          color: #333;
          font-size: 14px;
          font-weight: bold;
          border-bottom: 1px solid #eee;
          padding-bottom: 10px;
        }
        .control-panel-button {
          display: inline-block;
          margin: 5px;
          padding: 8px 12px;
          background-color: #f0f0f0;
          border: 1px solid #ddd;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
          width: calc(100% - 10px);
          text-align: center;
        }
        .control-panel-button:hover {
          background-color: #e0e0e0;
        }
        .control-panel-button.active {
          background-color: #4c8bf5;
          color: white;
          border-color: #3670d6;
        }
        .close-button {
          background-color: #f44336;
          color: white;
          border-color: #d32f2f;
        }
        .close-button:hover {
          background-color: #d32f2f;
        }
      `;
      document.head.appendChild(styleElement);
      
      // Create a persistent floating control panel if it doesn't exist.
      if (!document.getElementById('collapseControlPanel')) {
          const panel = document.createElement('div');
          panel.id = 'collapseControlPanel';
          document.body.appendChild(panel);
      }
      
      // Store the currently selected node ID (if needed later)
      let currentNodeId = null;
      
      // Function to update the panel content for a given node.
      function updatePanel(nodeId, nodeData) {
          const panel = document.getElementById('collapseControlPanel');
          panel.innerHTML = '';  // Clear previous content.
          currentNodeId = nodeId;
          
          // Create header.
          const header = document.createElement('h4');
          header.textContent = 'Controls for ' + nodeId;
          panel.appendChild(header);
          
          // Create the Collapse Lock toggle button.
          const lockBtn = document.createElement('div');
          lockBtn.className = 'control-panel-button' + (nodeData.collapse_lock ? ' active' : '');
          lockBtn.textContent = nodeData.collapse_lock ? 'Unlock Collapse' : 'Lock Collapse';
          lockBtn.onclick = function(e) {
              e.stopPropagation();
              nodeData.collapse_lock = !nodeData.collapse_lock;
              this.classList.toggle('active');
              this.textContent = nodeData.collapse_lock ? 'Unlock Collapse' : 'Lock Collapse';
              // Update node title tooltip.
              window.network.body.data.nodes.update({
                  id: nodeId,
                  title: 'Name: ' + nodeData.name + '\\nPriority: ' + nodeData.impact_score +
                         '\\nStatus: ' + nodeData.status + '\\nCreated: ' + nodeData.created_at +
                         '\\nCollapse Lock: ' + nodeData.collapse_lock +
                         '\\nCollapse Children: ' + nodeData.collapse_children
              });
          };
          panel.appendChild(lockBtn);
          
          // Create the Collapse Children toggle button.
          const collapseBtn = document.createElement('div');
          collapseBtn.className = 'control-panel-button' + (nodeData.collapse_children ? ' active' : '');
          collapseBtn.textContent = nodeData.collapse_children ? 'Expand Children' : 'Collapse Children';
          collapseBtn.onclick = function(e) {
              e.stopPropagation();
              nodeData.collapse_children = !nodeData.collapse_children;
              this.classList.toggle('active');
              this.textContent = nodeData.collapse_children ? 'Expand Children' : 'Collapse Children';
              // Update node title tooltip.
              window.network.body.data.nodes.update({
                  id: nodeId,
                  title: 'Name: ' + nodeData.name + '\\nPriority: ' + nodeData.impact_score +
                         '\\nStatus: ' + nodeData.status + '\\nCreated: ' + nodeData.created_at +
                         '\\nCollapse Lock: ' + nodeData.collapse_lock +
                         '\\nCollapse Children: ' + nodeData.collapse_children
              });
              // Here you would call your recursive collapse/expand logic.
              collapseOrExpandChildren(nodeId, nodeData.collapse_children);
          };
          panel.appendChild(collapseBtn);
          
          // Add a Close button to hide the panel.
          const closeBtn = document.createElement('div');
          closeBtn.className = 'control-panel-button close-button';
          closeBtn.textContent = 'Close Panel';
          closeBtn.onclick = function(e) {
              e.stopPropagation();
              panel.style.display = 'none';
              currentNodeId = null;
          };
          panel.appendChild(closeBtn);
      }
      
      // Function to show the control panel for a given node.
      function showCollapsePanel(nodeId, nodeData) {
          const panel = document.getElementById('collapseControlPanel');
          panel.style.display = 'block';
          updatePanel(nodeId, nodeData);
      }
      
      // Placeholder for collapse/expand children functionality.
      function collapseOrExpandChildren(nodeId, shouldCollapse) {
          console.log('Collapse children of ' + nodeId + ': ' + shouldCollapse);
          // Implement actual collapse/expand logic here.
      }
      
      // Attach a click listener to the network.
      if (window.network) {
          window.network.on("click", function(params) {
              // Only show the panel if a node is actually clicked.
              if (params.nodes.length > 0) {
                  const nodeId = params.nodes[0];
                  const nodeData = window.network.body.data.nodes.get(nodeId);
                  // Ensure our custom properties exist.
                  if (typeof nodeData.collapse_lock === 'undefined') {
                      nodeData.collapse_lock = false;
                  }
                  if (typeof nodeData.collapse_children === 'undefined') {
                      nodeData.collapse_children = false;
                  }
                  showCollapsePanel(nodeId, nodeData);
              }
          });
      }
  }
  
  // Run our init function depending on document readiness.
  if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initControlPanel);
  } else {
      initControlPanel();
  }
</script>
"""
        net.html += custom_js
        
        if output_path:
            net.save_graph(output_path)
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

