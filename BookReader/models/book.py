from dataclasses import dataclass, field
from typing import Optional

from models.progress import calc_progress
from models.work import Work, WORK_STATUS_READING, WORK_STATUS_SKIPPED


def normalize_url(url: str) -> str:
    text = (url or "").strip()
    if not text:
        return ""
    if not text.startswith(("http://", "https://")):
        text = "https://" + text
    return text


@dataclass
class Book:
    title: str
    author: str
    total_pages: int
    current_page: int = 0
    description: str = ""
    marketplace_url: str = ""
    review: str = ""
    works: list[Work] = field(default_factory=list)

    def __post_init__(self):
        self.title = (self.title or "").strip()
        self.author = (self.author or "").strip()
        self.description = (self.description or "").strip()
        self.marketplace_url = normalize_url(self.marketplace_url)
        self.review = (self.review or "").strip()
        self.total_pages = max(int(self.total_pages), 0)
        self.current_page = max(int(self.current_page), 0)
        if not isinstance(self.works, list):
            self.works = []
        self.works = [work if isinstance(work, Work) else Work.from_dict(work) for work in self.works]
        if self.has_works:
            self.sync_from_works()
        elif self.total_pages > 0:
            self.current_page = min(self.current_page, self.total_pages)

    @property
    def has_works(self) -> bool:
        return len(self.works) > 0

    @property
    def active_works(self) -> list[Work]:
        return [work for work in self.works if work.counts_toward_progress]

    @property
    def allocated_pages(self) -> int:
        return sum(work.total_pages for work in self.works)

    @property
    def effective_total_pages(self) -> int:
        if not self.has_works:
            return self.total_pages
        return sum(work.total_pages for work in self.active_works)

    @property
    def effective_current_page(self) -> int:
        if not self.has_works:
            return self.current_page
        return sum(work.current_page for work in self.active_works)

    @property
    def progress_total_pages(self) -> int:
        if self.total_pages > 0:
            return self.total_pages
        if self.has_works:
            return self.effective_total_pages
        return 0

    @property
    def progress(self) -> float:
        if not self.has_works:
            return calc_progress(self.total_pages, self.current_page)
        total = self.progress_total_pages
        if total <= 0:
            return 0.0
        return calc_progress(total, self.effective_current_page)

    @property
    def is_finished(self) -> bool:
        if self.has_works:
            active = self.active_works
            if not active:
                return False
            return all(work.is_finished for work in active)
        return self.total_pages > 0 and self.progress >= 100

    def sync_from_works(self) -> None:
        if not self.has_works:
            return
        self.current_page = min(self.effective_current_page, self.total_pages)

    def find_reading_work(self) -> Optional[Work]:
        for work in self.works:
            if work.status == WORK_STATUS_READING and not work.is_finished:
                return work
        return None

    def find_next_work(self) -> Optional[Work]:
        reading = self.find_reading_work()
        if reading is not None:
            return reading
        for work in self.works:
            if work.counts_toward_progress and not work.is_finished:
                return work
        return None

    def add_work_page(self, pages: int = 1) -> int:
        if not self.has_works or pages <= 0:
            return 0

        work = self.find_next_work()
        if work is None:
            return 0

        if work.status != WORK_STATUS_READING and work.current_page == 0:
            work.set_status(WORK_STATUS_READING)

        before = work.current_page
        work.current_page = min(work.current_page + pages, work.total_pages)
        if work.current_page >= work.total_pages and work.total_pages > 0:
            work.set_status("finished")
        self.sync_from_works()
        return work.current_page - before

    def validate_works(self) -> None:
        if not self.works:
            return
        if self.allocated_pages > self.total_pages:
            raise ValueError(
                f"Сумма страниц произведений ({self.allocated_pages}) "
                f"не может превышать страниц книги ({self.total_pages})"
            )
        for index, work in enumerate(self.works, start=1):
            if not work.title:
                raise ValueError(f"Укажите название произведения №{index}")
            if work.total_pages <= 0:
                raise ValueError(f"У произведения «{work.title}» должно быть больше 0 страниц")

    def to_dict(self) -> dict:
        payload = {
            "title": self.title,
            "author": self.author,
            "total_pages": self.total_pages,
            "current_page": self.current_page,
            "description": self.description,
            "marketplace_url": self.marketplace_url,
            "review": self.review,
        }
        if self.works:
            payload["works"] = [work.to_dict() for work in self.works]
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        works_data = data.get("works", [])
        works = []
        if isinstance(works_data, list):
            for item in works_data:
                if isinstance(item, dict):
                    try:
                        works.append(Work.from_dict(item))
                    except (TypeError, ValueError):
                        continue
        return cls(
            title=str(data.get("title", "")),
            author=str(data.get("author", "")),
            total_pages=int(data.get("total_pages", 0)),
            current_page=int(data.get("current_page", 0)),
            description=str(data.get("description", "")),
            marketplace_url=str(data.get("marketplace_url", "")),
            review=str(data.get("review", "")),
            works=works,
        )
