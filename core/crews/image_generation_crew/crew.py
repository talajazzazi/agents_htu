from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from core.tools import basic_llm, dalle3_image_generator

@CrewBase
class ImageGeneratorCrew():

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def image_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['image_generator'],
            verbose=True,
            llm=basic_llm,
            tools=[dalle3_image_generator],
        )

    @task
    def image_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['image_generation_task'],
            agent=self.image_generator(),
        )

    @crew
    def crew(self) -> Crew:

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )