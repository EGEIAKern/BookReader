import math


class GoalService:

    @staticmethod
    def pages_per_day(pages_left, days_left):

        if days_left <= 0:
            raise ValueError

        return math.ceil(
            pages_left /
            days_left
        )