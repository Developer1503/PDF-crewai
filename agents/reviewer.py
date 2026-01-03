from crewai import Agent

def get_reviewer_agent(llm):
    return Agent(
        role='Senior Editor',
        goal='Review the content for accuracy, clarity, and tone. Ensure it meets high standards.',
        backstory=(
            "You are a meticulous editor who ensures that every piece of content "
            "meets the highest standards of quality. You check for logical flow, "
            "grammar, and alignment with the original goals."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
