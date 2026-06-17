def calc_progress(total_pages: int, current_page: int) -> float:
    if total_pages <= 0:
        return 0.0
    current_page = min(max(current_page, 0), total_pages)
    return round(current_page / total_pages * 100, 1)
