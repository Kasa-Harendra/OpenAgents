import json
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.model_providers.models import AgentConfig
from backend.agents.model_providers.llm_providers import provide_llm

# load_dotenv("../../.env")

config_path = os.environ.get('AGENT_CONFIG_PATH', '../../config/agents_config.json')
if not os.path.exists(config_path):
    # Try relative to the current file if absolute/cwd path fails
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'agents_config.json'))

with open(config_path, 'r') as f:
    config = json.load(fp=f)

config = config['agents']

agent_configs = {}

for agent in config:
    agent_configs[agent] = AgentConfig(
        agent_name=agent,
        type=config[agent]['type'],
        provider=config[agent]['llm_provider'],
        model_name=config[agent]['llm_config']['model'],
        apiKey=config[agent]['llm_config']['api_key'],
        base_url=config[agent]['llm_config']['base_url']
    )


# pprint.pprint(agent_configs)

agent_llms = {}
for agent in config:
    agent_llms[agent] = provide_llm(agent_configs[agent])
