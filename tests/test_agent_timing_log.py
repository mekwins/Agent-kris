"""
Regression test for the BrainAgent timing-log bug.

Before the fix, src/agent.py kept a module-level `_TIMING_LOG` list that was
never cleared between requests. Because the MCP server process is long-lived
(hourly cron compiles all hit the same process), every tool response dumped
the ENTIRE accumulated timing history since the last process restart — not
just the current call's timing. That list grew unbounded across repeated
calls until the serialized response exceeded a size limit somewhere in the
SSE/HTTP response path and got truncated mid-JSON on the client
(`Expecting value: line 1 column 9841301 (char 9841300)`).

The fix moves `_timing_log` onto the BrainAgent *instance* (set in __init__),
so it is naturally scoped to a single run() call and discarded when that
agent instance goes out of scope — it can never accumulate across requests.

This test does not require any network access or API keys: it only exercises
BrainAgent.__init__ / _log_timing directly, bypassing the AsyncAnthropic
client construction via __new__.
"""
import time
from types import SimpleNamespace

from src.agent import BrainAgent

_FAKE_VAULT = SimpleNamespace(id="test-vault")


def _bare_agent() -> BrainAgent:
    """Construct a BrainAgent without running __init__ (no API client needed)."""
    agent = BrainAgent.__new__(BrainAgent)
    agent.vault = _FAKE_VAULT
    agent._timing_log = []
    return agent


def test_timing_log_is_instance_scoped_not_shared_across_agents():
    agent1 = _bare_agent()
    agent1._log_timing("agent1 step A", time.time())
    agent1._log_timing("agent1 step B", time.time())
    assert len(agent1._timing_log) == 2

    # A second BrainAgent, as would be created for a later, separate tool call
    # in the same long-lived server process.
    agent2 = _bare_agent()
    assert len(agent2._timing_log) == 0, (
        "agent2 inherited timing entries from agent1 — the timing log is not "
        "instance-scoped (regression of the module-global bug)."
    )

    agent2._log_timing("agent2 step C", time.time())
    assert len(agent2._timing_log) == 1

    # agent1's log must remain untouched by agent2's activity.
    assert len(agent1._timing_log) == 2


def test_no_module_level_timing_log_global_exists():
    import src.agent as agent_module

    assert not hasattr(agent_module, "_TIMING_LOG"), (
        "Module-level _TIMING_LOG global has returned — this is the root "
        "cause of the JSON-truncation bug and must stay removed."
    )


def test_log_timing_is_a_bound_method():
    assert hasattr(BrainAgent, "_log_timing"), "_log_timing must be a BrainAgent method"
    agent = _bare_agent()
    # Calling it as an unbound module function should no longer be possible.
    assert callable(agent._log_timing)
