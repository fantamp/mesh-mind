# Kaggle Submission: Enterprise Agents Track

## Введение
Это требования для написания writeup для submission на Kaggle.
На Kaggle просили выбрать трек. Выбрали следующий: Enterprise Agents
Submission на kaggle будется делать путем выкладывания этого проекта в публичный GitHub репозиторий и написание writeup'ов в папке `kaggle/` 

## Требования к Submission
Ниже описаны исходные требования к writeup на Kaggle:

### Features to Include in Your Agent Submission
In your submission, you must demonstrate what you’ve learned in this course by applying at least three (3) of the key concepts listed below:

- Multi-agent system, including any combination of:
  - Agent powered by an LLM
  - Parallel agents
  - Sequential agents
  - Loop agents
- Tools, including:
  - MCP
  - custom tools
  - built-in tools, such as Google Search or Code Execution
  - OpenAPI tools
  - Long-running operations (pause/resume agents)
- Sessions & Memory
  - Sessions & state management (e.g. InMemorySessionService)
  - Long term memory (e.g. Memory Bank)
- Context engineering (e.g. context compaction)
- Observability: Logging, Tracing, Metrics
- Agent evaluation
- A2A Protocol
- Agent deployment

### Evaluation

Your submission will be evaluated on three categories earning up to a maximum of 100 points.

*   Category 1: The Pitch (max 30 points)
*   Category 2: The Implementation (max 70 points)
*   Bonus: (max 20 points)

Note: Bonus points are added to the total of Category 1 and 2 points, up to a maximum of total 100 points.

Example scoring evaluation: Category 1 score of 30 points + Category 2 score of 60 points + Bonus points of 20 = 100 points.

| Criteria (points) | Description |
| --- | --- |
| **Category 1: The Pitch (Problem, Solution, Value)** (30 points total) | This is where you'll be evaluated on the "why" and "what" of your project and how well you communicate your vision. |
| **Core Concept & Value** (15 points) | Your project's central idea, its relevance to the track for the submission; focused on innovation and value. The use of agents should be clear, meaningful and central to your solution. |
| **Writeup** (15 points) | How well your written submission articulates the problem you're solving, your solution, its architecture, and your project's journey. |
| **Category 2: The Implementation (Architecture, Code)** (70 points total) | This is where you'll be evaluated on the "how" of your project. This includes the quality of your code, technical design, and AI integration. |
| **Technical Implementation** (50 points) | In your submission, you must demonstrate what you’ve learned in this course by applying at least three (3) of the key concepts listed in the [Features To Include In Your Agent Submission section.](https://www.kaggle.com/competitions/agents-intensive-capstone-project/overview#agents-intensive-course-capstone-2025/overview/features-to-include-in-your-agent-submission) For this criteria, we will assess the quality of your solution's architecture, and your code, and the meaningful use of agents in your solution. Your code should contain comments pertinent to implementation, design and behaviors. Participants are **not** required to deploy their agents to a live public endpoint for judging purposes; however, if you do deploy, please provide documentation to reproduce the deployment. 🚨REMINDER: DO NOT INCLUDE ANY API KEYS OR PASSWORDS IN YOUR CODE. |
| **Documentation** (20 points) | Your submission (when submitting via GitHub) should contain a README.md file explaining the problem, solution, architecture, instructions for setup, and relevant diagrams or images where appropriate. If you are solely submitting a Kaggle notebook, please provide documentation directly inline via Markdown Cells of the notebook. |
| **Bonus points (Tooling, Model Use, Deployment, Video)** 20 points total | You can earn optional bonus points. |
| **Effective Use of Gemini** (5 points) | Use of Gemini to power your agent (or at least one sub-agent). |
| **Agent Deployment** (5 points) | If you either have code or otherwise show evidence (e.g. in your code or write up) of having deployed your agent using [Agent Engine](https://cloud.google.com/agent-builder/agent-engine/overview) or a similar Cloud-based runtime (e.g. [Cloud Run](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run)). |
| **YouTube Video Submission** (10 points) | Your video should include clarity, conciseness and quality of messaging. It should be under 3 min long. It should articulate: Problem Statement: Describe the problem you're trying to solve, and why you think it's an important or interesting problem to solve. Agents: Why agents? How can agents uniquely help solve that problem? Architecture: Images and a description of the overall agent architecture. Demo: demo of your solution, which can include images, an animation, or a video of the agent working. The Build: How you created it, what tools or technologies you used. |

### Структура файлов в папке `kaggle/`
В папке `kaggle/` должны быть следующие файлы:
   - writeup.ru.md - русский язык, максимум 1400 слов
   - writeup.en.md - английский язык, максимум 1400 слов
   - rules.md - правила на русском языке по написанию файлов writeup.*.md, максимум 20 строк. Там явно должен быть указан язык для каждого файла, а также указано, что русскоязычный файл ведущий, а англоязычный всегда должен обновляться после изменения русскоязычного файла. В правилах должно быть указано, что writeup'ы не должны превышать 1400 слов.
   - recommendations_before_submission.md - рекомендации по проекту перед тем, как он будет выложен в публичный GitHub репозиторий. Рекомендации должны быть связаны с тем, чтобы проект лучше соответствовал требованиям Kaggle. Например, возможно, в проекте легко можно сделать какую-то доработку и лучше выполнить требования Kaggle, или, возможно, в проекте что-то реализовано, но реализовано плохо, и это можно улучшить.
   - kaggle/specs/ - папка с двумя спеками (каждая спека максимум 50 строк) для написания:
      - recommendations_before_submission.md
      - writeup.ru.md и writeup.en.md
      

## Полезная документация и ссылки
- Google Agent Development Kit (ADK): https://google.github.io/adk-docs/
- Документация проекта: папка docs/
- Kaggle соревнование в котором хотим сделать Submission: https://www.kaggle.com/competitions/agents-intensive-capstone-project