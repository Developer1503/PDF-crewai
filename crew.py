from crewai import Crew, Process
from agents.researcher import get_researcher_agent
from agents.analyst import get_analyst_agent
from agents.writer import get_writer_agent
from agents.reviewer import get_reviewer_agent
from tasks.research_task import get_research_task
from tasks.analysis_task import get_analysis_task
from tasks.writing_task import get_writing_task
from tasks.review_task import get_review_task

def create_crew(llm, tools, pdf_path):
    # Agents
    researcher = get_researcher_agent(llm, tools)
    analyst = get_analyst_agent(llm)
    writer = get_writer_agent(llm)
    reviewer = get_reviewer_agent(llm)

    # Tasks
    research = get_research_task(researcher, pdf_path)
    analysis = get_analysis_task(analyst, [research])
    writing = get_writing_task(writer, [analysis])
    review = get_review_task(reviewer, [writing])
    
    crew = Crew(
        agents=[researcher, analyst, writer, reviewer],
        tasks=[research, analysis, writing, review],
        process=Process.sequential,
        verbose=True,
        function_calling_llm=llm,  # Ensure CrewAI uses our LLM for internal operations
    )
    return crew
