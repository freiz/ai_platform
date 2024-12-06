from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field

from src.activities import Activity


class Connection(BaseModel):
    """
    Represents a connection between two activities in a workflow.
    
    Attributes:
        source_activity_name (str): Name of the source activity
        source_output (str): Output parameter name of the source activity
        target_activity_name (str): Name of the target activity
        target_input (str): Input parameter name of the target activity
    """
    source_activity_name: str
    source_output: str
    target_activity_name: str
    target_input: str


class Workflow(BaseModel):
    """
    Represents a workflow composed of interconnected activities.
    
    Attributes:
        activities (Dict[str, Activity]): Dictionary of activities in the workflow, keyed by name
        connections (List[Connection]): Connections between activities
    """
    activities: Dict[str, Activity] = Field(default_factory=dict)
    connections: List[Connection] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Activity: lambda v: v.model_dump()
        }

    def add_activity(self, name: str, activity: Activity) -> None:
        """
        Add an activity to the workflow.
        
        Args:
            name (str): Name of the activity in the workflow
            activity (Activity): Activity to add
        """
        self.activities[name] = activity

    def connect_activities(self,
                           source_activity_name: str,
                           source_output: str,
                           target_activity_name: str,
                           target_input: str):
        """
        Connect two activities by mapping an output to an input.
        
        Args:
            source_activity_name (str): Name of the source activity
            source_output (str): Output parameter name of the source activity
            target_activity_name (str): Name of the target activity
            target_input (str): Input parameter name of the target activity
        
        Raises:
            ValueError: If activities or parameters are not found
        """
        # Find source and target activities
        if source_activity_name not in self.activities or target_activity_name not in self.activities:
            raise ValueError("Activity not found")

        source_activity = self.activities[source_activity_name]
        target_activity = self.activities[target_activity_name]

        # Validate output and input parameters
        if source_output not in source_activity.output_params:
            raise ValueError(f"Output parameter {source_output} not found in source activity")

        if target_input not in target_activity.input_params:
            raise ValueError(f"Input parameter {target_input} not found in target activity")

        # Check type compatibility
        source_param = source_activity.output_params[source_output]
        target_param = target_activity.input_params[target_input]

        if source_param.type != target_param.type:
            raise ValueError(f"Type mismatch: {source_output} ({source_param.type}) "
                             f"cannot be connected to {target_input} ({target_param.type})")

        # Add connection
        connection = Connection(
            source_activity_name=source_activity_name,
            source_output=source_output,
            target_activity_name=target_activity_name,
            target_input=target_input
        )
        self.connections.append(connection)

    def run(self, initial_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the workflow with optional initial inputs.
        
        Args:
            initial_inputs (Optional[Dict[str, Any]]): Initial inputs for the first activity
        
        Returns:
            Dict[str, Any]: Final outputs of the workflow
        """
        # Topological sort of activities based on connections
        sorted_activities = self._topological_sort()

        # Track outputs of each activity
        activity_outputs: Dict[str, Dict[str, Any]] = {}

        # Run activities in order
        for activity in sorted_activities:
            # Prepare inputs for this activity
            activity_inputs = {}

            # If it's the first activity and initial inputs are provided
            if activity == sorted_activities[0] and initial_inputs:
                activity_inputs.update(initial_inputs)

            # Check connections to fill inputs
            for connection in self.connections:
                if connection.target_activity_name == activity:
                    source_activity_name = connection.source_activity_name
                    source_output = connection.source_output
                    target_input = connection.target_input

                    # Use output from previous activity as input
                    activity_inputs[target_input] = activity_outputs[source_activity_name][source_output]

            # Run the activity
            outputs = self.activities[activity](**activity_inputs)
            activity_outputs[activity] = outputs

        # Return outputs of the last activity
        return activity_outputs[sorted_activities[-1]]

    def _topological_sort(self) -> List[str]:
        """
        Perform a topological sort of activities based on connections.
        
        Returns:
            List[str]: Sorted list of activity names
        
        Raises:
            ValueError: If a cyclic dependency is detected
        """
        # Create adjacency list and in-degree map
        graph = {activity: [] for activity in self.activities}
        in_degree = {activity: 0 for activity in self.activities}

        # Build graph based on connections
        for connection in self.connections:
            graph[connection.source_activity_name].append(connection.target_activity_name)
            in_degree[connection.target_activity_name] += 1

        # Perform topological sort
        queue = [activity for activity in self.activities if in_degree[activity] == 0]
        sorted_activities = []

        while queue:
            current_activity = queue.pop(0)
            sorted_activities.append(current_activity)

            # Find connected activities
            for connection in self.connections:
                if connection.source_activity_name == current_activity:
                    target_activity = connection.target_activity_name
                    in_degree[target_activity] -= 1

                    if in_degree[target_activity] == 0:
                        queue.append(target_activity)

        # Check for cyclic dependencies
        if len(sorted_activities) != len(self.activities):
            raise ValueError("Cyclic dependencies detected in workflow")

        return sorted_activities
