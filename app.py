from fastapi import FastAPI, HTTPException
from googlesearch import search
from pydantic import BaseModel
import subprocess
import json

app = FastAPI()

class SearchRequest(BaseModel):
    topic: str

def find_reliable_link(topic):
    reliable_sites = ["wikipedia.org", "britannica.com", "plato.stanford.edu"]
    for site in reliable_sites:
        search_query = f'{topic} site:{site}'
        for url in search(search_query, num_results=5):
            if site in url:
                return url
    return None

@app.post("/scrape-topic/")
async def search_google(request: SearchRequest):
    try:
        topic = request.topic
        url = find_reliable_link(topic)
        print(url)
        
        if not url:
            raise HTTPException(status_code=404, detail="No reliable URL found.")
        
        process = subprocess.Popen(
            ["python", "wiki_scrapy_main.py", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=stderr.decode("utf-8"))
        
        with open("scraped_results.json", "r") as file:
            scraped_data = json.load(file)
        
        return {"scraped_data": scraped_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
