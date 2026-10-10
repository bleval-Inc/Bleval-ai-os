from pathlib import Path

from axiom import config


def test_config_paths_point_to_agent_system_when_present():
    assert config.workflows_path() == config.REPO_ROOT / "agent_system" / "workflows"
    assert (config.workflows_path() / "workflow-index.yaml").exists()

    assert config.agents_path() == config.REPO_ROOT / "agent_system" / "agents"
    assert config.organizations_path() == config.REPO_ROOT / "agent_system" / "organizations"
