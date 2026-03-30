import os
import json
import asyncio
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

# Dynamically resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
CONFIG_PATH = BASE_DIR / "config" / "mcp_config.json"

def get_mcp_client_config():
    """Load and process the MCP servers config."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    servers_config = data.get("mcpServers", {})
    
    # Process environment variables: resolve relative paths correctly 
    # and merge with the OS environment
    for name, config in servers_config.items():
        if config.get("env"):
            env = os.environ.copy()
            for k, v in config["env"].items():
                if isinstance(v, str) and v.startswith("./"):
                    # Make relative paths absolute based on PROJECT_ROOT
                    env[k] = str((PROJECT_ROOT / v[2:]).resolve())
                else:
                    env[k] = v
            config["env"] = env
            
    return servers_config


async def get_multi_mcp_client():
    """Returns an initialized MultiServerMCPClient."""
    config = get_mcp_client_config()
    client = MultiServerMCPClient(config)
    return client


async def get_mcp_tools():
    try:
        config = get_mcp_client_config()
        print(f"Initializing MultiServerMCPClient with {len(config)} servers...")
        
        # Start connection manager block, or use it directly per langchain_mcp_adapters
        # In langchain_mcp_adapters, typically `async with` is used if it handles resources properly.
        # But per the provided template, instantiation then `get_tools()` is used.
        client = MultiServerMCPClient(config)
        # Load tools from all MCP servers
        tools = await client.get_tools()
        
        print(f"\nLoaded {len(tools)} tools")
        # for tool in tools:
        #     print(f"- {tool.name}")
        return tools
    except Exception as e:
        print(f"Error during MCP initialization: {e}")

if __name__ == "__main__":
    asyncio.run(get_mcp_tools())
