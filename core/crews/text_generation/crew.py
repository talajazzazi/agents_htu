from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from core.tools import basic_llm


@CrewBase
class TextGenerationCrew():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def text_generation(self) -> Agent:
        return Agent(
            config=self.agents_config['text_generation'],
            verbose=True,
            llm=basic_llm
        )

    @task
    def text_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['text_generation_task'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
