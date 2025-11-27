import pytest
from legion.agents.ci_healer_agent import CIHealerAgent

def test_agent_initialization():
    agent = CIHealerAgent()
    assert agent is not None

def test_run_dry():
    agent = CIHealerAgent(dry_run=True)
    payload = {
        "workflow_run": {"conclusion": "failure"},
        "repository": {"full_name": "legion14041981-ui/Legion"}
    }
    result = agent.handle_webhook(payload)
    assert result is not None
    assert hasattr(result, "success")
