

from openai import OpenAI
from utils.credentials import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def search_web(query, location="RW", city="Kigali"):
    try:
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
