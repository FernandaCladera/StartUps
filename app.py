import asyncio
from crawl4ai import *
from pydantic import BaseModel, Field


async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://ai.ethz.ch/entrepreneurship/affiliated-startups.html",
        )
        print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())

    # from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    # Create an instance of WebCrawler
    # crawler = AsyncWebCrawler()

    # Warn up the crawler (load necessary models)
    # crawler.warmup()

    # Run the crawler on a URL
    # result= crawler.run(url="https://openai.com/api/pricing/")

    # Print the extracted content
    # print(result.markdown)
