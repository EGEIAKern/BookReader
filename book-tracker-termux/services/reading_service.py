from models.book import calc_progress


class ReadingService:

    @staticmethod
    def calculate_progress(total_pages, current_pages):
        if total_pages <= 0:
            raise ValueError("total_pages must be positive")
        return calc_progress(total_pages, current_pages)
