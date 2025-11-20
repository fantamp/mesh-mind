# Specification: Summarizer Agent (ai_core/agents)

## 1. Overview
This agent is responsible for generating concise summaries of chat history. It uses the "Fast" Gemini model to process a batch of messages.

## 2. Requirements

### 2.1. Core Logic
-   **Framework:** Must use `google.adk.agents.llm_agent.Agent` (or equivalent ADK class).
-   **Model:** `Settings.GEMINI_MODEL_SMART` (e.g., `gemini-2.5-pro`).
-   **Input:** User query (str), Chat History (optional context).
-   **Output:** A markdown-formatted summary string.

### 2.2. Functionality
-   **`summarize(messages: List[Message]) -> str`**:
    -   Construct a prompt: *"You are a helpful assistant. Summarize the following conversation concisely in Russian (or language of the chat). Highlight key decisions and action items."*
    -   Call LLM.
    -   Return result.

### 2.3. Context Window Management
-   **Strategy:** Simply feed all messages (or the last 1000 if extremely large). Gemini 1.5/2.0 has a massive context window (1M+ tokens), so complex truncation is YAGNI for this MVP.

## 3. Implementation Details
-   Create `ai_core/agents/summarizer.py`.
-   Use `google-generativeai` to call the model.
-   **Resilience:** Use `@retry` decorator from `tenacity` library to handle API errors (429, 500, etc.).

## 4. Verification & Definition of Done
-   [ ] Agent accepts a list of mock messages.
-   [ ] Agent returns a non-empty string.
-   [ ] Summary accurately reflects the content of the mock messages (manual check).
-   [ ] **Manual Test:** Run `tests/manual/test_summarizer.py` with 10 dummy messages and print the output.
