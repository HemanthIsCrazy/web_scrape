from scrapy.crawler import CrawlerRunner
from scrapy import signals
from scrapy.signalmanager import dispatcher
from twisted.internet.defer import inlineCallbacks, returnValue, ensureDeferred
from googlesearch import search
from wiki_scrapy_main import KnowledgeSpider
import json
import os

# File handling utilities
JSON_FILE = "scraped_results.json"

def initialize_json_file():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)

def load_existing_data():
    initialize_json_file()
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_to_json(data):
    existing_data = load_existing_data()
    existing_data.append(data)
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

def check_if_topic_exists(topic):
    existing_data = load_existing_data()
    for entry in existing_data:
        if entry.get('topic', '').lower() == topic.lower():
            return entry
    return None

def find_reliable_link(topic):
    reliable_sites = ["wikipedia.org", "britannica.com", "plato.stanford.edu"]
    for site in reliable_sites:
        search_query = f'{topic} site:{site}'
        for url in search(search_query, num_results=5):
            if site in url:
                return url
    return None

@inlineCallbacks
def run_scrapy_for_topics(topics):
    results = []
    runner = CrawlerRunner()

    for topic in topics:
        url = find_reliable_link(topic)
        if not url:
            results.append({'topic': topic, 'error': 'No reliable link found'})
            continue

        scraped_result = {}

        def collect_result(item, response, spider):
            scraped_result.update(item)

        dispatcher.connect(collect_result, signal=signals.item_scraped)

        try:
            yield runner.crawl(KnowledgeSpider, topic=url)
            if scraped_result:
                scraped_result['topic'] = topic
                save_to_json(scraped_result)
                results.append(scraped_result)
            else:
                results.append({'topic': topic, 'error': 'Scraping failed'})
        except Exception as e:
            results.append({'topic': topic, 'error': str(e)})

    returnValue(results)

@inlineCallbacks
def get_info(topics):
    results = []

    for topic in topics:
        cached_entry = check_if_topic_exists(topic)
        if cached_entry:
            results.append(cached_entry)
        else:
            results.append(None)

    topics_to_scrape = [t for t, r in zip(topics, results) if r is None]
    if topics_to_scrape:
        scraped_results = yield run_scrapy_for_topics(topics_to_scrape)
        for topic, result in zip(topics_to_scrape, scraped_results):
            results[topics.index(topic)] = result

    returnValue(results)

async def scrape_topic(topic):
    return await ensureDeferred(get_info([topic]))
