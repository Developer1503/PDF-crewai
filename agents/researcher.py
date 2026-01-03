from crewai import Agent

def get_researcher_agent(llm, tools):
    return Agent(
        role='Senior PDF Researcher',
        goal='Uncover actionable insights and key information from the provided PDF document',
        backstory=(
            "You are a seasoned researcher with a keen eye for detail. "
            "Your expertise lies in dissecting complex documents and extracting "
            "the most relevant information to answer specific queries or generate summaries."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False
    )
