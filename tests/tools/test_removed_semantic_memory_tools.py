from nanobot.agent.tools.context import ToolContext
from nanobot.agent.tools.loader import ToolLoader
from nanobot.agent.tools.registry import ToolRegistry


def test_removed_semantic_memory_tools_are_not_registered():
    registry = ToolRegistry()
    ToolLoader().load(ToolContext(config=None, workspace="/tmp"), registry)
    names = set(registry.tool_names)
    removed_prefix = "open" + "viking_"
    removed_memory_tool = "user_memory" + "_search"

    assert removed_memory_tool not in names
    assert not any(name.startswith(removed_prefix) for name in names)
