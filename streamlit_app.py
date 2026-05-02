"""Streamlit MCP client — chat terminal for the brain MCP server."""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from typing import Any

import streamlit as st
from anthropic import AsyncAnthropic
from mcp import ClientSession
from mcp.client.sse import sse_client

from src.config import ANTHROPIC_FOUNDRY_BASE_URL, ANTHROPIC_FOUNDRY_API_KEY, MCP_API_KEY

MODEL = "claude-sonnet-4-6"
MCP_URL = "http://127.0.0.1:8765/sse"

SYSTEM = """You are a personal AI assistant with access to Kris's second brain vault.
Use the available brain tools to search, recall, write, and relate knowledge.
Be concise and cite your sources using [[Page Title]] wikilinks when referencing vault pages."""


# ---------------------------------------------------------------------------
# MCP server lifecycle (subprocess)
# ---------------------------------------------------------------------------

def _start_mcp_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        ["python3", "-m", "src.server", "--transport", "sse"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Give the server a moment to bind
    time.sleep(2)
    return proc


# ---------------------------------------------------------------------------
# Async helpers — MCP tool discovery and single-turn execution
# ---------------------------------------------------------------------------

async def _fetch_tools() -> list[dict[str, Any]]:
    """Connect to MCP server and return tools in Anthropic format."""
    headers = {"x-api-key": MCP_API_KEY} if MCP_API_KEY else {}
    async with sse_client(MCP_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "input_schema": t.inputSchema,
                }
                for t in result.tools
            ]


async def _call_tool(name: str, args: dict[str, Any]) -> str:
    """Call a single MCP tool and return the text result."""
    headers = {"x-api-key": MCP_API_KEY} if MCP_API_KEY else {}
    async with sse_client(MCP_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, args)
            parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    parts.append(content.text)
            return "\n".join(parts) or "(empty result)"


async def _chat_turn(messages: list[dict], tools: list[dict]) -> tuple[str, list[dict]]:
    """
    Run one chat turn against Claude with MCP tools.
    Returns (assistant_text, updated_messages).
    """
    client = AsyncAnthropic(
        base_url=ANTHROPIC_FOUNDRY_BASE_URL,
        api_key=ANTHROPIC_FOUNDRY_API_KEY,
        default_headers={"api-key": ANTHROPIC_FOUNDRY_API_KEY},
    )

    loop_messages = list(messages)
    tool_call_log: list[str] = []

    for _ in range(20):  # safety cap on tool loop
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            tools=tools,
            messages=loop_messages,
        )

        if response.stop_reason == "end_turn":
            text = "\n".join(
                b.text for b in response.content if hasattr(b, "text") and b.text
            )
            loop_messages.append({"role": "assistant", "content": response.content})
            return text, loop_messages

        if response.stop_reason == "tool_use":
            loop_messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_call_log.append(f"🔧 `{block.name}` {json.dumps(block.input)[:120]}")
                tool_output = await _call_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_output,
                })
            loop_messages.append({"role": "user", "content": tool_results})
        else:
            break

    text = f"(Loop ended — stop_reason={response.stop_reason})"
    if tool_call_log:
        text = "\n".join(tool_call_log) + "\n\n" + text
    loop_messages.append({"role": "assistant", "content": text})
    return text, loop_messages


def run_async(coro):
    """Run an async coroutine from sync Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Brain — Second Brain Terminal",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
/* Dark terminal aesthetic */
body, .stApp { background-color: #0d0d0d; }

.stChatMessage { border-radius: 8px; margin-bottom: 8px; }

/* User messages */
[data-testid="stChatMessage"][aria-label*="user"] {
    background: #1a1a2e;
}

/* Assistant messages */
[data-testid="stChatMessage"][aria-label*="assistant"] {
    background: #0f1923;
}

/* Input */
.stChatInputContainer { border-top: 1px solid #2a2a3e; }
textarea { background: #111 !important; color: #e0e0e0 !important; }

h1 { font-family: 'JetBrains Mono', monospace; color: #7ec8e3; }
h2, h3 { color: #a8d8ea; }
code { color: #c3e88d; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #111; }
</style>
""", unsafe_allow_html=True)


