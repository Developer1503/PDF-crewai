from crewai import Task

def get_analysis_task(agent, context):
    return Task(
        description="Analyze the findings from the research task. Identify major themes, implications, and potential areas for further investigation.",
        expected_output="A comprehensive analysis report highlighting trends and insights derived from the research.",
        agent=agent,
        context=context
    )
