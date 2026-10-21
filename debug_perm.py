import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from axiom.engine.tool import ToolEngine
from axiom.registry.agent import AgentRegistryLoader

tool = ToolEngine()
agent_loader = AgentRegistryLoader()
detail = agent_loader.load_detail("axiom")
print("Detail:", detail)
if detail:
    print("Can:", detail.permissions.can)
    print("Cannot:", detail.permissions.cannot)
    # test permission
    from axiom.engine.tool import ToolEngine
    te = ToolEngine()
    perm = te.check_permission("axiom", "search")
    print("Permission for search:", perm)
    perm2 = te.check_permission("axiom", "web_search")
    print("Permission for web_search:", perm2)
    perm3 = te.check_permission("axiom", "research")
    print("Permission for research:", perm3)
else:
    print("Agent not found")