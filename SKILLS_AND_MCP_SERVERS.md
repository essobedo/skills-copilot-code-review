# Skills and MCP Servers Available on GitHub Copilot Agent

## Skills

### prompt-optimizer
**Purpose**: Optimize prompts for any LLM model within chat interfaces

**Trigger phrases**:
- "rewrite this prompt"
- "make this a better prompt"
- "optimize this prompt"
- "turn this into a prompt"
- "help me prompt this"
- "draft a prompt that..."

---

### customize-cloud-agent
**Purpose**: Customize the Copilot cloud agent environment, including configuration, dependencies, runners, and settings

**Trigger phrases**:
- "copilot-setup-steps"
- "configure cloud agent environment"

---

## MCP Servers

### GitHub MCP Server
Provides comprehensive GitHub API access including:
- Repository management
- Pull request operations
- Issue management
- Code searching and analysis
- GitHub Actions workflows
- Commit operations
- Release management

---

### Playwright Browser
Web automation and testing capabilities:
- Navigate and interact with web pages
- Take screenshots and accessibility snapshots
- Fill forms and perform clicks
- Drag and drop operations
- Handle dialogs and file uploads

---

### SQL Database
Local SQLite database for task tracking:
- `todos` table - Task tracking
- `todo_deps` table - Task dependencies

---

### Session Store SQL
Cloud and local session store queries using DuckDB/SQLite:
- Query past sessions and turn history
- Track changes across sessions
- Search for session context and artifacts

---

## Reference

For more information on GitHub Copilot agents and capabilities, refer to the [GitHub Copilot documentation](https://docs.github.com/en/copilot).
