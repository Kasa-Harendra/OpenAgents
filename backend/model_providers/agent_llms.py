import json
from dotenv import load_dotenv
import pprint
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.model_providers.models import AgentConfig
from backend.model_providers.llm_providers import provide_llm

load_dotenv("../.env")
load_dotenv("./.env")

with open(os.environ['AGENT_CONFIG_PATH'], 'r') as f:
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
