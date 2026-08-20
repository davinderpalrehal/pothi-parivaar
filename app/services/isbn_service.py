from typing import Optional
import httpx


async def lookup_isbn(isbn_code: str) -> Optional[dict]:
    """
    Look up book metadata by ISBN using Open Library API.
    Returns normalized book dictionary or None if not found/error.
    """
    clean_isbn = "".join(filter(str.isalnum, isbn_code.strip()))
    if not clean_isbn:
        return None

    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&jscmd=data&format=json"

    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return None

            data = response.json()
            key = f"ISBN:{clean_isbn}"
            if key not in data:
                return None

            book_info = data[key]

            # Extract authors
            authors = book_info.get("authors", [])
            author_str = ", ".join(a.get("name", "") for a in authors if "name" in a) or "Unknown Author"

            # Extract publication year
            pub_date = book_info.get("publish_date", "")
            pub_year = None
            if pub_date:
                # Find 4 consecutive digits
                import re
                year_match = re.search(r"\b(19\d\d|20\d\d)\b", pub_date)
                if year_match:
                    pub_year = int(year_match.group(1))

            # Cover URL
            cover_data = book_info.get("cover", {})
            cover_url = cover_data.get("large") or cover_data.get("medium") or cover_data.get("small")

            # Page count
            page_count = book_info.get("number_of_pages")

            # Subjects / Genres
            subjects = book_info.get("subjects", [])
            genres = [s.get("name") for s in subjects if isinstance(s, dict) and "name" in s][:5]
            genres_tags = ", ".join(genres) if genres else None

            # Summary / Description
            summary = None
            if "description" in book_info:
                desc = book_info["description"]
                summary = desc if isinstance(desc, str) else desc.get("value")

            return {
                "title": book_info.get("title", ""),
                "author": author_str,
                "publication_year": pub_year,
                "isbn": clean_isbn,
                "summary": summary,
                "cover_url": cover_url,
                "page_count": page_count,
                "genres_tags": genres_tags,
                "formats": "physical",
            }
        except Exception:
            return None
