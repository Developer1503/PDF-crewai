from crewai import Task

def get_review_task(agent, context):
    return Task(
        description="Review the written blog post/report. Check for grammatical errors, flow, and ensure the content aligns with the analysis.",
        expected_output="A final, polished version of the blog post/report, ready for publication.",
        agent=agent,
        context=context
    )
