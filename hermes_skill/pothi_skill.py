"""
Pothi Parivaar - Standalone Hermes Agent Skill / Tool
Integrates Hermes AI agent with local Pothi Parivaar instance over REST API.
"""

from typing import Optional
import httpx


class PothiParivaarSkill:
    """Hermes Agent Skill to interact with family library."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def get_status(self) -> dict:
        """Get summary of total books, readers, and currently reading sessions."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/v1/hermes/status")
                return res.json()
        except Exception as e:
            return {"error": f"Failed to connect to Pothi Parivaar: {e}"}

    def recommend_books(
        self, reader_name: Optional[str] = None, genre: Optional[str] = None, limit: int = 5
    ) -> dict:
        """Get book recommendations for a reader or topic."""
        try:
            params = {}
            if reader_name:
                params["reader_name"] = reader_name
            if genre:
                params["genre"] = genre
            params["limit"] = limit

            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/v1/hermes/recommend", params=params)
                return res.json()
        except Exception as e:
            return {"error": f"Failed to get recommendations: {e}"}

    def locate_book(self, query: str) -> dict:
        """Find the physical shelf location of a book."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/v1/hermes/locate/{query}")
                return res.json()
        except Exception as e:
            return {"error": f"Failed to locate book: {e}"}

    def search_books(self, query: str) -> dict:
        """Search books by title, author, or keywords."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/v1/books", params={"q": query})
                return {"results": res.json()}
        except Exception as e:
            return {"error": f"Failed to search books: {e}"}

    def add_book(
        self,
        title: str,
        author: str,
        room: Optional[str] = None,
        unit: Optional[str] = None,
        shelf: Optional[str] = None,
        isbn: Optional[str] = None,
        genres_tags: Optional[str] = None,
    ) -> dict:
        """Add a new physical book to the library catalog."""
        try:
            payload = {
                "title": title,
                "author": author,
                "location_room": room,
                "location_unit": unit,
                "location_shelf": shelf,
                "isbn": isbn,
                "genres_tags": genres_tags,
            }
            with httpx.Client(timeout=5.0) as client:
                res = client.post(f"{self.base_url}/api/v1/books", json=payload)
                return res.json()
        except Exception as e:
            return {"error": f"Failed to add book: {e}"}


# Convenience default instance
skill = PothiParivaarSkill()
