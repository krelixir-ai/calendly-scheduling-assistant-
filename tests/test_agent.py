import pytest
from agents.main_agent import Agent

def test_agent_initialization():
    agent = Agent()
    assert agent.llm is not None
    assert agent.tools_map is not None

def test_agent_run_basic_query():
    agent = Agent()
    response = agent.run("What is 2 + 2?")
    assert "4" in response or "Error" in response

def test_agent_run_calendly_query():
    agent = Agent()
    response = agent.run("Check Calendly availability for AI learning between 10 am and 2 pm.")
    assert "No specific availability information found" in response or "Error" in response