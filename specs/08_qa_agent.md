# Specification: QA Agent (ai_core/agents)

## 1. Overview
This agent answers user questions based on the Knowledge Base (Vector DB) and Chat History. It implements the RAG (Retrieval Augmented Generation) pattern.

## 2. Requirements

### 2.1. Core Logic
-   **Framework:** Must use `google.adk.agents.llm_agent.Agent` (or equivalent ADK class).
-   **Model:** `Settings.GEMINI_MODEL_SMART` (e.g., `gemini-2.5-pro`).
-   **Input:** User query (str), Chat History (optional context).
-   **Output:** Answer string + Source references.

### 2.2. RAG Flow
1.  **Retrieval:**
    -   Call `VectorStore.search(query)` to get relevant chunks (documents and past messages).
2.  **Augmentation:**
    -   Construct a prompt including the retrieved chunks.
    -   **Critical Instruction:** *"Answer the question based ONLY on the provided context. If the answer is not in the context, say 'Я не знаю' (I don't know). Do not hallucinate."*
3.  **Generation:**
    -   Call LLM.

### 2.3. Source Attribution
-   The agent should return the filenames or message IDs of the chunks used to generate the answer.

## 3. Implementation Details
-   Create `ai_core/agents/qa.py`.
-   Prompt engineering is key here to prevent hallucinations.
-   **Resilience:** Use `@retry` decorator from `tenacity` library to handle API errors.

## 4. Verification & Definition of Done
-   [ ] Agent retrieves relevant chunks for a known query.
-   [ ] Agent answers correctly when info is present.
-   [ ] **Agent answers "Я не знаю" when info is missing.** (Critical test).
-   [ ] **Manual Test:** Run `tests/manual/test_qa.py`:
    -   Ingest a specific fact (e.g., "The secret code is 1234").
    -   Ask "What is the secret code?" -> Expect "1234".
    -   Ask "What is the weather on Mars?" -> Expect "Я не знаю".
