import sys
import os
import asyncio
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_mcp_tools():
    # # Load MCP config
    try:
        config_path = os.path.join(project_root, "backend", "config", "mcp_config.json")
        with open(config_path, "r") as f:
            config = json.load(f)["mcpServers"]
    except FileNotFoundError:
        print(f"Error: mcp_config.json not found at {config_path}")
        return []

    # Create client
    client = MultiServerMCPClient(config)

    # Load tools (this starts gmail-mcp automatically)
    tools = await client.get_tools()

    resources = await client.get_resources("gmail-mcp")

    # print("\nConnected MCP Tools:\n")
    # for tool in tools:
    #     print(f"- {tool.name}: {tool.get_input_jsonschema()}")
    print(resources)

    return tools


if __name__ == "__main__":
    asyncio.run(get_mcp_tools())