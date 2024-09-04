from collections import deque


class CyclicDependencyException(Exception):
    def __init__(self, cycle):
        self.cycle = cycle
        cycle_str = " -> ".join(task_id for task_id in cycle)
        super().__init__(f"Cyclic dependency detected: {cycle_str}")


class DAGManager:
    @staticmethod
    def get_execution_order(tasks):
        # Create a dictionary mapping task IDs to tasks
        task_dict = {str(task.id): task for task in tasks}
        # Graph represents dependencies: key is the task ID, value is a list of task IDs it depends on
        graph = {
            str(task.id): [
                str(dependency.id) for dependency in task.get_all_dependencies()
            ]
            for task in tasks
        }

        # Reverse graph represents dependents: key is the task ID, value is a list of task IDs that depend on it
        reverse_graph = {task_id: [] for task_id in graph}
        for task_id in graph:
            for dependent_id in graph[task_id]:
                reverse_graph[dependent_id].append(task_id)

        # Find a cycle in the graph
        def find_cycle(node, path):
            if node in path:
                return path[path.index(node) :]
            path.append(node)
            for neighbor in graph.get(node, []):
                cycle = find_cycle(neighbor, path.copy())
                if cycle:
                    return cycle
            return None

        for task_id in graph:
            cycle = find_cycle(task_id, [])
            if cycle:
                raise CyclicDependencyException(cycle)

        # degree is a dictionary where the key is the task and the value is the number of dependencies it has
        # It represents the number of tasks that need to be completed before this task can be executed
        in_degree = {
            task_id: len(dependencies) for task_id, dependencies in graph.items()
        }

        # Initialize a queue with tasks that have no dependencies
        # Tasks with no dependencies are the ones that can be executed first
        queue = deque([task_id for task_id in graph if in_degree[task_id] == 0])
        execution_order = []

        # Perform a topological sort on the graph
        while queue:
            # Get the task with no dependencies
            task_id = queue.popleft()
            # Add the task to the execution order
            execution_order.append(task_dict[task_id])

            # Reduce the in-degree of tasks that depend on the current task
            for dependent_id in reverse_graph[task_id]:
                if dependent_id in in_degree:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)

        # If there is a cycle, the length of execution_order will be less than the length of tasks
        if len(execution_order) != len(tasks):
            raise CyclicDependencyException([])
        return execution_order
