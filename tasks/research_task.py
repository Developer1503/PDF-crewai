from crewai import Task

def get_research_task(agent, pdf_path):
    return Task(
        description=f"Thoroughly analyze the PDF file provided. Extract key findings, summaries, and any relevant data points. The file is located at: {pdf_path}",
        expected_output="A detailed summary document containing key findings and extracted data from the PDF.",
        agent=agent
    )
