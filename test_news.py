import asyncio
from services.news_service import NewsService

async def test():
    service = NewsService()
    news = await service.fetch_latest_news()
    print("Fetched News Items Count:", len(news))
    print("\nTop News Items:")
    for n in news[:6]:
        title = n['title'].encode('ascii', 'ignore').decode('ascii')
        print(f"- [{n['source']}] {title} | Img: {bool(n.get('image_url'))}")
        print(f"  Link: {n['link']}")

if __name__ == "__main__":
    asyncio.run(test())
