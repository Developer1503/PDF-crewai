from crewai import Task

def get_writing_task(agent, context):
    return Task(
        description="Write a professional blog post or report based on the analysis. Ensure the tone is engaging and informative. Structure it with clear headings.",
        expected_output="A polished blog post/report in Markdown format.",
        agent=agent,
        context=context
    )
