from langchain_google_community.gmail.utils import (
    build_resource_service,
    get_google_credentials
)
from googleapiclient.discovery import build
from langchain_google_community import GmailToolkit
from langchain_google_community import CalendarToolkit
from langchain_community.agent_toolkits.nasa.toolkit import NasaToolkit
from langchain_community.utilities.nasa import NasaAPIWrapper
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools import YouTubeSearchTool

def get_google_tools():
    credentials = get_google_credentials(
        token_file="backend/credentials/token.json",
        scopes=["https://mail.google.com/", "https://www.googleapis.com/auth/calendar"],
        client_secrets_file="backend/credentials/credentials.json",
    )
    api_resource = build_resource_service(credentials=credentials)


    gmail_toolkit = GmailToolkit(api_resource=api_resource)
    gmail_tools = gmail_toolkit.get_tools()

    calendar_resource = build("calendar", "v3", credentials=credentials)
    calendar_toolkit = CalendarToolkit(api_resource=calendar_resource)
    calendar_tools = calendar_toolkit.get_tools()

    return gmail_tools + calendar_tools

nasa_wrapper = NasaAPIWrapper()
nasa_toolkit = NasaToolkit.from_nasa_api_wrapper(nasa_wrapper)
nasa_tools = nasa_toolkit.get_tools()

youtube_tools = [YouTubeSearchTool()]

arxiv_tools = [ArxivQueryRun()]

def get_tools():
    return get_google_tools() + youtube_tools + arxiv_tools

# print(get_tools())
