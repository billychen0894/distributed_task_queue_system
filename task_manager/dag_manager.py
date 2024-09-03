from collections import deque


class DAGManager:
    @staticmethod
    def get_execution_order(tasks):
        # Create a dictionary mapping task IDs to tasks
        task_dict = {str(task.id): task for task in tasks}
        # Graph is a dictionary where the key is the task ID and the value is a list of all the tasks that depend on it
        # Graph represents the task dependency graph
        graph = {
            str(task.id): [
                str(dependency.id) for dependency in task.get_all_dependencies()
            ]
            for task in tasks
        }
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
            # Get the task with no dependencies (FIFO)
            task_id = queue.popleft()
            # Add the task to the execution order
            execution_order.append(task_dict[task_id])

            # Reduce the in-degree of tasks that depend on the current task
            for dependent_id in [
                str(dependency.id)
                for dependency in task_dict[task_id].dependent_tasks.all()
            ]:
                if dependent_id in in_degree:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)

        # If there is a cycle, the length of execution_order will be less than the length of tasks
        if len(execution_order) != len(tasks):
            raise ValueError("There exists a cycle in the graph")
        return execution_order
