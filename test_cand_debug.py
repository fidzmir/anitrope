import asyncio
from services.anilist_service import AniListService

async def test():
    anilist = AniListService()

    print("Test 1: Tag query ['Demons']")
    res1 = await anilist._query_graphql(
        """
        query ($type: MediaType, $tag_in: [String]) {
          Page(page: 1, perPage: 5) {
            media(type: $type, tag_in: $tag_in, isAdult: false) {
              id
              title { english romaji }
            }
          }
        }
        """,
        {"type": "ANIME", "tag_in": ["Demons"]}
    )
    print("Res1:", [x.get("title") for x in res1])

    print("\nTest 2: Search query 'The Seven Deadly Sins'")
    res2 = await anilist._query_graphql(
        """
        query ($search: String, $type: MediaType) {
          Page(page: 1, perPage: 5) {
            media(search: $search, type: $type, isAdult: false) {
              id
              title { english romaji }
            }
          }
        }
        """,
        {"search": "The Seven Deadly Sins", "type": "ANIME"}
    )
    print("Res2:", [x.get("title") for x in res2])

    print("\nTest 3: Full fetch_candidates")
    res3 = await anilist.fetch_candidates(
        keywords=["deadly sins"],
        anilist_tags=["Demons", "Super Power"],
        genres=["Fantasy"],
        clean_keyword="The Seven Deadly Sins, Fullmetal Alchemist",
        type_str="anime"
    )
    print("Res3 count:", len(res3))
    print("Res3 titles:", [x.get("title") for x in res3[:5]])

if __name__ == "__main__":
    asyncio.run(test())
