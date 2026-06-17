from dataclasses import dataclass

from models.progress import calc_progress


WORK_STATUS_PLANNED = "planned"
WORK_STATUS_READING = "reading"
WORK_STATUS_FINISHED = "finished"
WORK_STATUS_SKIPPED = "skipped"

WORK_STATUSES = (
    WORK_STATUS_PLANNED,
    WORK_STATUS_READING,
    WORK_STATUS_FINISHED,
    WORK_STATUS_SKIPPED,
)

WORK_STATUS_LABELS = {
    WORK_STATUS_PLANNED: "Буду читать",
    WORK_STATUS_READING: "Читаю",
    WORK_STATUS_FINISHED: "Прочитано",
    WORK_STATUS_SKIPPED: "Не буду читать",
}


def normalize_work_status(status: str) -> str:
    text = (status or "").strip().lower()
    if text in WORK_STATUSES:
        return text
    return WORK_STATUS_PLANNED


@dataclass
class Work:
    title: str
    total_pages: int
    current_page: int = 0
    status: str = WORK_STATUS_PLANNED

    def __post_init__(self):
        self.title = (self.title or "").strip()
        self.total_pages = max(int(self.total_pages), 0)
        self.current_page = max(int(self.current_page), 0)
        self.status = normalize_work_status(self.status)
        if self.total_pages > 0:
            self.current_page = min(self.current_page, self.total_pages)
        if self.status == WORK_STATUS_FINISHED and self.total_pages > 0:
            self.current_page = self.total_pages
        if self.status == WORK_STATUS_SKIPPED:
            self.current_page = 0

    @property
    def counts_toward_progress(self) -> bool:
        return self.status != WORK_STATUS_SKIPPED

    @property
    def progress(self) -> float:
        if not self.counts_toward_progress:
            return 0.0
        return calc_progress(self.total_pages, self.current_page)

    @property
    def is_finished(self) -> bool:
        if self.status == WORK_STATUS_SKIPPED:
            return False
        if self.status == WORK_STATUS_FINISHED:
            return True
        return self.total_pages > 0 and self.current_page >= self.total_pages

    def set_status(self, status: str) -> None:
        self.status = normalize_work_status(status)
        if self.status == WORK_STATUS_FINISHED and self.total_pages > 0:
            self.current_page = self.total_pages
        elif self.status == WORK_STATUS_SKIPPED:
            self.current_page = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "total_pages": self.total_pages,
            "current_page": self.current_page,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Work":
        return cls(
            title=str(data.get("title", "")),
            total_pages=int(data.get("total_pages", 0)),
            current_page=int(data.get("current_page", 0)),
            status=str(data.get("status", WORK_STATUS_PLANNED)),
        )
