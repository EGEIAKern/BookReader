from dataclasses import dataclass


def calc_progress(total_pages: int, current_page: int) -> float:
    if total_pages <= 0:
        return 0.0
    current_page = min(max(current_page, 0), total_pages)
    return round(current_page / total_pages * 100, 1)


@dataclass
class Book:
    title: str
    author: str
    total_pages: int
    current_page: int = 0

    def __post_init__(self):
        self.title = (self.title or "").strip()
        self.author = (self.author or "").strip()
        self.total_pages = max(int(self.total_pages), 0)
        self.current_page = max(int(self.current_page), 0)
        if self.total_pages > 0:
            self.current_page = min(self.current_page, self.total_pages)

    @property
    def progress(self) -> float:
        return calc_progress(self.total_pages, self.current_page)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "total_pages": self.total_pages,
            "current_page": self.current_page,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        return cls(
            title=str(data.get("title", "")),
            author=str(data.get("author", "")),
            total_pages=int(data.get("total_pages", 0)),
            current_page=int(data.get("current_page", 0)),
        )
