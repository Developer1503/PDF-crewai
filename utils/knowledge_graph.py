import json
import os
import networkx as nx
from pyvis.network import Network
import litellm
import tempfile

class KnowledgeGraphGenerator:
    def __init__(self, provider="groq", use_turbo=True):
        self.provider = provider
        self.use_turbo = use_turbo

    def extract_entities_and_relations(self, text, max_relations=20):
        """Use LLM to extract entities and their relationships from text."""
        # Truncate text to avoid context limits if too long
        text_chunk = text[:15000]

        system_prompt = f"""You are an expert data extractor.
Analyze the following text and extract key concepts, entities, and their relationships.
Return the output strictly as a JSON list of objects with 'source', 'target', and 'relation' keys.
Example: [{{"source": "AI", "target": "Machine Learning", "relation": "is a subset of"}}]
Extract a maximum of {max_relations} important relationships. Do NOT output any markdown, only raw JSON.
"""
        def attempt_extraction(chunk):
            try:
                if self.provider == "gemini":
                    model = "gemini/gemini-1.5-flash"
                    api_key = os.getenv("GOOGLE_API_KEY")
                else:
                    model = "groq/llama-3.1-8b-instant" if self.use_turbo else "groq/llama-3.3-70b-versatile"
                    api_key = os.getenv("GROQ_API_KEY")

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk},
                ]

                response = litellm.completion(
                    model=model,
                    messages=messages,
                    api_key=api_key,
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"} if self.provider == "groq" else None
                )

                content = response.choices[0].message.content
                
                # Clean up potential markdown formatting if any
                if content.startswith("```json"):
                    content = content.strip()[7:-3]
                elif content.startswith("```"):
                    content = content.strip()[3:-3]
                
                data = json.loads(content)
                
                # Handle if the LLM wrapped it in an object like {"relations": [...]}
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list):
                            return v
                    return []
                return data if isinstance(data, list) else []
                
            except litellm.RateLimitError as e:
                print(f"Rate limit error: {e}")
                raise e
            except Exception as e:
                print(f"Error extracting relations: {e}")
                return []

        try:
            return attempt_extraction(text[:10000])
        except litellm.RateLimitError:
            print("Retrying with a smaller chunk due to rate limit...")
            try:
                return attempt_extraction(text[:3000])
            except Exception as e:
                print(f"Final error extracting relations: {e}")
                return []


    def generate_html(self, text):
        """Generate interactive HTML for the knowledge graph."""
        relations = self.extract_entities_and_relations(text)
        
        if not relations:
            return "<div><p>Could not extract enough relationships from the text to generate a graph.</p></div>"
            
        G = nx.Graph()
        
        for rel in relations:
            source = rel.get("source")
            target = rel.get("target")
            relation_desc = rel.get("relation", "")
            
            if source and target:
                G.add_edge(source, target, title=relation_desc, label=relation_desc)
                
        # Use pyvis to render
        net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#333333", directed=True)
        # Avoid physics issues
        net.toggle_physics(True)
        net.from_nx(G)
        
        # Set node styles
        for node in net.nodes:
            node["color"] = "#8B5CF6"
            node["shape"] = "dot"
            node["size"] = 20
            node["font"] = {"size": 14, "color": "#1F2937", "face": "Arial"}

        # Set edge styles
        for edge in net.edges:
            edge["color"] = "#CBD5E1"
            edge["font"] = {"size": 10, "color": "#6B7280", "align": "middle"}

        # Generate HTML string
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.save_graph(tmp.name)
            with open(tmp.name, 'r', encoding='utf-8') as f:
                html_content = f.read()
        
        # Clean up tmp
        os.unlink(tmp.name)
        
        return html_content
