from collections import deque


class DAGManager:
    @staticmethod
    def get_execution_order(tasks):
        # Graph is a dictionary where the key is the task and the value is a list of all the tasks that depend on it
        # Graph represents the task dependency graph
        graph = {task: task.get_all_dependencies() for task in tasks}
        # In-degree is a dictionary where the key is the task and the value is the number of dependencies it has
        # It represents the number of tasks that need to be completed before this task can be executed
        in_degree = {task: len(dependencies) for task, dependencies in graph.items()}

        # Initialize a queue with tasks that have no dependencies
        # Tasks with no dependencies are the ones that can be executed first
        queue = deque([task for task in tasks if in_degree[task] == 0])
        execution_order = []

        # Perform a topological sort on the graph
        while queue:
            # Get the task with no dependencies (FIFO)
            task = queue.popleft()
            # Add the task to the execution order
            execution_order.append(task)

            # Reduce the in-degree of tasks that depend on the current task
            for dependent in task.dependent_tasks.all():
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        # If there is a cycle, the length of execution_order will be less than the length of tasks
        if len(execution_order) != len(tasks):
            raise ValueError("There exists a cycle in the graph")
        return execution_order
