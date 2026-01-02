import scrapy
from opensearchpy import OpenSearch

# Connect to local OpenSearch node
client = OpenSearch(hosts=[{"host": "localhost", "port": 9200}])
INDEX = "pages"

# Create index once with a basic mapping (idempotent)
if not client.indices.exists(index=INDEX):
    client.indices.create(
        index=INDEX,
        body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "body": {"type": "text"},
                    "url": {"type": "keyword"},
                }
            }
        },
    )


class SiteSpider(scrapy.Spider):
    name = "site"

    # 🔸 Add seed sites you care about
    start_urls = [
        "https://example.com",
        "https://blog.example.org",
    ]

    def parse(self, response):
        """Index the current page then follow outgoing links."""
        doc = {
            "url": response.url,
            "title": response.css("title::text").get() or response.url,
            "body": " ".join(response.css("p::text").getall())[:2000],
        }
        # upsert using URL as id to avoid duplicates
        client.index(index=INDEX, body=doc, id=response.url, refresh=True)

        # Follow new links
        for href in response.css("a::attr(href)").getall():
            if href.startswith("http"):
                yield scrapy.Request(href, callback=self.parse)
