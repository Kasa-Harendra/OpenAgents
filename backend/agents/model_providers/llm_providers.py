from langchain.chat_models import BaseChatModel 
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

from .models import AgentConfig

load_dotenv('../.env')

def provide_llm(
    config: AgentConfig
) -> BaseChatModel:
    model_name = config.model_name
    apikey = config.api_key
    base_url = config.base_url if config.base_url != "" else None

    model = None
    match(config.type):
        case "chat":
            match(config.provider):
                case "anthropic":
                    model = ChatAnthropic(
                        model_name=model_name, 
                        anthropic_api_key=apikey,
                        **({"anthropic_api_url": base_url} if base_url else {}),
                        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
                    )
                case "openai":
                    model = ChatOpenAI(
                        model=model_name,
                        api_key=apikey,
                        **({"base_url": base_url} if base_url else {})
                    )
                case "gemini":
                    model = ChatGoogleGenerativeAI(
                        model=model_name, 
                        api_key=apikey,
                    )
                case "ollama":
                    model = ChatOllama(
                        model=model_name,
                        **({"base_url": base_url} if base_url else {})
                    )
                case "groq":
                    model = ChatGroq(
                        model=model_name,
                        api_key=apikey,
                        **({"base_url": base_url} if base_url else {}) 
                    )
                case _:
                    model = ChatOpenAI(
                        model=model_name,
                        api_key=apikey,
                        **({"base_url": base_url} if base_url else {})
                    )
        case "embed":
            match(config.provider):
                case "openai":
                    model = OpenAIEmbeddings(
                        model=model_name,
                        api_key=apikey,
                        **({"base_url": base_url} if base_url else {})
                    )
                case "gemini":
                    model = GoogleGenerativeAIEmbeddings(
                        model=model_name, 
                        api_key=apikey,
                    )
                case "ollama":
                    model = OllamaEmbeddings(
                        model=model_name,
                        base_url=base_url,
                    )
                case _:
                    model = OpenAIEmbeddings(
                        model=model_name,
                        base_url=base_url,
                        api_key=apikey
                    )
    return model