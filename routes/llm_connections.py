from groq import Groq
from openai import OpenAI, AzureOpenAI
import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI
# from langchain_groq import ChatGroq  # Commented out as it might use Portkey
# from portkey_ai import Portkey  # Commented out as it's not to be used
import routes.exceptions as exceptions
from routes.exceptions import RetryableException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import Config
# from portkey_ai import Portkey, PORTKEY_GATEWAY_URL, Portkey, createHeaders  # Commented out as it's not to be used
import json

# Retry configuration
RETRY_WAIT = wait_exponential(multiplier=int(Config.RETRY_MULTIPLIER), min=int(Config.RETRY_MIN), max=int(Config.RETRY_MAX))
RETRY_ATTEMPTS = int(Config.RETRY_ATTEMPTS)

try:
    groq_client = Groq(api_key=os.environ['GROQ_API_KEY'])
    
    openai_client = OpenAI()
    
    azure_openai_client = AzureOpenAI(
        api_key=os.environ['AZURE_OPENAI_API_KEY'],  
        api_version=os.environ['AZURE_OPENAI_API_VERSION'],
        azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
    )
    
    llm_openai = ChatOpenAI(temperature=0.3, model="gpt-4o")
    
    llm_azure_openai = AzureChatOpenAI(azure_deployment=os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'], openai_api_version=os.environ['AZURE_OPENAI_API_VERSION'])

    # Commented out Portkey initialization
    # portkey_openai = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # portkey_groq = Portkey(api_key=str(Config.PORTKEY_GROQ_VIRTUAL_KEY))
    
except Exception as e:
    print(f"Error connecting to client: {e}")
    raise e

@retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=RETRY_WAIT, retry=retry_if_exception_type(RetryableException))
def groq_llm(system_prompt: str, user_prompt: str, **kwargs):
    try:
        # ensure your LLM imports are all within this function
        from groq import Groq
        # from portkey_ai import Portkey  # Commented out as it's not to be used

        # Commented out Portkey initialization
        # portkey = Portkey(api_key=str(Config.PORTKEY_API_KEY), virtual_key=str(Config.PORTKEY_GROQ_VIRTUAL_KEY)) 

        # define your own LLM here
        client = Groq(api_key=os.environ['GROQ_API_KEY'])
        MODEL = 'llama3-70b-8192'

        # Directly use Groq client instead of Portkey
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            **kwargs
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating response from groq: {e}")
        raise RetryableException(e)

@retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=RETRY_WAIT, retry=retry_if_exception_type(RetryableException))
def gpt_llm(system_prompt: str, user_prompt: str, **kwargs):
    try:
        # ensure your LLM imports are all within this function
        import openai

        json_str = json.dumps(kwargs)
        metadata = json.loads(json_str)

        user_id = metadata.get('user_id', 'default')  # Use 'default_user' if user_id is not provided
        project_id = metadata.get('project_id', 'default')  # Use 'default_user' if user_id is not provided
        environment = metadata.get('environment', 'default')  # Use 'default_user' if user_id is not provided

        max_tokens = metadata.get('max_tokens', 4096)  # Use 'default_user' if user_id is not provided
        temperature = metadata.get('temperature', 0.5)  # Use 'default_user' if user_id is not provided

        print(metadata)        

        # define your own LLM here
        client = openai(api_key=os.environ['OPENAI_API_KEY'])

        MODEL = 'gpt-4o'

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response from GPT: {e}")
        raise RetryableException(e)
