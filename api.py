import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# LangChain Imports
from langchain_community.graphs import Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain 

# --- 1. Setup API Keys & Database ---
# Ensure your actual Gemini API key is pasted here
os.environ["GOOGLE_API_KEY"] = "API_Key" 

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password" 

print("Connecting to Neo4j...")
graph = Neo4jGraph(
    url=NEO4J_URI, 
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD
)

# --- 2. Initialize the AI Chain ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Prompt 1: Teaching the AI how to write Cypher for the Bravo dataset
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

# Prompt 2: Forcing the AI to use the returned database results to answer
QA_TEMPLATE = """You are a Cognitive Facility Assistant. 
Use the provided database results to answer the user's question. 
Assume the database results are the direct and correct output for the user's query. Format the raw data into a clean, human-readable sentence.

Database Results: 
{context}

User Question: 
{question}

Helpful Answer:"""
qa_prompt = PromptTemplate(
    input_variables=["context", "question"], 
    template=QA_TEMPLATE
)

print("Building AI Orchestrator...")
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True, 
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt,  # Injecting the new QA prompt here
    allow_dangerous_requests=True,
    top_k=50 
)

# --- 3. Build the FastAPI Web Server ---
app = FastAPI(title="Cognitive SCADA AI Backend")

class UserQuery(BaseModel):
    question: str

@app.post("/ask-assistant")
async def ask_assistant(query: UserQuery):
    """This endpoint receives a question, runs it through LangChain, and returns the answer."""
    try:
        response = chain.invoke({"query": query.question})
        return {"status": "success", "answer": response["result"]}
        
    except Exception as e:
        # --- NEW CODE: Print the exact error to the terminal! ---
        import traceback
        print("\n--- CRASH REPORT ---")
        traceback.print_exc()
        print("--------------------\n")
        
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting API Server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
