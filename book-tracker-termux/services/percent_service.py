class PercentService:

    @staticmethod
    def calculate_pages(total_pages, percent):

        if total_pages <= 0:
            raise ValueError

        if percent < 0 or percent > 100:
            raise ValueError

        return round(
            total_pages *
            percent / 100
        )
