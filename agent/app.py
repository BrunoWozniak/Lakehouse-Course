"""
LangChain SQL Agent with Chainlit UI for Data Lakehouse queries.
Dynamic schema discovery using PyArrow Flight - no hardcoded table schemas.
"""

import os
import logging
import base64
import chainlit as cl
from langchain_mistralai import ChatMistralAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from pyarrow import flight
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
DREMIO_HOST = os.getenv("DREMIO_HOST", "dremio")
DREMIO_PORT = os.getenv("DREMIO_PORT", "32010")
DREMIO_USER = os.getenv("DREMIO_USER", "dremio")
DREMIO_PASSWORD = os.getenv("DREMIO_PASSWORD", "dremio123")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
SCHEMA_PATH = os.getenv("SCHEMA_PATH", "catalog.gold")

logger.info(f"Dremio host: {DREMIO_HOST}:{DREMIO_PORT}")
logger.info(f"Mistral API key configured: {bool(MISTRAL_API_KEY)}")


class DremioClient:
    """PyArrow Flight client for Dremio using Basic auth."""

    def __init__(self):
        self.client = flight.connect(f"grpc://{DREMIO_HOST}:{DREMIO_PORT}")
        self.options = self._create_auth_options()

    def _create_auth_options(self):
        """Create flight options with Basic auth header."""
        auth_string = f"{DREMIO_USER}:{DREMIO_PASSWORD}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        return flight.FlightCallOptions(
            headers=[(b"authorization", f"Basic {auth_encoded}".encode())]
        )

    def execute(self, query: str):
        """Execute SQL query and return results as dict and column names."""
        info = self.client.get_flight_info(
            flight.FlightDescriptor.for_command(query),
            self.options
        )
        reader = self.client.do_get(info.endpoints[0].ticket, self.options)
        table = reader.read_all()
        return table.to_pydict(), table.column_names


# Global client
dremio_client = None


def get_client():
    """Get or create Dremio client."""
    global dremio_client
    if dremio_client is None:
        logger.info("Creating Dremio Flight client...")
        dremio_client = DremioClient()
    return dremio_client


def discover_schema() -> str:
    """Dynamically discover tables and columns from Dremio."""
    logger.info(f"Discovering schema for {SCHEMA_PATH}...")
    client = get_client()

    # Get all tables in the schema
    data, _ = client.execute(f"SHOW TABLES IN {SCHEMA_PATH}")
    tables = data.get("TABLE_NAME", [])
    logger.info(f"Found {len(tables)} tables: {tables}")

    if not tables:
        return "No tables found in the Data Lakehouse."

    # Build schema info for each table
    schema_info = f"Available tables in {SCHEMA_PATH} (use full path in queries):\n\n"

    for i, table_name in enumerate(tables, 1):
        full_path = f"{SCHEMA_PATH}.{table_name}"
        try:
            _, columns = client.execute(f"SELECT * FROM {full_path} LIMIT 1")
            schema_info += f"{i}. {full_path}\n"
            schema_info += f"   Columns: {', '.join(columns)}\n\n"
        except Exception as e:
            logger.warning(f"Could not get schema for {full_path}: {e}")
            schema_info += f"{i}. {full_path}\n"
            schema_info += f"   (schema unavailable)\n\n"

    return schema_info


def run_sql_query(query: str) -> str:
    """Execute SQL query against Dremio and return results."""
    try:
        client = get_client()
        data, columns = client.execute(query)

        if not columns:
            return "Query executed successfully. No results returned."

        # Get row count
        row_count = len(data[columns[0]]) if columns else 0
        if row_count == 0:
            return "Query executed successfully. No results returned."

        # Format as table
        output = " | ".join(columns) + "\n"
        output += "-" * len(output) + "\n"

        for i in range(min(20, row_count)):
            row_values = [str(data[col][i]) for col in columns]
            output += " | ".join(row_values) + "\n"

        if row_count > 20:
            output += f"\n... ({row_count} total rows, showing first 20)"

        return output
    except Exception as e:
        return f"SQL Error: {str(e)}"


