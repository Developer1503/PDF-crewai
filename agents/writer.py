from crewai import Agent

def get_writer_agent(llm):
    return Agent(
        role='Technical Writer',
        goal='Craft a compelling and well-structured report based on the analysis',
        backstory=(
            "You are a gifted storyteller with a knack for technical writing. "
            "You can take complex insights and present them in a clear, "
            "engaging, and professional manner."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