# --- Session state initialisation ---
if "server_proc" not in st.session_state:
    st.session_state.server_proc = None
if "tools" not in st.session_state:
    st.session_state.tools = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "server_status" not in st.session_state:
    st.session_state.server_status = "stopped"


# --- Sidebar ---
with st.sidebar:
    st.markdown("## 🧠 Brain MCP")

    status_color = {"stopped": "🔴", "starting": "🟡", "running": "🟢"}.get(
        st.session_state.server_status, "⚪"
    )
    st.markdown(f"**Server:** {status_color} {st.session_state.server_status}")

    if st.session_state.server_status == "stopped":
        if st.button("▶ Start MCP Server", use_container_width=True):
            with st.spinner("Starting server..."):
                st.session_state.server_status = "starting"
                proc = _start_mcp_server()
                st.session_state.server_proc = proc
                try:
                    tools = run_async(_fetch_tools())
                    st.session_state.tools = tools
                    st.session_state.server_status = "running"
                    st.success(f"Connected — {len(tools)} tools loaded")
                    st.rerun()
                except Exception as e:
                    st.session_state.server_status = "stopped"
                    st.error(f"Failed to connect: {e}")

    elif st.session_state.server_status == "running":
        if st.button("⏹ Stop Server", use_container_width=True):
            if st.session_state.server_proc:
                st.session_state.server_proc.terminate()
                st.session_state.server_proc = None
            st.session_state.server_status = "stopped"
            st.session_state.tools = []
            st.rerun()

        st.markdown("---")
        st.markdown("**Tools available:**")
        for tool in st.session_state.tools:
            st.markdown(f"- `{tool['name']}`")

    st.markdown("---")
    st.markdown("**Model:**")
    st.caption(MODEL)

    if st.button("🗑 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("**Quick commands:**")
    quick_cmds = [
        "Search for MCP in my vault",
        "What do I know about Kris Mekwinski?",
        "Show me recent learning notes",
        "Compile inbox",
    ]
    for cmd in quick_cmds:
        if st.button(cmd, use_container_width=True, key=f"quick_{cmd}"):
            st.session_state._pending_message = cmd
            st.rerun()


# --- Main area ---
st.markdown("# 🧠 Second Brain Terminal")

if st.session_state.server_status != "running":
    st.info("Start the MCP server from the sidebar to begin chatting.")

# Display chat history
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    if isinstance(content, list):
        # Extract text from content blocks
        text = " ".join(
            b.get("text", "") if isinstance(b, dict) else getattr(b, "text", "")
            for b in content
            if (isinstance(b, dict) and b.get("type") == "text")
            or (hasattr(b, "type") and b.type == "text")
        )
    else:
        text = str(content)
    if text.strip():
        with st.chat_message(role):
            st.markdown(text)

# Handle quick command injection
if hasattr(st.session_state, "_pending_message") and st.session_state._pending_message:
    pending = st.session_state._pending_message
    st.session_state._pending_message = None
    user_input = pending
else:
    user_input = None

# Chat input
chat_input = st.chat_input(
    "Ask your brain anything…",
    disabled=(st.session_state.server_status != "running"),
)
if chat_input:
    user_input = chat_input

if user_input and st.session_state.server_status == "running":
    with st.chat_message("user"):
        st.markdown(user_input)

    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if isinstance(m["content"], str) or isinstance(m["content"], list)
    ]
    api_messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                reply, updated = run_async(
                    _chat_turn(api_messages, st.session_state.tools)
                )
                st.markdown(reply)
                # Store user + assistant turn
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                err = f"Error: {e}"
                st.error(err)
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.messages.append({"role": "assistant", "content": err})
