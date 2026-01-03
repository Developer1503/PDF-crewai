import os
import sys
from dotenv import load_dotenv
from crewai_tools import PDFSearchTool
from config.llm import get_llm
from crew import create_crew

# Load environment variables
load_dotenv()

def main():
    # Helper to check if API keys are set
    if not os.getenv("GROQ_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("Error: API keys not found. Please set GROQ_API_KEY or GOOGLE_API_KEY in your .env file.")
        return

    print("Welcome to the PDF Research Crew!")
    pdf_path = input("Please enter the path to the PDF file you want to analyze: ").strip()
    
    # Remove quotes if user added them
    if (pdf_path.startswith('"') and pdf_path.endswith('"')) or (pdf_path.startswith("'") and pdf_path.endswith("'")):
        pdf_path = pdf_path[1:-1]
        
    if not os.path.exists(pdf_path):
        print(f"Error: The file '{pdf_path}' does not exist.")
        return
        
    print(f"Initializing crew with {pdf_path}...")
    
    # Initialize Tool
    try:
        # Configure tool to use Google Gemini if available, since we are not using OpenAI
        # This requires GOOGLE_API_KEY to be set
        if os.getenv("GOOGLE_API_KEY"):
            # Workaround: PDFSearchTool might enforce OPENAI_API_KEY existence check even if using custom config.
            if "OPENAI_API_KEY" not in os.environ:
                os.environ["OPENAI_API_KEY"] = "NA"

            pdf_tool = PDFSearchTool(
                pdf=pdf_path,
                config=dict(
                    llm=dict(
                        provider="google",
                        config=dict(
                            model="gemini-1.5-flash",
                        ),
                    ),
                    embedder=dict(
                        provider="google",
                        config=dict(
                            model="models/embedding-001",
                            task_type="retrieval_document",
                        ),
                    ),
                )
            )
        else:
            # Fallback or let it error if no embedding provider is found (e.g. if only Groq is keys)
            # If the user only has Groq, they might need local embeddings (HuggingFace),
            # but that requires extra dependencies like sentence-transformers.
            print("Warning: GOOGLE_API_KEY not found. Attempting to initialize PDFSearchTool without explicit config (may default to OpenAI and fail).")
            pdf_tool = PDFSearchTool(pdf=pdf_path)
            
    except Exception as e:
        print(f"Failed to initialize PDF tool: {e}")
        return

    # Initialize LLM
    provider = "groq" if os.getenv("GROQ_API_KEY") else "gemini"
    
    # Allow user to override via args or just use available
    # Simple logic: check Groq first (as per config preference), then Gemini
    try:
        llm = get_llm(provider=provider)
        print(f"Using LLM provider: {provider}")
    except Exception as e:
        print(f"Failed to initialize LLM: {e}")
        return

    # Create Crew
    crew = create_crew(llm, [pdf_tool], pdf_path)
    
    # Run
    try:
        result = crew.kickoff()
        print("\n\n########################")
        print("## Here is your result ##")
        print("########################\n")
        print(result)
        
        # Save result
        with open("result.md", "w", encoding="utf-8") as f:
            f.write(str(result))
        print("\nResult saved to result.md")
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()
