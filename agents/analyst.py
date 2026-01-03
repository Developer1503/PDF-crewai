from crewai import Agent

def get_analyst_agent(llm):
    return Agent(
        role='Data Analyst',
        goal='Analyze the extracted data and identify trends, patterns, and key takeaways',
        backstory=(
            "With a background in data science and business intelligence, "
            "you excel at transforming raw information into meaningful insights. "
            "You connect the dots that others miss."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
