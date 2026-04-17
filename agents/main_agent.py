from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
import ast
import math

class Agent:
    def __init__(self):
        self.llm = ChatVertexAI(model_name="gemini-2.0-flash-001", project="gen-ai-poc-onboarding", location="us-central1")
        self.tools_map = {t.name: t for t in self._get_tools()}
        self.llm_with_tools = self.llm.bind_tools(list(self.tools_map.values()))
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self):
        import yaml
        try:
            with open("config/config.yaml", "r") as f:
                config = yaml.safe_load(f)
                return config.get("system_prompt", "You are a helpful AI agent.")
        except FileNotFoundError:
            return "You are a helpful AI agent."

    def _get_tools(self):
        from tools.tool_manager import get_tools
        return get_tools()

    def run(self, message: str) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message),
        ]
        # Agentic loop: keep calling LLM until no more tool calls
        for _ in range(10):  # max iterations to prevent infinite loops
            try:
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)
                if not response.tool_calls:
                    break
                # Execute each tool call and feed results back
                for tc in response.tool_calls:
                    fn = self.tools_map.get(tc["name"])
                    user_query = tc["args"].get("expression", "") if tc["name"] == "calculate" else message # Use expression for calculate, original message otherwise
                    tool_result = fn.invoke(tc["args"]) if fn else f"Unknown tool: {tc['name']}"
                    messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))
                    self._ingest_to_rag(user_query, str(tool_result), tc["name"]) # Ingest data to RAG
            except Exception as e:
                # If LLM fails, try calculator tool directly for math-related queries
                if "calculate" in self.tools_map and self._is_math_related(message):
                    try:
                        tool_result = self.tools_map["calculate"].invoke({"expression": message})
                        return str(tool_result)
                    except Exception as e2:
                        return f"Error: Failed to generate response from LLM and calculator tool. {e2}"
                else:
                    return f"Error: Failed to generate response from LLM. {e}"

        return response.content if hasattr(response, "content") else str(response)

    def _is_math_related(self, message: str) -> bool:
        """Simple heuristic to check if the message is likely math-related."""
        return any(op in message for op in "+-*/^()") or any(word in message for word in ["calculate", "compute", "sum", "product"])

    def _ingest_to_rag(self, query: str, mcp_result: str, tool_name: str = "mcp_tool") -> None:
        """Ingest MCP-fetched data into ChromaDB for future RAG retrieval."""
        try:
            import chromadb, hashlib, os
            from datetime import datetime
            chroma_path = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
            client = chromadb.PersistentClient(path=os.path.abspath(chroma_path))
            collection = client.get_or_create_collection("knowledge_base", metadata={"hnsw:space": "cosine"})
            doc_id = "mcp_" + hashlib.md5(f"{tool_name}:{query}".encode()).hexdigest()[:16]
            chunk_id = f"{doc_id}_chunk_0"
            collection.upsert(
                ids=[chunk_id],
                documents=[f"Tool: {tool_name}\nQuery: {query}\nResult: {mcp_result}"],
                metadatas=[{"doc_id": doc_id, "title": f"MCP: {tool_name}", "source": "mcp_tool",
                             "chunk_index": 0, "ingested_at": datetime.utcnow().isoformat()}],
            )
        except Exception as e:
            print(f"Error ingesting to RAG: {e}")  # Log the error for debugging
            pass  # RAG ingestion is best-effort, never block the response