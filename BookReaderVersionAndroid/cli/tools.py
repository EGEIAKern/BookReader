from services.calculator_service import CalculatorService
from services.goal_service import GoalService
from services.percent_service import PercentService
from services.reading_service import ReadingService

from cli.display import (
    ask_float,
    ask_int,
    clear_screen,
    horizontal_bar,
    pause,
    print_error,
    print_header,
    print_success,
)


class ToolsScreen:

    def run(self) -> None:
        options = [
            "📖 Прогресс чтения",
            "🎯 План чтения",
            "📊 Страницы по %",
            "🧮 Калькулятор",
        ]
        while True:
            clear_screen()
            print_header("🛠 Инструменты")
            for index, label in enumerate(options, start=1):
                print(f"  {index}. {label}")
            print("  0. Назад")

            choice = ask_int("\nПункт", min_value=0, max_value=len(options))
            if choice is None:
                continue
            if choice == 0:
                return
            if choice == 1:
                self._reading_progress()
            elif choice == 2:
                self._reading_goal()
            elif choice == 3:
                self._percent_pages()
            elif choice == 4:
                self._calculator()

    def _reading_progress(self) -> None:
        clear_screen()
        print_header("📖 Прогресс чтения")
        total = ask_int("Всего страниц в книге", min_value=1)
        if total is None:
            pause()
            return
        current = ask_int("Уже прочитано", min_value=0, max_value=total)
        if current is None:
            pause()
            return
        try:
            percent = ReadingService.calculate_progress(total, current)
        except ValueError as error:
            print_error(str(error))
            pause()
            return

        print_success(f"{percent}% прочитано")
        print(f"  {horizontal_bar(percent, 100, width=30)}")
        pause()

    def _reading_goal(self) -> None:
        clear_screen()
        print_header("🎯 План чтения")
        pages_left = ask_int("Осталось страниц", min_value=0)
        if pages_left is None:
            pause()
            return
        days_left = ask_int("Дней до дедлайна", min_value=1)
        if days_left is None:
            pause()
            return
        try:
            per_day = GoalService.pages_per_day(pages_left, days_left)
        except ValueError:
            print_error("Количество дней должно быть больше 0")
            pause()
            return

        print_success(f"Нужно читать {per_day} стр./день")
        pause()

    def _percent_pages(self) -> None:
        clear_screen()
        print_header("📊 Страницы по проценту")
        total = ask_int("Всего страниц в книге", min_value=1)
        if total is None:
            pause()
            return
        percent = ask_float("Процент (0–100)")
        if percent is None:
            pause()
            return
        try:
            pages = PercentService.calculate_pages(total, percent)
        except ValueError:
            print_error("Страниц > 0, процент от 0 до 100")
            pause()
            return

        print_success(f"Это {pages} страниц")
        pause()

    def _calculator(self) -> None:
        clear_screen()
        print_header("🧮 Калькулятор")
        v1 = ask_float("Первое число")
        if v1 is None:
            pause()
            return
        v2 = ask_float("Второе число")
        if v2 is None:
            pause()
            return
        op = input("Операция (+, -, *, /): ").strip()
        if op not in {"+", "-", "*", "/"}:
            print_error("Неизвестная операция")
            pause()
            return
        try:
            result = CalculatorService.calculate(v1, v2, op)
        except ZeroDivisionError:
            print_error("Деление на ноль невозможно")
            pause()
            return
        except ValueError as error:
            print_error(str(error))
            pause()
            return

        print_success(f"= {result:g}")
        pause()
