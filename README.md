# Cerina Protocol Foundry 🧠

> An autonomous multi-agent system for generating safe, empathetic CBT (Cognitive Behavioral Therapy) exercises using LangGraph, PostgreSQL persistence, and Model Context Protocol (MCP) integration.

![Python](https://img.shields.io/badge/python-3.13-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-1.0.4-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Checkpointing-orange)
![MCP](https://img.shields.io/badge/MCP-Enabled-purple)

---

## 🎯 Overview

Cerina is not just a chatbot—it's a **clinical foundry** powered by autonomous AI agents that:
- **Draft** CBT exercises based on user queries
- **Validate** content for safety (no self-harm, medical advice, or triggering content)
- **Critique** for empathy, clarity, and clinical correctness
- **Iterate** autonomously until ready for human review
- **Pause** for human-in-the-loop approval before finalizing

### Key Features
- ✅ **Multi-Agent Architecture**: Supervisor-Worker pattern with autonomous loops
- ✅ **PostgreSQL Checkpointing**: Crash-resistant, resume-anywhere execution
- ✅ **Real-Time Streaming UI**: Watch agents debate and refine in real-time
- ✅ **Human-in-the-Loop**: Edit, approve, or reject drafts before saving
- ✅ **MCP Integration**: Expose workflow as a tool for Claude Desktop and other MCP clients
- ✅ **Session History**: Track all past queries and generated exercises

---

## 🏗️ Architecture

### Agent Topology: Supervisor-Worker Pattern

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│              SUPERVISOR                         │
│  (Routes tasks, decides when "good enough")     │
└──┬──────────────────────────────────────────┬───┘
   │                                          │
   ▼                                          │
┌──────────┐    ┌──────────┐    ┌──────────┐ │
│ DRAFTER  │───▶│  SAFETY  │───▶│  CRITIC  │─┘
│          │    │ GUARDIAN │    │ REVIEWER │
└──────────┘    └──────────┘    └──────────┘
   │                                     │
   │  ◄──────── Loop if failed ─────────┘
   │
   ▼
┌─────────────────┐
│ HUMAN APPROVAL  │ ◄── Graph pauses here
│  (Edit/Approve) │
└────────┬────────┘
         │
         ▼
    ┌─────────┐
    │  SAVE   │
    │  TO DB  │
    └─────────┘
```

### Agents
1. **Supervisor**: Orchestrates workflow, routes to agents, decides when to halt
2. **Drafter**: Creates CBT exercises, learns from rejected drafts
3. **Safety Guardian**: Checks for unsafe content (self-harm, medical advice)
4. **Clinical Critic**: Reviews empathy, clarity, and CBT correctness

### State Management ("The Blackboard")
```python
AgentState:
  - user_query: str
  - draft: str                    # Current working draft
  - previous_drafts: List[str]    # Version history
  - safety_notes: List[str]       # Safety agent scratchpad
  - critic_notes: List[str]       # Critic agent scratchpad
  - metadata:
      - iterations: int
      - safety_pass: bool
      - critic_pass: bool
      - user_rejected: bool
      - edited_by_user: bool
  - final_output: str             # Approved & saved
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL database (local or cloud, e.g., Neon)
- API keys: Groq or OpenAI (for LLM)

### Installation

1. **Clone the repository**
```bash
git clone Cerina-Foundry
cd Cerina-Foundry
```

2. **Install dependencies**
```bash
# Using uv (recommended)
uv sync

# OR using pip
uv add -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file:
```env
# Database (PostgreSQL connection string)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# LLM API Keys (choose one)
GROQ_API_KEY=your_groq_api_key
# OR
OPENAI_API_KEY=your_openai_api_key

# LangSmith (optional, for tracing)
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=cerina-foundry
```

4. **Initialize the database**
The app will auto-create tables on first run, but you can verify:
```bash
python db_test.py
```

5. **Run the Flask app**
```bash
python main.py
```

The dashboard will be available at: **http://localhost:5000**

---

## 🖥️ Using the Web Dashboard

### Creating a Session
1. Click **"New Session"** in the sidebar
2. Enter a query (e.g., *"Create an exposure hierarchy for social anxiety"*)
3. Click **"Start Generation"**

### Watching Agents Work
- **Agent Stream Panel**: See real-time logs of each agent's actions
- **Status Badges**: Monitor iterations, safety checks, and critic reviews
- **Clinical Notes Panel**: View detailed feedback from Safety and Critic agents

### Human-in-the-Loop Approval
When the draft is ready, the **Action Bar** appears:
- **Reject**: Discard draft, agents create a new one from scratch
- **Edit**: Modify the draft manually, then re-validate through Safety/Critic
- **Approve & Save**: Finalize and save to database

### Session History
- Click any session in the sidebar to view its history
- Delete sessions with the trash icon

---

## 🔌 MCP Integration (Machine-to-Machine)

### What is MCP?
The [Model Context Protocol](https://modelcontextprotocol.io) allows AI assistants (like Claude Desktop) to use your LangGraph workflow as a tool.

### Setup for Claude Desktop

1. **Locate Claude Desktop config**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add Cerina server**:
```json
{
  "mcpServers": {
    "cerina_foundry": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Users/rouna/PycharmProjects/Cerina",  # (use absolute path were all requiremnts are installed)
        "run",
        "python",
        "MCP/cerina_mcp_tools.py"
      ]
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Test it**:
   - In Claude Desktop, type: *"Ask Cerina Foundry to create a sleep hygiene protocol"*
   - Claude will invoke your multi-agent workflow and return the generated draft

### MCP Tool: `generate_cbt_exercise`
```python
generate_cbt_exercise(
    topic: str,           # e.g., "Sleep Hygiene"
    instructions: str     # Optional details
) -> str                  # Returns generated CBT exercise
```

---

## 📂 Project Structure

```
Cerina/
├── agent/
│   ├── drafter_agent.py       # Creates CBT exercises
│   ├── safety_agent.py        # Safety validation
│   ├── critic_agent.py        # Quality review
│   ├── supervisor_agent.py    # Orchestration
│   ├── prompts.py             # Agent prompts
│   └── llm_client.py          # LLM wrapper
├── MCP/
│   └── cerina_mcp_tools.py    # MCP server
├── db/
│   └── config.py              # Database config
├── templates/
│   └── index.html             # Web dashboard
├── checkpoint_store.py        # PostgreSQL checkpointer
├── graph_builder.py           # LangGraph definition
├── state.py                   # AgentState schema
├── main.py                    # Flask API
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

---

## 🧪 Testing

### Manual Testing
1. **Test the web UI**:
   ```bash
   python main.py
   # Visit http://localhost:5000
   ```

2. **Test MCP integration**:
   ```bash
   # Run MCP server standalone
   python MCP/cerina_mcp_tools.py or run python mcp_caller.py
   
   # Use mcp-use CLI to test
   mcp-use cerina_foundry generate_cbt_exercise --topic "Sleep Hygiene"
   ```

3. **Test database persistence**:
   ```bash
   python db_test.py
   ```

### Crash Recovery Test
1. Start a generation
2. Kill the Flask process mid-execution
3. Restart Flask
4. Load the session—it should resume from the last checkpoint

---

## 🛠️ Configuration

### LLM Provider
Edit `agent/llm_client.py` to switch between Groq/OpenAI:
```python
# Current: OpenAI
client = OpenAI(model="gpt-4o-mini")

# Switch to Groq:
# from lgroq import ChatGroq
# llm = ChatGroq(model="openai/gpt-oss-120b")
```

### Database
Update `DATABASE_URL` in `.env` to use:
- **Local PostgreSQL**: `postgresql://user:pass@localhost:5432/cerina`
- **Neon (cloud)**: `postgresql://user:pass@ep-xxx.neon.tech/cerina?sslmode=require`

### Agent Prompts
Customize agent behavior in `agent/prompts.py`:
- `DRAFTER_PROMPT`: How the drafter creates exercises
- `SAFETY_PROMPT`: What safety checks to perform
- `CRITIC_PROMPT`: Quality review criteria

---

## 📊 Database Schema

### `checkpoints` (auto-created by LangGraph)
Stores graph execution state for crash recovery.

### `saved_exercises`
```sql
CREATE TABLE saved_exercises (
    id SERIAL PRIMARY KEY,
    thread_id TEXT,
    user_query TEXT,
    final_output TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### `session_metadata`
```sql
CREATE TABLE session_metadata (
    id TEXT PRIMARY KEY,
    user_query TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---


**Contents**:
1. React UI demo: Agents debating, human-in-the-loop approval
2. MCP demo: Claude Desktop triggering workflow
3. Code walkthrough: State definition and checkpointer logic

---

## 🤝 Contributing

This is a sprint assignment project. For production use:
1. Add comprehensive error handling
2. Implement rate limiting
3. Add authentication/authorization
4. Write unit and integration tests
5. Add monitoring and logging

---

## 📝 License

MIT License

---

## 🙏 Acknowledgments

- **LangGraph**: For the agent orchestration framework
- **Model Context Protocol**: For AI interoperability standards
- **Anthropic**: For Claude and MCP documentation
- **OpenAI**: For LLM inference  ## we can also use grog for fast llm inference 

---

## 📧 Contact

Name: Rounak Raj

Email: rajrounak366@gmail.com

---

**Built with ❤️ for the Cerina "Agentic Architect" Sprint**