AGENT_PROMPT = PromptTemplate.from_template("""You are a SQL expert for a Data Lakehouse. You MUST ALWAYS query the database to answer questions.

CRITICAL RULES:
1. NEVER answer without first executing a SQL query using the sql_query tool
2. NEVER make up or hallucinate data - only use actual query results
3. If a query fails or returns no results, say "I could not find data for that question" - do NOT invent an answer
4. ALWAYS filter out NULL values in your WHERE clause when querying specific fields (e.g., WHERE column IS NOT NULL)
5. Use the full table path: catalog.gold.table_name

{table_info}

Tools: {tools}
Tool names: {tool_names}

You must ALWAYS use this EXACT format:

Thought: I need to query the database
Action: sql_query
Action Input: SELECT ... FROM catalog.gold.table_name ...

After you see the Observation with results, respond with ONLY:

Thought: I now have the results
Final Answer: [your answer here]

NEVER skip "Final Answer:" - it must appear after your last Thought.

Begin!

Question: {input}
{agent_scratchpad}""")


def create_agent(table_info: str):
    """Create the SQL agent with discovered schema."""
    logger.info("Creating agent...")

    llm = ChatMistralAI(
        model=MISTRAL_MODEL,
        temperature=0,
        mistral_api_key=MISTRAL_API_KEY
    )

    tools = [
        Tool(
            name="sql_query",
            func=run_sql_query,
            description="Execute a SQL query against the Dremio database. Input should be a valid SQL query."
        )
    ]

    prompt = AGENT_PROMPT.partial(table_info=table_info)
    agent = create_react_agent(llm, tools, prompt)

    def parsing_error_handler(_error):
        return "Format error. Remember: after Observation, you must respond with exactly:\nThought: I now have the results\nFinal Answer: [your answer based on the data]"

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=parsing_error_handler,
        max_iterations=10,
        return_intermediate_steps=True
    )


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    logger.info("Chat session starting...")

    if not MISTRAL_API_KEY:
        await cl.Message(content="**ERROR**: MISTRAL_API_KEY not found. Add it to agent/.env").send()
        return

    try:
        # Discover schema dynamically
        logger.info("Discovering database schema...")
        table_info = discover_schema()
        logger.info(f"Schema discovered:\n{table_info}")

        # Create agent with discovered schema
        logger.info("Creating agent...")
        agent = create_agent(table_info)

        cl.user_session.set("agent", agent)

        # Count tables for welcome message
        client = get_client()
        data, _ = client.execute(f"SHOW TABLES IN {SCHEMA_PATH}")
        table_count = len(data.get("TABLE_NAME", []))

        welcome_msg = f"""**Ready!** Connected to your Data Lakehouse.

**{table_count} tables** discovered in the Gold layer.

**Try asking:**
- "Show me the top 5 customers by total spent"
- "Which cities have the most charging sessions?"
- "What's the average transaction value?"
"""
        await cl.Message(content=welcome_msg).send()
        logger.info("Agent initialized successfully")

    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}", exc_info=True)
        await cl.Message(content=f"**Initialization Error**: {str(e)}").send()


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages."""
    agent = cl.user_session.get("agent")

    if not agent:
        await cl.Message(content="Agent not initialized. Please refresh the page.").send()
        return

    msg = cl.Message(content="Querying...")
    await msg.send()

    try:
        response = await cl.make_async(agent.invoke)({"input": message.content})
        output = response.get("output", "No output generated")

        # Extract SQL query from intermediate steps
        sql_queries = []
        intermediate_steps = response.get("intermediate_steps", [])
        for action, _ in intermediate_steps:
            if hasattr(action, "tool_input"):
                sql_queries.append(action.tool_input)

        # Build response with query
        if sql_queries:
            queries_text = "\n\n".join([f"```sql\n{q}\n```" for q in sql_queries])
            msg.content = f"**SQL Query:**\n{queries_text}\n\n## Answer\n\n{output}"
        else:
            msg.content = f"## Answer\n\n{output}"
        await msg.update()

    except Exception as e:
        logger.error(f"Query error: {str(e)}", exc_info=True)
        msg.content = f"**Error**: {str(e)}"
        await msg.update()
