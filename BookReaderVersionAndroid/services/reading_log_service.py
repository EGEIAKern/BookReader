from datetime import date, timedelta


class ReadingLogService:

    @staticmethod
    def record_pages(log: dict[str, int], pages: int, day: date | None = None) -> None:
        if pages <= 0:
            return

        key = (day or date.today()).isoformat()
        log[key] = log.get(key, 0) + pages

    @staticmethod
    def get_daily_series(
        log: dict[str, int],
        days: int = 14,
        end_day: date | None = None,
    ) -> list[dict]:
        if days <= 0:
            return []

        today = end_day or date.today()
        series = []

        for offset in range(days - 1, -1, -1):
            current = today - timedelta(days=offset)
            key = current.isoformat()
            pages = log.get(key, 0)
            series.append(
                {
                    "date": current,
                    "iso": key,
                    "label": current.strftime("%d.%m"),
                    "pages": pages,
                }
            )

        return series

    @staticmethod
    def total_pages(series: list[dict]) -> int:
        return sum(item["pages"] for item in series)

    @staticmethod
    def average_pages(series: list[dict]) -> float:
        if not series:
            return 0.0
        return round(ReadingLogService.total_pages(series) / len(series), 1)
