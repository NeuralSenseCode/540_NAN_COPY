"""
This library is used to define Client and Project classes for managing projects.
"""

import os
import pickle
from typing import List, Optional

class Client:
    """
    Represents a client who owns one or more projects.
    """

    def __init__(self, name: str):
        """
        Initializes a new Client.

        :param name: The name of the client.
        """
        self.name = name
        self.projects: List[Project] = []

    def add_project(self, project: 'Project') -> None:
        """
        Adds a new project to the client.

        :param project: The Project instance to add.
        """
        self.projects.append(project)

    def get_project(self, project_name: str) -> Optional['Project']:
        """
        Retrieves a project by name.

        :param project_name: The name of the project.
        :return: The Project instance if found, otherwise None.
        """
        for project in self.projects:
            if project.name == project_name:
                return project
        return None

    def list_projects(self) -> List[str]:
        """
        Lists the names of all projects associated with the client.

        :return: A list of project names.
        """
        return [project.name for project in self.projects]

    def save_state(self, filepath: str) -> None:
        """
        Saves the state of the client and its projects to a file.

        :param filepath: The path to the file where the state should be saved.
        """
        with open(filepath, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load_state(filepath: str) -> 'Client':
        """
        Loads a client and its projects from a saved state file.

        :param filepath: The path to the file where the state is saved.
        :return: The loaded Client instance.
        """
        if os.path.exists(filepath):
            with open(filepath, 'rb') as file:
                return pickle.load(file)
        else:
            raise FileNotFoundError(f"No state file found at {filepath}")


class Project:
    """
    Represents a project belonging to a client.
    """

    def __init__(self, name: str, client: Client, input_folder: str, output_folder: str):
        """
        Initializes a new Project.

        :param name: The name of the project.
        :param client: The Client instance the project belongs to.
        :param input_folder: The path to the input folder.
        :param output_folder: The path to the output folder.
        """
        self.name = name
        self.client = client
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.tools = []

    def add_tool(self, tool) -> None:
        """
        Adds a tool to the project.

        :param tool: The tool to be added.
        """
        self.tools.append(tool)

    def run_tool_workflow(self) -> None:
        """
        Runs the workflow for all tools in the project.
        """
        for tool in self.tools:
            tool.setup_project()
            tool.process_data()
            tool.analyze_data()

    def save_state(self, filepath: str) -> None:
        """
        Saves the state of the project to a file.

        :param filepath: The path to the file where the state should be saved.
        """
        with open(filepath, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load_state(filepath: str) -> 'Project':
        """
        Loads a project from a saved state file.

        :param filepath: The path to the file where the state is saved.
        :return: The loaded Project instance.
        """
        if os.path.exists(filepath):
            with open(filepath, 'rb') as file:
                return pickle.load(file)
        else:
            raise FileNotFoundError(f"No state file found at {filepath}")

# Example usage in a main function
def main():
    # Example of how you might use this framework in a script
    client = Client("Client XYZ")
    project = Project("Project Alpha", client, "/path/to/input", "/path/to/output")
    client.add_project(project)

    # Save the client's state
    client.save_state("client_state.pkl")

    # Later, load the client's state
    loaded_client = Client.load_state("client_state.pkl")

    print(f"Loaded Client: {loaded_client.name}")
    print("Projects:", loaded_client.list_projects())

if __name__ == "__main__":
    main()
