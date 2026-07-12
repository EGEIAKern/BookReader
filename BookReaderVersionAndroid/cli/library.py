from pathlib import Path

from models.book import Book, normalize_url
from models.work import WORK_STATUS_LABELS, WORK_STATUSES, Work
from services.export_service import export_books_to_csv, export_books_to_excel
from services.reading_log_service import ReadingLogService
from storage.storage import save_books

from cli.display import (
    ask_int,
    ask_text,
    ask_yes_no,
    clear_screen,
    horizontal_bar,
    pause,
    print_error,
    print_form_step,
    print_header,
    print_hint,
    print_key_value,
    print_section,
    print_shortcuts,
    print_success,
    progress_bar,
)


class LibraryScreen:
    def __init__(self, books: list[Book], reading_log: dict[str, int]):
        self.books = books
        self.reading_log = reading_log

    def run(self) -> None:
        while True:
            clear_screen()
            print_header(f"📚 Библиотека ({len(self.books)} книг)")
            self._list_books()
            choice = input(
                "\n[a] добавить [n] номер книги [s] поиск [e] экспорт [0] назад\n> "
            ).strip().lower()

            if choice in {"0", "q", "назад"}:
                return
            if choice in {"a", "д", "add"}:
                self._add_book()
                continue
            if choice in {"s", "п", "search"}:
                self._search()
                continue
            if choice in {"e", "э", "export"}:
                self._export()
                continue
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(self.books):
                    self._book_menu(index)
                else:
                    print_error("Неверный номер")
                pause()
                continue
            print_error("Неизвестная команда")
            pause()

    def _format_pages(self, book: Book) -> str:
        if book.has_works:
            text = f"{book.effective_current_page}/{book.progress_total_pages} стр."
            if book.total_pages > 0 and book.allocated_pages != book.total_pages:
                text += f" · произведения: {book.allocated_pages} стр."
            return text
        return f"{book.current_page}/{book.total_pages} стр."

    def _list_books(self, items: list[tuple[int, Book]] | None = None) -> None:
        rows = items if items is not None else list(enumerate(self.books))
        if not rows:
            print("\n Список пуст. Добавьте первую книгу.")
            return
        print()
        for display_index, (book_index, book) in enumerate(rows, start=1):
            author = book.author or "автор не указан"
            status = "✓" if book.is_finished else " "
            print(
                f" {display_index:>2}. [{status}] {book.title}\n"
                f" {author} · {self._format_pages(book)} ({book.progress}%)\n"
                f" {progress_bar(book.progress)}"
            )
            if book.has_works:
                finished = sum(1 for work in book.active_works if work.is_finished)
                total_active = len(book.active_works)
                print(f" 📖 Произведения: {finished}/{total_active} прочитано")
            for work in book.works:
                status_label = WORK_STATUS_LABELS.get(work.status, work.status)
                if work.counts_toward_progress:
                    pages = f"{work.current_page}/{work.total_pages} стр."
                else:
                    pages = f"{work.total_pages} стр."
                print(f" • {work.title} — {pages} · {status_label}")

    def _search(self) -> None:
        query = ask_text("\nПоиск (название или автор)")
        if query is None:
            return
        query = query.lower()
        found = [
            (index, book)
            for index, book in enumerate(self.books)
            if query in book.title.lower() or query in book.author.lower()
        ]
        clear_screen()
        print_header("🔍 Результаты поиска")
        self._list_books(found)
        pause()

    def _add_book(self) -> None:
        try:
            book = self._prompt_new_book_wizard()
        except ValueError as error:
            print_error(str(error))
            pause()
            return
        if book is None:
            pause()
            return
        if book.effective_current_page > 0:
            ReadingLogService.record_pages(self.reading_log, book.effective_current_page)
        self.books.append(book)
        self._save()
        print_success(f"«{book.title}» добавлена в библиотеку")
        self._prompt_review_if_completed(len(self.books) - 1, was_finished=False)
        pause()

    def _book_menu(self, index: int) -> None:
        book = self.books[index]
        while True:
            clear_screen()
            print_header(f"📖 {book.title}")
            author = book.author or "автор не указан"
            print(f"\n Автор: {author}")
            if book.description:
                print(f" Описание: {book.description}")
            if book.marketplace_url:
                print(f" Ссылка: {book.marketplace_url}")
            if book.review:
                print(f" Мнение: {book.review}")
            print(f" Прогресс: {self._format_pages(book)} ({book.progress}%)")
            print(f" {progress_bar(book.progress)}")
            if book.has_works:
                print("\n Произведения:")
                for work_index, work in enumerate(book.works, start=1):
                    status_label = WORK_STATUS_LABELS.get(work.status, work.status)
                    if work.counts_toward_progress:
                        pages = f"{work.current_page}/{work.total_pages} стр."
                    else:
                        pages = f"{work.total_pages} стр."
                    print(f" {work_index}. {work.title} — {pages} · {status_label}")
            choice = input(
                "\n[+] +1 стр. [p] прогресс [w] произведения "
                "[e] изменить [d] удалить [0] назад\n> "
            ).strip().lower()
            if choice in {"0", "q"}:
                return
            if choice in {"+", "п", "plus"}:
                self._add_page(index)
            elif choice in {"p", "пр"}:
                self._set_page(index)
            elif choice in {"w", "ц", "works"}:
                self._manage_works(index)
            elif choice in {"e", "и"}:
                self._edit_book(index)
            elif choice in {"d", "у"}:
                self._delete_book(index)
            else:
                print_error("Неизвестная команда")
                pause()

    def _add_page(self, index: int) -> None:
        book = self.books[index]
        was_finished = book.is_finished
        old_page = book.effective_current_page
        if book.has_works:
            added = book.add_work_page(1)
            if added <= 0:
                print_error("Нет незавершённых произведений для добавления страницы")
                pause()
                return
            ReadingLogService.record_pages(self.reading_log, added)
            self._save()
            print_success(f"Прогресс: {self._format_pages(book)} ({book.progress}%)")
            self._prompt_review_if_completed(index, was_finished)
            pause()
            return
        if book.current_page >= book.total_pages:
            print_error("Книга уже прочитана")
            pause()
            return
        book.current_page += 1
        ReadingLogService.record_pages(self.reading_log, 1)
        self._save()
        print_success(f"Страница {book.current_page}/{book.total_pages}")
        self._prompt_review_if_completed(index, was_finished)
        pause()

    def _set_page(self, index: int) -> None:
        """✅ ИСПРАВЛЕНИЕ ОШИБКИ 1: Теперь работает для книг с произведениями"""
        book = self.books[index]
        was_finished = book.is_finished
        
        # ✅ ИСПРАВЛЕНИЕ: Для книг с произведениями предлагаем выбор
        if book.has_works:
            self._set_page_for_works(index)
            return
        
        # Для обычных книг
        page = ask_int(
            f"До какой страницы прочитали (0–{book.total_pages})",
            min_value=0,
            max_value=book.total_pages,
        )
        if page is None:
            pause()
            return
        
        old_page = book.current_page
        
        # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 2: Проверяем уменьшение прогресса
        if page < old_page:
            print_error(f"Нельзя уменьшить прогресс (было {old_page})")
            pause()
            return
        
        book.current_page = page
        delta = book.current_page - old_page
        
        # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 2: Всегда сохраняем изменения
        if delta > 0:
            ReadingLogService.record_pages(self.reading_log, delta)
            print_success(f"Добавлено {delta} стр. Прогресс: {book.progress}%")
        else:
            print_success(f"Прогресс: {book.progress}%")
        
        self._save()
        self._prompt_review_if_completed(index, was_finished)
        pause()

    def _set_page_for_works(self, index: int) -> None:
        """✅ НОВЫЙ МЕТОД: Задать страницу для книги с произведениями"""
        book = self.books[index]
        was_finished = book.is_finished
        
        while True:
            clear_screen()
            print_header(f"📖 Задать страницу — {book.title}")
            print(f"\n Текущий прогресс: {self._format_pages(book)} ({book.progress}%)")
            print(f" {progress_bar(book.progress)}")
            
            print("\n Выберите способ:")
            print("  0. Задать общую страницу для всей книги")
            for work_index, work in enumerate(book.works, start=1):
                status_label = WORK_STATUS_LABELS.get(work.status, work.status)
                if work.counts_toward_progress:
                    pages = f"{work.current_page}/{work.total_pages} стр."
                else:
                    pages = f"{work.total_pages} стр."
                print(f" {work_index}. {work.title} — {pages} · {status_label}")
            print(" [0] Назад")
            
            choice = input("\n Ваш выбор: ").strip()
            
            if choice in {"0", "q", "назад"}:
                return
            
            if choice.isdigit():
                work_index = int(choice) - 1
                if work_index == -1:
                    # Задать общую страницу для всей книги
                    self._set_page_for_whole_book(index)
                    return
                elif 0 <= work_index < len(book.works):
                    # Задать страницу для конкретного произведения
                    self._set_page_for_work(index, work_index)
                    return
                else:
                    print_error("Неверный номер")
                    pause()
            else:
                print_error("Неверный ввод")
                pause()

    def _set_page_for_whole_book(self, index: int) -> None:
        """✅ НОВЫЙ МЕТОД: Задать общую страницу для всей книги с произведениями"""
        book = self.books[index]
        was_finished = book.is_finished
        old_page = book.effective_current_page
        
        clear_screen()
        print_header(f"📖 Общая страница — {book.title}")
        print(f"\n Текущий прогресс: {self._format_pages(book)} ({book.progress}%)")
        
        # Показываем распределение страниц по произведениям
        print("\n Произведения:")
        for work in book.works:
            if work.counts_toward_progress:
                print(f" • {work.title}: {work.current_page}/{work.total_pages} стр.")
        
        page = ask_int(
            f"\nДо какой страницы прочитали (общий прогресс, 0–{book.progress_total_pages})",
            min_value=0,
            max_value=book.progress_total_pages,
        )
        if page is None:
            pause()
            return
        
        # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 2: Проверяем уменьшение прогресса
        if page < old_page:
            print_error(f"Нельзя уменьшить прогресс (было {old_page})")
            pause()
            return
        
        # Распределяем страницы по произведениям
        pages_to_add = page - old_page
        remaining = pages_to_add
        
        print(f"\n Распределение {pages_to_add} стр. по произведениям:")
        
        for work in book.works:
            if remaining <= 0:
                break
            
            if not work.counts_toward_progress:
                continue
            
            available = work.total_pages - work.current_page
            if available <= 0:
                continue
            
            to_add = min(remaining, available)
            work.current_page += to_add
            remaining -= to_add
            
            # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 3: Правильная логика статусов
            if work.current_page >= work.total_pages and work.total_pages > 0:
                work.set_status("finished")
            elif work.current_page > 0 and work.status == "planned":
                work.set_status("reading")
            
            print(f" ✓ {work.title}: +{to_add} стр. ({work.current_page}/{work.total_pages})")
        
        book.sync_from_works()
        delta = book.effective_current_page - old_page
        
        if delta > 0:
            ReadingLogService.record_pages(self.reading_log, delta)
            print_success(f"\n Добавлено {delta} стр. Прогресс: {book.progress}%")
        else:
            print_success(f"\n Прогресс: {book.progress}%")
        
        self._save()
        self._prompt_review_if_completed(index, was_finished)
        pause()

    def _set_page_for_work(self, book_index: int, work_index: int) -> None:
        """✅ НОВЫЙ МЕТОД: Задать страницу для конкретного произведения"""
        book = self.books[book_index]
        work = book.works[work_index]
        was_finished = book.is_finished
        old_page = book.effective_current_page
        
        if not work.counts_toward_progress:
            print_error("Произведение пропущено")
            pause()
            return
        
        clear_screen()
        print_header(f"📄 {work.title}")
        status_label = WORK_STATUS_LABELS.get(work.status, work.status)
        print(f"\n Статус: {status_label}")
        print(f" Прогресс: {work.current_page}/{work.total_pages} ({work.progress}%)")
        print(f" {progress_bar(work.progress)}")
        
        page = ask_int(
            f"\nДо какой страницы прочитали (0–{work.total_pages})",
            min_value=0,
            max_value=work.total_pages,
        )
        if page is None:
            pause()
            return
        
        # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 2: Проверяем уменьшение прогресса
        if page < work.current_page:
            print_error(f"Нельзя уменьшить прогресс (было {work.current_page})")
            pause()
            return
        
        old_work_page = work.current_page
        work.current_page = page
        
        # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 3: Правильная логика статусов
        if work.current_page >= work.total_pages and work.total_pages > 0:
            work.set_status("finished")
        elif work.current_page > 0 and work.status == "planned":
            work.set_status("reading")
        elif work.current_page == 0:
            work.set_status("planned")
        
        book.sync_from_works()
        delta = book.effective_current_page - old_page
        
        if delta > 0:
            ReadingLogService.record_pages(self.reading_log, delta)
            print_success(f"\n Добавлено {delta} стр. Прогресс произведения: {work.progress}%")
        else:
            print_success(f"\n Прогресс произведения: {work.progress}%")
        
        print(f" Общий прогресс книги: {book.progress}%")
        
        self._save()
        self._prompt_review_if_completed(book_index, was_finished)
        pause()

    def _manage_works(self, index: int) -> None:
        book = self.books[index]
        if not book.works:
            print_error("Произведения не добавлены. Используйте «изменить» для настройки.")
            pause()
            return
        was_finished = book.is_finished
        old_page = book.effective_current_page
        while True:
            clear_screen()
            print_header(f"📖 Произведения — {book.title}")
            print(f"\n Прогресс книги: {book.progress}% · {self._format_pages(book)}")
            for work_index, work in enumerate(book.works, start=1):
                status_label = WORK_STATUS_LABELS.get(work.status, work.status)
                if work.counts_toward_progress:
                    pages = f"{work.current_page}/{work.total_pages} стр. · {work.progress}%"
                else:
                    pages = f"{work.total_pages} стр. · пропущено"
                print(f"\n{work_index}. {work.title}")
                print(f" {pages} · {status_label}")
            choice = input(
                "\n[n] номер произведения [0] назад\n> "
            ).strip().lower()
            if choice in {"0", "q", "назад"}:
                delta = book.effective_current_page - old_page
                if delta > 0:
                    ReadingLogService.record_pages(self.reading_log, delta)
                self._save()
                self._prompt_review_if_completed(index, was_finished)
                return
            if choice.isdigit():
                work_index = int(choice) - 1
                if 0 <= work_index < len(book.works):
                    self._work_menu(index, work_index)
                else:
                    print_error("Неверный номер")
                pause()

    def _work_menu(self, book_index: int, work_index: int) -> None:
        book = self.books[book_index]
        work = book.works[work_index]
        while True:
            clear_screen()
            print_header(f"📄 {work.title}")
            status_label = WORK_STATUS_LABELS.get(work.status, work.status)
            print(f"\n Статус: {status_label}")
            if work.counts_toward_progress:
                print(f" Прогресс: {work.current_page}/{work.total_pages} ({work.progress}%)")
                print(f" {progress_bar(work.progress)}")
            print(
                "\n 1. +1 страница\n"
                " 2. Задать страницу\n"
                " 3. Изменить статус\n"
                " 0. Назад"
            )
            choice = ask_int("\nПункт", min_value=0, max_value=3)
            if choice is None:
                continue
            if choice == 0:
                return
            if choice == 1:
                if not work.counts_toward_progress:
                    print_error("Произведение пропущено")
                    pause()
                    continue
                if work.current_page >= work.total_pages:
                    print_error("Произведение уже прочитано")
                    pause()
                    continue
                if work.status != "reading" and work.current_page == 0:
                    work.set_status("reading")
                work.current_page += 1
                if work.current_page >= work.total_pages:
                    work.set_status("finished")
                book.sync_from_works()
                self._save()
                print_success(f"Страница {work.current_page}/{work.total_pages}")
                pause()
            elif choice == 2:
                if not work.counts_toward_progress:
                    print_error("Произведение пропущено")
                    pause()
                    continue
                page = ask_int(
                    f"Текущая страница (0–{work.total_pages})",
                    min_value=0,
                    max_value=work.total_pages,
                )
                if page is None:
                    pause()
                    continue
                
                # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 2: Проверяем уменьшение прогресса
                old_work_page = work.current_page
                if page < old_work_page:
                    print_error(f"Нельзя уменьшить прогресс (было {old_work_page})")
                    pause()
                    continue
                
                work.current_page = page
                
                # ✅ ИСПРАВЛЕНИЕ ОШИБКИ 3: Правильная логика статусов
                if work.current_page >= work.total_pages and work.total_pages > 0:
                    work.set_status("finished")
                elif work.current_page > 0 and work.status == "planned":
                    work.set_status("reading")
                elif work.current_page == 0:
                    work.set_status("planned")
                
                book.sync_from_works()
                self._save()
                print_success(f"Прогресс: {work.progress}%")
                pause()
            elif choice == 3:
                self._change_work_status(work)
                book.sync_from_works()
                self._save()

    def _change_work_status(self, work: Work) -> None:
        options = list(WORK_STATUS_LABELS.values())
        print("\n Статусы:")
        for index, label in enumerate(options, start=1):
            print(f" {index}. {label}")
        choice = ask_int("Номер статуса", min_value=1, max_value=len(options))
        if choice is None:
            return
        status = WORK_STATUSES[choice-1]
        work.set_status(status)
        print_success(f"Статус: {WORK_STATUS_LABELS[status]}")
        pause()

    def _edit_book(self, index: int) -> None:
        book = self.books[index]
        was_finished = book.is_finished
        old_page = book.effective_current_page
        clear_screen()
        print_header(f"✏️ Изменить — {book.title}")
        try:
            updated = self._prompt_book_form(book)
        except ValueError as error:
            print_error(str(error))
            pause()
            return
        if updated is None:
            pause()
            return
        delta = updated.effective_current_page - old_page
        if delta > 0:
            ReadingLogService.record_pages(self.reading_log, delta)
        self.books[index] = updated
        self._save()
        print_success("Книга обновлена")
        self._prompt_review_if_completed(index, was_finished)
        pause()

    def _prompt_new_book_wizard(self) -> Book | None:
        total_steps = 3
        clear_screen()
        print_header("➕ Новая книга")
        print_form_step(1, total_steps, "Основное")
        print_hint("Название обязательно. Автор можно указать позже.")
        title = ask_text("Название", required=True)
        if title is None:
            return None
        author = ask_text("Автор", hint="Enter — без автора") or ""
        clear_screen()
        print_header("➕ Новая книга")
        print_form_step(2, total_steps, "Объём и прогресс")
        print_hint("Укажите общее число страниц и сколько уже прочитано.")
        total = ask_int("Всего страниц", min_value=1)
        if total is None:
            return None
        works: list[Work] = []
        current_page = 0
        if ask_yes_no("Разбить книгу на произведения (главы, тома)?"):
            works = self._prompt_works(total)
            if works is None:
                return None
        else:
            current = ask_int(
                "Текущая страница",
                min_value=0,
                max_value=total,
                hint=f"Enter — начать с 0 из {total}",
            )
            current_page = 0 if current is None else current
        clear_screen()
        print_header("➕ Новая книга")
        print_form_step(3, total_steps, "Дополнительно")
        print_hint("Эти поля необязательны — можно пропустить Enter.")
        description = ask_text("Описание") or ""
        marketplace = normalize_url(ask_text("Ссылка на маркетплейс") or "")
        book = Book(
            title=title,
            author=author,
            total_pages=total,
            current_page=current_page,
            description=description,
            marketplace_url=marketplace,
            works=works,
        )
        book.validate_works()
        if not self._confirm_new_book(book):
            return None
        return book

    def _confirm_new_book(self, book: Book) -> bool:
        clear_screen()
        print_header("➕ Новая книга")
        print_section("Проверьте данные")
        print_key_value("Название", book.title)
        print_key_value("Автор", book.author)
        print_key_value("Страницы", self._format_pages(book))
        print(f" {'Прогресс':<14}{book.progress:.0f}%")
        print(f" {'':14}{progress_bar(book.progress)}")
        if book.description:
            print_key_value("Описание", book.description)
        if book.marketplace_url:
            print_key_value("Ссылка", book.marketplace_url)
        if book.has_works:
            print_section(f"Произведения ({len(book.works)})")
            for work in book.works:
                status_label = WORK_STATUS_LABELS.get(work.status, work.status)
                print(f" • {work.title} — {work.total_pages} стр. · {status_label}")
        print()
        return ask_yes_no("Сохранить книгу?", default=True)

    def _prompt_book_form(self, book: Book | None = None) -> Book | None:
        if book is None:
            return self._prompt_new_book_wizard()
        print_section("Основное")
        title = ask_text("Название", required=True, default=book.title) or book.title
        if not title:
            return None
        author = ask_text("Автор", default=book.author or None)
        if author is None:
            author = book.author
        author = author or ""

        print_section("Объём")
        total_raw = ask_int("Всего страниц", min_value=1)
        if total_raw is None:
            total = book.total_pages
        else:
            total = total_raw
        description = ask_text("Описание", default=book.description or None)
        if description is None:
            description = book.description
        description = description or ""

        marketplace = ask_text("Ссылка на маркетплейс", default=book.marketplace_url or None)
        if marketplace is None:
            marketplace = book.marketplace_url
        marketplace = normalize_url(marketplace or "")

        new_review = ask_text("Мнение о книге", default=book.review or None)
        review = book.review if new_review is None else new_review

        works = list(book.works)
        if ask_yes_no("Добавить или изменить произведения?"):
            updated_works = self._prompt_works(total, works)
            if updated_works is None:
                return None
            works = updated_works

        if works:
            current_page = 0
        else:
            current = ask_int(
                "Текущая страница",
                min_value=0,
                max_value=total,
                hint=f"Enter — оставить {book.current_page}",
            )
            current_page = book.current_page if current is None else current

        updated = Book(
            title=title,
            author=author,
            total_pages=total,
            current_page=current_page,
            description=description,
            marketplace_url=marketplace,
            review=review,
            works=works,
        )
        updated.validate_works()
        return updated

    def _prompt_works(
        self,
        book_total_pages: int,
        existing: list[Work] | None = None,
    ) -> list[Work] | None:
        works = list(existing or [])
        while True:
            clear_screen()
            print_header("📖 Произведения в книге")
            allocated = sum(work.total_pages for work in works)
            remaining = max(book_total_pages - allocated, 0)
            print_section("Распределение страниц")
            print(f" {horizontal_bar(allocated, book_total_pages, width=28)}")
            print(f" {allocated} / {book_total_pages} стр.", end="")
            if remaining:
                print(f" · осталось {remaining}")
            else:
                print()
            if not works:
                print_hint("Добавьте произведения — главы, тома или отдельные части.")
            else:
                print_section("Список")
                for index, work in enumerate(works, start=1):
                    status_label = WORK_STATUS_LABELS.get(work.status, work.status)
                    print(
                        f" {index:>2}. {work.title}\n"
                        f" {work.current_page}/{work.total_pages} стр. · {status_label}"
                    )
            print_shortcuts(
                ("a", "добавить"),
                ("n", "номер"),
                ("0", "готово"),
                ("x", "отмена"),
            )
            choice = input("\n > ").strip().lower()
            if choice in {"x", "отмена", "cancel"}:
                return None
            if choice in {"0", "г", "done"}:
                allocated = sum(item.total_pages for item in works)
                if allocated > book_total_pages:
                    print_error(
                        f"Сумма страниц произведений ({allocated}) "
                        f"не может превышать {book_total_pages}"
                    )
                    pause()
                    continue
                return works
            if choice in {"a", "д", "add"}:
                work = self._prompt_single_work(book_total_pages)
                if work:
                    works.append(work)
                continue
            if choice.isdigit():
                work_index = int(choice) - 1
                if 0 <= work_index < len(works):
                    print_shortcuts(("e", "изменить"), ("d", "удалить"))
                    action = input("\n > ").strip().lower()
                    if action in {"d", "у"}:
                        works.pop(work_index)
                    elif action in {"e", "и"}:
                        updated = self._prompt_single_work(
                            book_total_pages,
                            works[work_index],
                        )
                        if updated:
                            works[work_index] = updated
                    else:
                        print_error("Неверная команда")
                    pause()

    def _prompt_single_work(
        self,
        book_total_pages: int,
        work: Work | None = None,
    ) -> Work | None:
        clear_screen()
        print_header("➕ Произведение" if work is None else "✏️ Произведение")
        print_hint(f"В книге доступно до {book_total_pages} страниц суммарно.")
        print_section("Основное")
        title = ask_text("Название", required=True)
        if not title:
            return None
        total = ask_int("Всего страниц", min_value=1)
        if total is None:
            return None
        print_section("Прогресс")
        default_current = work.current_page if work else 0
        current = ask_int(
            "Прочитано",
            min_value=0,
            max_value=total,
            hint=f"Enter — {default_current}",
        )
        current_page = default_current if current is None else current
        print_section("Статус")
        for index, label in enumerate(WORK_STATUS_LABELS.values(), start=1):
            print(f" {index}. {label}")
        default_status = work.status if work else "planned"
        default_index = WORK_STATUSES.index(default_status) + 1
        status_choice = ask_int(
            "Статус",
            min_value=1,
            max_value=len(WORK_STATUSES),
            hint=f"Enter — {WORK_STATUS_LABELS[default_status]}",
        )
        status = WORK_STATUSES[(status_choice or default_index) - 1]
        return Work(title, total, current_page, status)

    def _prompt_review_if_completed(self, index: int, was_finished: bool) -> None:
        book = self.books[index]
        if book.is_finished and not was_finished and not book.review:
            print_success(f"🎉 Вы дочитали «{book.title}»!")
            if ask_yes_no("Оставить мнение о книге?"):
                review = ask_text("Мнение", required=False) or ""
                if review:
                    book.review = review
                self._save()

    def _delete_book(self, index: int) -> None:
        book = self.books[index]
        if not ask_yes_no(f"Удалить «{book.title}»?"):
            return
        self.books.pop(index)
        self._save()
        print_success("Книга удалена")
        pause()

    def _export(self) -> None:
        if not self.books:
            print_error("Нет книг для экспорта")
            pause()
            return
        print_header("📥 Экспорт")
        print(" 1. CSV (без зависимостей)")
        print(" 2. Excel (нужен openpyxl)")
        print(" 0. Назад")
        choice = ask_int("Формат", min_value=0, max_value=2)
        if not choice:
            return
        default_name = "book_tracker_library.csv" if choice == 1 else "book_tracker_library.xlsx"
        path_str = ask_text(f"Путь к файлу [{default_name}]") or default_name
        path = Path(path_str).expanduser()
        try:
            if choice == 1:
                saved = export_books_to_csv(self.books, path)
            else:
                saved = export_books_to_excel(self.books, path)
        except (OSError, ImportError, ValueError) as error:
            print_error(str(error))
            pause()
            return
        print_success(f"Сохранено: {saved}")
        pause()

    def _save(self) -> None:
        save_books(self.books)
        from storage.reading_log import save_reading_log
        save_reading_log(self.reading_log)