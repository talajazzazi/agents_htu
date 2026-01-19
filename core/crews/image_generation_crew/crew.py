from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from core.tools import basic_llm
from core.tools.recraft.recraft_v3 import generat_image

def _get_image_generation_tool():
    return generat_image


@CrewBase
class ImageGeneratorCrew():

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def image_prompt_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['image_prompt_creator'],
            verbose=True,
            llm=basic_llm,
        )
    

    
    @agent
    def image_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['image_generator'],
            verbose=True,
            llm=basic_llm,
            tools=[_get_image_generation_tool()]
        )


    @task
    def image_prompt_creator_task(self) -> Task:
        return Task(
            config=self.tasks_config['image_prompt_creator_task'],
        )
    
    @task
    def image_generator_task(self) -> Task:
        return Task(
            config=self.tasks_config['image_generator_task'],
        )

    @crew
    def crew(self) -> Crew:

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )