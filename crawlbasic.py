import asyncio
import json
import base64
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    CacheMode,
    AdaptiveCrawler,
    AdaptiveConfig,
    AsyncUrlSeeder,
    SeedingConfig,
    c4a_compile,
    CompilationResult,
    CrawlResult,
)
from crawl4ai.proxy_strategy import ProxyConfig
from crawl4ai import RoundRobinProxyStrategy
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai import LLMConfig
from crawl4ai import PruningContentFilter
from crawl4ai import DefaultMarkdownGenerator
from crawl4ai import DefaultMarkdownGenerator
from crawl4ai import BFSDeepCrawlStrategy, DomainFilter, FilterChain


__cur_dir__ = Path(__file__).parent
load_dotenv()

## SIMPLE CRAWL


async def demo_basic_crawl():
    """Basic web crawling with markdown generation"""
    print("(\n=== 1. Basic Web Crawling ===)")

    async with AsyncWebCrawler() as crawler:
        results: list[CrawlResult] = await crawler.arun(
            url="https://news.ycombinator.com/"
        )
        for i, result in enumerate(results):
            print(f"Result {i + 1}:")
            print(f"Success: {result.success}")
            if result.success:
                print(f"Markdown length: {len(result.markdown.raw_markdown)} chars")
                print(f"First 100 chars: {result.markdown.raw_markdown[:100]}...")
            else:
                print("Failed to crawl the URL.")


# if __name__ == "__main__":
#    asyncio.run(demo_basic_crawl())


## PARALLEL CRAWL
async def demo_parallel_crawl():
    """Crawl multiple URLs in parallel"""
    print("\n=== 2. Parallel Crawling ===")

    urls = [
        "https://news.ycombinator.com/",
        "https://example.com/",
    ]

    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun_many(
            urls=urls,
        )

        print(f"Crawled {len(results)} URLs in parallel:")
        for i, result in enumerate(results):
            print(f" {i + 1}.{result.url}- {'Success' if result.success else 'Failed'}")


# if __name__ == "__main__":
#    asyncio.run(demo_parallel_crawl())


## FIT MARKDOWN
## There are different strategies for generating markdown.
## 1)  Main/ Default: It has the content filter which is filtering noises. Here there are 2 algorithms:
#### Prunning Content Filter Algorithm: It shakes the html tree and some loosely elements just go away.
#### BM25: You can pass a query -> imagine creating an research agent. The mkdown would have just relevant for that query.
##### Generate less markdown for large language model.


async def demo_fit_markdown():
    """Generate focused markdown with LLM content filter"""
    print("\n === 3. Fit Markdown with LLM Content Filter ===")
    async with AsyncWebCrawler() as crawler:
        result: CrawlResult = await crawler.arun(
            url="https://en.wikipedia.org/wiki/Python_(programmin_language)",
            config=CrawlerRunConfig(
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter()
                )
            ),
        )
        print(f"Raw: {len(result.markdown.raw_markdown)} chars")
        print(f"Fit: {len(result.markdown.fit_markdown)} chars")


# if __name__ == "__main__":
#    asyncio.run(demo_fit_markdown())

## LINKS AND MEDIA


async def demo_media_and_links():
    """Extract media and links from a page"""
    print("\n === 3. Media and Links Extraction ===")

    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun(
            "https://en.wikipedia.org/wiki/Main_Page"
        )

        for i, result in enumerate(result):
            # Extract and save all image
            images = result.media.get("images", [])
            print(f"Found {len(images)} images")

            # Extract and save all links (internal and external)
            internal_links = result.links.get("internal", [])
            external_links = result.links.get("external", [])
            print(f"Found {len(internal_links)} internal links")
            print(f"Found {len(external_links)} external links")

            # Print some of the images and links
            for image in images[:3]:
                print(f"Image: {image['scr']}")
            for link in internal_links[:3]:
                print(f"Internal link: {link['href']}")
            for link in external_links[:3]:
                print(f"External link: {link['href']}")

            # Save everything to files
            # with open("images.json", "w") as f:
            #     json.dump(images, f, indent=2)

            # with open("links.json", "w") as f:
            #     json.dump(
            #         {"internal": internal_links, "external": external_links},
            #         f,
            #         indent=2,
            #     )


# if __name__ == "__main__":
#     asyncio.run(demo_media_and_links())


## SCREENSHOT AND PDF


async def demo_screenshot_and_pdf():
    """Capture screenshot and PDF of a page"""
    print("\n=== 4. Screenshot and PDF capture ===")

    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun(
            url="https://en.wikipedia.org/wiki/Giant_anteater",
            config=CrawlerRunConfig(screenshot=True, pdf=True),
        )

        for i, result in enumerate(result):
            if result.screenshot:
                # Save screenshot
                screenshot_path = f"{__cur_dir__}/tmp/example_screenshot.png"
                with open(screenshot_path, "wb") as f:
                    f.write(base64.b64decode(result.screenshot))
                print(f"Screenshot saved to {screenshot_path}")

            if result.pdf:
                # Save PDF
                pdf_path = f"{__cur_dir__}/tmp/example.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(result.pdf)
                print(f"PDF saved to {pdf_path}")


# if __name__ == "__main__":
#     asyncio.run(demo_screenshot_and_pdf())


## LLM STRUCTURE DATA NO SCHEMA
async def demo_llm_structured_extraction_no_schema():
    # Create a simple LLM extraction strategy (no schema required)
    extraction_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token="env:OPENAI_API_KEY",
        ),
        instruction="This is news.ycombinator.com, extract all new for each I want title, source url, number of comments",
        extract_type="schema",
        schema="{title:string, url:string, comments:int}",
        extra_args={
            "temperature": 0.0,
            "max_tokens": 4096,
        },
        verbose=True,
    )
    config = CrawlerRunConfig(extraction_strategy=extraction_strategy)
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            "https://news.ycombinator.com/", config=config
        )

        for result in results:
            print(f"URL: {result.url}")
            print(f"Success: {result.success}")
            if result.success:
                data = json.loads(result.extracted_content)
                print(json.dumps(data, indent=2))
            else:
                print("Failed to extract structured data")


# if __name__ == "__main__":
#    asyncio.run(demo_llm_structured_extraction_no_schema())
