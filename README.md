# Cognitive SCADA Assistant: Neuro-Symbolic AI for Industrial Automation

**Temple University | CIS 5590: Artificial General Intelligence** **Author:** Neil Naroznowski  

---

## 📖 Project Overview
Modern Building Automation Systems (BAS)—such as those provided by Siemens, Johnson Controls, and Automated Logic—are exceptional at monitoring telemetry but lack semantic reasoning capabilities. Conversely, standard Large Language Models (LLMs) possess vast semantic knowledge but suffer from "hallucinations" because they lack spatial and physical awareness of industrial layouts. 

The **Cognitive SCADA Assistant** bridges this gap using a **Neuro-Symbolic AI architecture**. By strictly grounding an LLM within a Neo4j graph database representing physical building topology (Graph-RAG), this project creates a deterministic, hallucination-free AI assistant. Operators can use natural language to query complex upstream and downstream HVAC relationships directly within their SCADA dashboard.

---

## 🏗️ Architecture & Software Stack
To achieve real-time interoperability between modern AI libraries and industrial operational technology (OT), the architecture was decoupled into a 4-tier stack. 

* **Frontend:** [Inductive Automation Ignition (Perspective)](https://inductiveautomation.com/)  
  *Serves as the industrial SCADA interface. Because Ignition runs on Jython (which does not support modern Python AI libraries), HTTP clients were utilized to bridge the OT and IT networks.*
* **Middleware:** [FastAPI](https://fastapi.tiangolo.com/)
  *A lightweight Python REST server that exposes the AI logic to the Ignition SCADA system.*
* **Orchestration:** [LangChain](https://www.langchain.com/) & [Google Gemini](https://ai.google.dev/)  
  *Utilizes `GraphCypherQAChain` to translate natural language into Cypher queries, route them to the database, and format the returned data via the Gemini-1.5/2.0-Flash LLM.*
* **Data Layer:** [Neo4j](https://neo4j.com/)  
  *A high-performance graph database used to store the physical and logical relationships of the facility's infrastructure.*

---

## 🗄️ The Semantic Model: Project Haystack
The foundation of the graph database is built upon the **[Project Haystack](https://project-haystack.org/)** open-source metadata standard. Specifically, this project models the "site-b" (Bravo) hospital dataset.

Traditional flat-tag systems were transformed into a Knowledge Graph where physical relationships are first-class entities:
* **`[:AIRREF]`**: Models airflow dependency (e.g., Variable Air Volume (VAV) boxes pointing upstream to their parent Roof Top Unit (RTU)).
* **`[:EQUIPREF]`**: Maps individual sensor points and commands to their respective physical equipment.
* **Nodes:** Over 140 pieces of equipment and 900 individual semantic points were mapped into the graph to allow the AI to physically "traverse" the building's physics.

---

## 📅 Project Scheduling & Development Phases

1. **Phase 1: Metadata Modeling & Database Construction** * Analyzed the Haystack Bravo dataset.
   * Engineered the schema and imported nodes/edges into Neo4j.
2. **Phase 2: AI Orchestration & Logic Translation** * Developed custom LangChain prompt templates to strictly govern the LLM's query generation.
   * Forced the AI to navigate the specific "Upward" physics of the `AIRREF` tags.
3. **Phase 3: Middleware API Development** * Wrapped the LangChain pipeline into a scalable FastAPI REST application to bypass Ignition's Jython limitations.
4. **Phase 4: SCADA Integration & Validation Testing** * Built the Perspective chat interface.
   * Conducted edge-case testing, resolving severe LLM safety fallback triggers and navigating Google Cloud API rate limits (HTTP 429 errors).

---

## 🧠 Learnings & Takeaways
1. **API Rate Limiting is a Critical Bottleneck:** Free-tier limits for cutting-edge LLMs (like Gemini 2.5 Flash) restrict rapid iterative testing. Production environments require dedicated provisioned throughput or localized open-source models (e.g., Llama 3) to guarantee SCADA uptime.
2. **Prompt Engineering for Determinism:** Default LLM behaviors often result in "I don't know" fallbacks when fed raw JSON database outputs. Explicit QA prompt templates are mandatory to force the LLM to trust the graph database as the absolute source of truth.
3. **Decoupling OT and IT:** Using FastAPI as a microservice is an incredibly effective architectural pattern for bringing modern Python machine learning into legacy or Java-based industrial environments.

---

## 🚀 Future Work & Scalability
Moving forward, this proof-of-concept will be expanded natively into broader Ignition projects with the following enhancements:
* **System Expansion:** Scaling the graph beyond HVAC to include Electrical Power distribution, Medical Gas lines, and Life Safety networks.
* **Predictive Diagnostics:** Integrating real-time sensor telemetry from Ignition back into the Neo4j graph. This will allow the AI to not only trace topology but also analyze active fault states and predict downstream comfort impacts before they occur.
* **Local LLM Deployment:** Migrating from cloud-based APIs to air-gapped, locally hosted LLMs to meet strict industrial cybersecurity requirements.
