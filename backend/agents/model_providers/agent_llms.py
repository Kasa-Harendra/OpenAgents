import json
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from backend.agents.model_providers.models import AgentConfig
from backend.agents.model_providers.llm_providers import provide_llm
from backend.db.database import get_db, SessionLocal
from backend.models.models import AgentConfig as DBAgentConfig

# Cache for agent configurations
_agent_configs = {}
# Cache for agent LLMs
_agent_llms = {}

def load_agent_llms():
    """Load or reload agent LLM configurations and instances from the database."""
    global _agent_llms, _agent_configs
    db = SessionLocal()
    try:
        db_configs = db.query(DBAgentConfig).all()
        
        new_agent_llms = {}
        new_agent_configs = {}
        
        for config in db_configs:
            # Check if config is actually set
            llm_config = config.llm_config or {}
            model_name = llm_config.get('model')
            
            if not model_name or config.llm_provider.lower() == 'none':
                # Skip unconfigured agents
                continue
                
            agent_config = AgentConfig(
                agent_name=config.agent_name,
                type=config.agent_type,
                provider=config.llm_provider,
                model_name=model_name,
                apiKey=llm_config.get('api_key'),
                base_url=llm_config.get('base_url')
            )
            
            new_agent_configs[config.agent_name] = agent_config
            
            try:
                new_agent_llms[config.agent_name] = provide_llm(agent_config)
            except Exception as e:
                print(f"Error providing LLM for {config.agent_name}: {e}")
        
        _agent_llms = new_agent_llms
        _agent_configs = new_agent_configs
        return _agent_llms
    except Exception as e:
        print(f"Error loading agent LLMs: {e}")
        return _agent_llms
    finally:
        db.close()

def get_agent_llm(agent_name: str):
    """Get the LLM instance for a specific agent, reloading if not found."""
    global _agent_llms
    if agent_name not in _agent_llms:
        load_agent_llms()
    return _agent_llms.get(agent_name)

def get_agent_config(agent_name: str):
    """Get the AgentConfig object for a specific agent, reloading if not found."""
    global _agent_configs
    if agent_name not in _agent_configs:
        load_agent_llms()
    return _agent_configs.get(agent_name)

# initial load
agent_llms = load_agent_llms()
# for backward compatibility where it was used as a dict
agent_configs = _agent_configs
