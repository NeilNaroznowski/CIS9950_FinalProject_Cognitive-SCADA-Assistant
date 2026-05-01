import os
import os
from langchain_community.graphs import Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# This is the updated path that bypasses the missing module error
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain

# --- 1. Credentials ---
# Replace with your actual OpenAI API Key
os.environ["GOOGLE_API_KEY"] = ""

NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USERNAME = ""
NEO4J_PASSWORD = "" # 

# --- 2. Connect LangChain to Neo4j ---
print("Connecting to Neo4j...")
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)
# This forces LangChain to scan your database and learn what labels and edges exist
graph.refresh_schema() 

# --- 3. Initialize the LLM ---
# Temperature is 0 so the AI is highly deterministic and doesn't hallucinate
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# --- 4. The "Prompt Engineering" to limit scope ---
# Because we scoped the project to RTU-1 for this sprint, we tell the LLM that in the prompt.
CYPHER_GENERATION_TEMPLATE = """Task: Generate a Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

IMPORTANT CONTEXT:
You are a Cognitive Facility Assistant reasoning over the 'Bravo' hospital dataset.
For this prototype, strictly limit your queries to RTU-1 (which has the property id: 'b-00ac') and its downstream network.
- VAVs point to the AHU that supplies them via the AIRREF relationship: (vav)-[:AIRREF]->(ahu)
- Points point to the Equipment they belong to via the EQUIPREF relationship: (point)-[:EQUIPREF]->(equip)

Schema:
{schema}

The question is:
{question}
"""

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

# --- 5. Build the Chain ---
print("Building the Graph-RAG Chain...")
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True, 
    cypher_prompt=cypher_prompt,
    allow_dangerous_requests=True,
    top_k=50  # <--- Add this line to allow up to 50 results!
)

# --- 6. Test the Pipeline ---
if __name__ == "__main__":
    print("\n--- Testing Cognitive Assistant ---")
    question = "Which VAVs receive air from RTU-1?"
    print(f"User Question: {question}\n")
    
    # Run the orchestration!
    response = chain.invoke({"query": question})
    
    print("\n--- Final Answer ---")
    print(response["result"])
