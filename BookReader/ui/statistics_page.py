import customtkinter as ctk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from services.reading_log_service import ReadingLogService
from ui.colors import COLORS


class StatisticsPage:

    CHART_COLORS = {
        "figure": COLORS["bg_card"],
        "axes": COLORS["bg_card"],
        "text": COLORS["text_main"],
        "muted": COLORS["text_muted"],
        "bar": COLORS["accent"],
        "line": COLORS["accent"],
        "line_fill": COLORS["accent"],
        "point": COLORS["accent_hover"],
        "point_hover": COLORS["success"],
        "grid": "#45475a",
        "tooltip_bg": "#45475a",
        "tooltip_border": COLORS["accent"],
    }
    CHART_FIGURE_WIDTH = 10
    CHART_FIGURE_HEIGHT = 4.2
    CHART_DPI = 72
    READING_CHART_DAYS = 14
    HOVER_RADIUS_PX = 18

    def __init__(self, parent, books, reading_log=None):
        self.parent = parent
        self.books = books
        self.reading_log = reading_log or {}
        self._card_values = {}
        self._percent_label = None
        self._reading_summary_label = None
        self._reading_chart_host = None
        self._books_chart_host = None
        self._empty_books_label = None
        self._chart_job = None

        self._build_shell()
        self._schedule_charts()

    def refresh(self, books, reading_log):
        self.books = books
        self.reading_log = reading_log or {}
        self._update_summary()
        self._clear_chart_hosts()
        self._schedule_charts()

    def _schedule_charts(self):
        if self._chart_job is not None:
            self.parent.after_cancel(self._chart_job)
        self._chart_job = self.parent.after_idle(self._render_charts)

    def _build_shell(self):
        ctk.CTkLabel(
            self.parent,
            text="📊 Статистика чтения",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(pady=20)

        cards = ctk.CTkFrame(self.parent, fg_color="transparent")
        cards.pack(fill="x", padx=20, pady=10)
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stats = self.compute_stats()
        self._card_values["total_books"] = self.card(cards, "Книг", stats["total_books"], 0)
        self._card_values["total_pages"] = self.card(cards, "Страниц", stats["total_pages"], 1)
        self._card_values["read_pages"] = self.card(cards, "Прочитано", stats["read_pages"], 2)
        self._card_values["completed"] = self.card(cards, "Завершено", stats["completed"], 3)

        self._percent_label = ctk.CTkLabel(
            self.parent,
            text=f"Общий прогресс: {stats['percent']}%",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        )
        self._percent_label.pack(pady=20)

        reading_section = ctk.CTkFrame(self.parent, fg_color="transparent")
        reading_section.pack(fill="x", padx=20, pady=(0, 10))

        header = ctk.CTkFrame(reading_section, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="📈 График чтения",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(side="left")

        self._reading_summary_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"],
        )
        self._reading_summary_label.pack(side="right")

        self._reading_chart_host = ctk.CTkFrame(reading_section, fg_color="transparent")
        self._reading_chart_host.pack(fill="x")

        self._books_chart_host = ctk.CTkFrame(self.parent, fg_color="transparent")
        self._books_chart_host.pack(fill="x", padx=20, pady=(10, 20))

        self._empty_books_label = ctk.CTkLabel(
            self.parent,
            text="Добавьте книги в библиотеку, чтобы увидеть прогресс по книгам",
            text_color=COLORS["text_muted"],
        )

        self._update_summary()

    def _update_summary(self):
        stats = self.compute_stats()

        card_titles = {
            "total_books": ("Книг", stats["total_books"]),
            "total_pages": ("Страниц", stats["total_pages"]),
            "read_pages": ("Прочитано", stats["read_pages"]),
            "completed": ("Завершено", stats["completed"]),
        }
        for key, label in self._card_values.items():
            label.configure(text=str(card_titles[key][1]))

        self._percent_label.configure(text=f"Общий прогресс: {stats['percent']}%")

        series = ReadingLogService.get_daily_series(
            self.reading_log,
            days=self.READING_CHART_DAYS,
        )
        total = ReadingLogService.total_pages(series)
        average = ReadingLogService.average_pages(series)
        self._reading_summary_label.configure(
            text=f"За {self.READING_CHART_DAYS} дней: {total} стр. · в среднем {average} стр./день",
        )

        if self.books:
            self._empty_books_label.pack_forget()
        else:
            self._empty_books_label.pack(pady=(10, 40))

    def _clear_chart_hosts(self):
        for host in (self._reading_chart_host, self._books_chart_host):
            for widget in host.winfo_children():
                widget.destroy()

    def _render_charts(self):
        self._chart_job = None
        self._clear_chart_hosts()
        self._render_reading_chart(self._reading_chart_host)

        if self.books:
            self._render_books_chart(self._books_chart_host)

    def compute_stats(self):
        total_books = len(self.books)
        total_pages = sum(book.total_pages for book in self.books)
        read_pages = sum(book.current_page for book in self.books)
        completed = sum(1 for book in self.books if book.progress >= 100)

        percent = 0
        if total_pages:
            percent = round(read_pages / total_pages * 100, 1)

        return {
            "total_books": total_books,
            "total_pages": total_pages,
            "read_pages": read_pages,
            "completed": completed,
            "percent": percent,
        }

    @staticmethod
    def style_axes_text(ax, colors, *, title=None, xlabel=None, ylabel=None):
        if title:
            ax.set_title(title, color=colors["text"], pad=12, fontsize=12)
            ax.title.set_color(colors["text"])
        if xlabel:
            ax.set_xlabel(xlabel, color=colors["text"])
            ax.xaxis.label.set_color(colors["text"])
        if ylabel:
            ax.set_ylabel(ylabel, color=colors["text"])
            ax.yaxis.label.set_color(colors["text"])

    @staticmethod
    def bar_height_for_count(book_count: int) -> float:
        if book_count <= 0:
            return 0.65
        available = StatisticsPage.CHART_FIGURE_HEIGHT - 1.2
        return min(0.65, max(0.22, available / book_count * 0.75))

    def _create_figure(self):
        fig = Figure(
            figsize=(self.CHART_FIGURE_WIDTH, self.CHART_FIGURE_HEIGHT),
            dpi=self.CHART_DPI,
        )
        fig.patch.set_facecolor(self.CHART_COLORS["figure"])
        return fig

    def _render_reading_chart(self, parent):
        series = ReadingLogService.get_daily_series(
            self.reading_log,
            days=self.READING_CHART_DAYS,
        )
        total = ReadingLogService.total_pages(series)

        if total == 0:
            ctk.CTkLabel(
                parent,
                text="Отмечайте прогресс в библиотеке — здесь появится дневной график",
                text_color=COLORS["text_muted"],
            ).pack(pady=(8, 16))
            return

        chart_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"])
        chart_frame.pack(fill="x", pady=(8, 0))

        colors = self.CHART_COLORS
        dates = [item["date"] for item in series]
        pages = [item["pages"] for item in series]

        fig = self._create_figure()
        ax = fig.add_subplot(111)
        ax.set_facecolor(colors["axes"])

        ax.fill_between(
            dates,
            pages,
            color=colors["line_fill"],
            alpha=0.18,
        )
        ax.plot(
            dates,
            pages,
            color=colors["line"],
            linewidth=2.5,
            marker="o",
            markersize=7,
            markerfacecolor=colors["point"],
            markeredgecolor=colors["figure"],
            markeredgewidth=1.5,
            zorder=3,
        )

        max_pages = max(pages) if pages else 1
        ax.set_ylim(0, max(max_pages * 1.25, 5))
        self.style_axes_text(
            ax,
            colors,
            title="Сколько страниц вы читали каждый день",
            ylabel="Страниц за день",
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, self.READING_CHART_DAYS // 7)))
        ax.tick_params(axis="x", colors=colors["muted"], rotation=0, labelsize=9)
        ax.tick_params(axis="y", colors=colors["muted"], labelsize=9)
        ax.grid(True, color=colors["grid"], alpha=0.35, linestyle="--", linewidth=0.8)
        ax.spines["bottom"].set_color(colors["grid"])
        ax.spines["left"].set_color(colors["grid"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(16, 16),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.45",
                facecolor=colors["tooltip_bg"],
                edgecolor=colors["tooltip_border"],
                linewidth=1.2,
            ),
            color=colors["text"],
            fontsize=10,
            ha="left",
            va="bottom",
        )
        annot.set_visible(False)

        highlight, = ax.plot(
            [],
            [],
            marker="o",
            markersize=11,
            markerfacecolor=colors["point_hover"],
            markeredgecolor=colors["text"],
            markeredgewidth=1.5,
            linestyle="None",
            zorder=4,
        )

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", expand=False, padx=8, pady=8)

        def hide_tooltip():
            if annot.get_visible():
                annot.set_visible(False)
                highlight.set_data([], [])
                canvas.draw_idle()

        def show_tooltip(index: int):
            item = series[index]
            point_date = dates[index]
            point_pages = pages[index]

            weekday = item["date"].strftime("%A")
            weekday_ru = {
                "Monday": "Понедельник",
                "Tuesday": "Вторник",
                "Wednesday": "Среда",
                "Thursday": "Четверг",
                "Friday": "Пятница",
                "Saturday": "Суббота",
                "Sunday": "Воскресенье",
            }.get(weekday, weekday)

            annot.xy = (point_date, point_pages)
            annot.set_text(
                f"{item['date'].strftime('%d.%m.%Y')}\n"
                f"{weekday_ru}\n"
                f"{point_pages} стр."
            )
            annot.set_visible(True)
            highlight.set_data([point_date], [point_pages])
            canvas.draw_idle()

        def on_hover(event):
            if event.inaxes != ax:
                hide_tooltip()
                return

            nearest_index = None
            nearest_distance = float("inf")

            for index, (point_date, point_pages) in enumerate(zip(dates, pages)):
                display_x, display_y = ax.transData.transform((mdates.date2num(point_date), point_pages))
                distance = ((event.x - display_x) ** 2 + (event.y - display_y) ** 2) ** 0.5
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_index = index

            if nearest_index is not None and nearest_distance <= self.HOVER_RADIUS_PX:
                show_tooltip(nearest_index)
            else:
                hide_tooltip()

        canvas.mpl_connect("motion_notify_event", on_hover)
        canvas.mpl_connect("axes_leave_event", lambda _event: hide_tooltip())

    def _render_books_chart(self, parent):
        ctk.CTkLabel(
            parent,
            text="📚 Прогресс по книгам",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(anchor="w")

        chart_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"])
        chart_frame.pack(fill="x", pady=(8, 0))

        titles = [self.format_chart_label(book) for book in self.books]
        values = [book.progress for book in self.books]
        colors = self.CHART_COLORS
        bar_height = self.bar_height_for_count(len(self.books))
        label_size = 10 if len(self.books) <= 8 else 9

        fig = self._create_figure()
        ax = fig.add_subplot(111)
        ax.set_facecolor(colors["axes"])

        y_positions = range(len(titles))
        bars = ax.barh(
            y_positions,
            values,
            color=colors["bar"],
            edgecolor=colors["grid"],
            height=bar_height,
        )
        ax.set_yticks(list(y_positions))
        ax.set_yticklabels(titles, color=colors["text"], fontsize=label_size)
        ax.set_xlim(0, 100)
        self.style_axes_text(ax, colors, xlabel="Прогресс (%)")
        ax.tick_params(axis="x", colors=colors["muted"])
        ax.grid(axis="x", color=colors["grid"], alpha=0.4)
        ax.spines["bottom"].set_color(colors["grid"])
        ax.spines["left"].set_color(colors["grid"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.invert_yaxis()

        for bar, value in zip(bars, values):
            ax.text(
                min(value + 1.5, 96),
                bar.get_y() + bar.get_height() / 2,
                f"{value}%",
                va="center",
                ha="left",
                color=colors["text"],
                fontsize=9,
            )

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", expand=False, padx=8, pady=8)

    def format_chart_label(self, book) -> str:
        title = self.shorten_title(book.title, max_length=42)
        if book.author:
            return f"{title} — {self.shorten_title(book.author, max_length=24)}"
        return title

    @staticmethod
    def shorten_title(title, max_length=18):
        if len(title) <= max_length:
            return title
        return title[: max_length - 1] + "…"

    def card(self, parent, title, value, column):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"])
        frame.grid(row=0, column=column, padx=8, pady=10, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text=title,
            text_color=COLORS["text_muted"],
        ).pack(pady=(12, 0))

        value_label = ctk.CTkLabel(
            frame,
            text=str(value),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_main"],
        )
        value_label.pack(pady=(0, 12))
        return value_label
