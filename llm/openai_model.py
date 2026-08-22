from openai import OpenAI
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def get_client():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_2'))
    return client

def get_llm_model():
    llm_model = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv('OPENAI_API_KEY_2'))
    return llm_model


#embedding function

def generate_embedding(text: str) -> list:
    client = get_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding




def search_web(query, location="RW", city="Kigali"):
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options={
                "user_location": {
                    "type": "approximate",
                    "approximate": {
                        "country": location,
                        "city": city,
                        "region": city
                    }
                },
                "search_context_size": "medium"
            },
            messages=[
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message
    except Exception as e:
        return {"content": f"Web search failed: {e}"}
    

