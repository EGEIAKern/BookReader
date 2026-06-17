import customtkinter as ctk
import math

# ==========================================
# КАСТОМНАЯ ЦВЕТОВАЯ ПАЛИТРА (Стиль "Modern Dark")
# ==========================================
COLORS = {
    "bg_main": "#181825",  # Основной фон (очень темный)
    "bg_sidebar": "#1E1E2E",  # Фон боковой панели
    "bg_card": "#313244",  # Фон карточек с контентом
    "accent": "#89B4FA",  # Акцентный цвет (мягкий голубой)
    "accent_hover": "#74C7EC",  # Акцент при наведении
    "success": "#A6E3A1",  # Цвет успеха (мягкий зеленый)
    "error": "#F38BA8",  # Цвет ошибки (мягкий красный)
    "text_main": "#CDD6F4",  # Основной текст
    "text_muted": "#A6ADC8",  # Второстепенный текст
}

ctk.set_appearance_mode("dark")
# Отключаем стандартную тему, чтобы использовать наши кастомные цвета
ctk.set_default_color_theme("dark-blue")


class BookApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("📚 Отслеживание чтение книг (утилиты)")
        self.geometry("900x650")
        self.minsize(800, 550)

        # Настраиваем сетку главного окна
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(fg_color=COLORS["bg_main"])

        self.active_button = None  # Для хранения ссылки на активную кнопку меню

        self.create_sidebar()
        self.create_main_area()

        # Открываем первую вкладку по умолчанию
        self.show_frame("reading_calc", self.btn_reading)

    def create_sidebar(self):
        """Создает стильную боковую панель"""
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)  # НОВОЕ: Сдвинули растягивание пустого пространства вниз

        # Логотип / Заголовок
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
        logo_frame.grid(row=0, column=0, padx=20, pady=30, sticky="ew")

        ctk.CTkLabel(logo_frame, text="📚 Полезные утилиты",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="Ваш личный помощник в анализе",

                     font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(5, 0))

        # Кнопки навигации
        btn_style = {
            "height": 50,
            "corner_radius": 16,
            "fg_color": "transparent",
            "text_color": COLORS["text_main"],
            "hover_color": COLORS["bg_card"],
            "font": ctk.CTkFont(size=16, weight="normal"),
            "anchor": "w"
        }

        self.btn_reading = ctk.CTkButton(self.sidebar, text="  📖  Прогресс прочтения книги",
                                         command=lambda: self.show_frame("reading_calc", self.btn_reading), **btn_style)
        self.btn_reading.grid(row=1, column=0, padx=15, pady=8)

        self.btn_calc = ctk.CTkButton(self.sidebar, text="  🧮  Калькулятор",
                                      command=lambda: self.show_frame("calculator", self.btn_calc), **btn_style)
        self.btn_calc.grid(row=2, column=0, padx=15, pady=8)

        self.btn_goal = ctk.CTkButton(self.sidebar, text="  🎯  Цель чтения",
                                      command=lambda: self.show_frame("goal", self.btn_goal), **btn_style)
        self.btn_goal.grid(row=3, column=0, padx=15, pady=8)

        # НОВОЕ: Кнопка для нового раздела
        self.btn_pages_from_percent = ctk.CTkButton(self.sidebar, text="  📊  Страниц из %",
                                                    command=lambda: self.show_frame("pages_from_percent",
                                                                                    self.btn_pages_from_percent),
                                                    **btn_style)
        self.btn_pages_from_percent.grid(row=4, column=0, padx=15, pady=8)

        # Переключатель темы внизу
        theme_label = ctk.CTkLabel(self.sidebar, text="Тема оформления", text_color=COLORS["text_muted"],
                                   font=ctk.CTkFont(size=12))
        theme_label.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="w")

        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["Dark", "Light", "System"],
                                                      fg_color=COLORS["bg_card"],
                                                      button_color=COLORS["bg_card"],
                                                      button_hover_color=COLORS["accent"],
                                                      command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=8, column=0, padx=20, pady=(0, 30))

    def create_main_area(self):
        """Создает правую область с прозрачным фоном"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)

    def set_active_button(self, button):
        """Подсвечивает активную кнопку в меню"""
        if self.active_button:
            self.active_button.configure(fg_color="transparent", text_color=COLORS["text_main"])

        self.active_button = button
        self.active_button.configure(fg_color=COLORS["accent"],
                                     text_color="#11111b")

    def show_frame(self, frame_name, button_ref):
        """Очищает основную область и рисует нужный интерфейс в виде 'карточки'"""
        self.set_active_button(button_ref)

        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Создаем "карточку" для контента
        card = ctk.CTkFrame(self.main_frame, fg_color=COLORS["bg_card"], corner_radius=24)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        # Передаем карточку в строительные функции
        if frame_name == "reading_calc":
            self.build_reading_calc(card)
        elif frame_name == "calculator":
            self.build_calculator(card)
        elif frame_name == "goal":
            self.build_goal(card)
        # НОВОЕ: Маршрутизация для нового раздела
        elif frame_name == "pages_from_percent":
            self.build_pages_from_percent(card)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode.lower())

    # =================================================================
    # ФУНКЦИЯ 1: Калькулятор прогресса книги
    # =================================================================
    def build_reading_calc(self, parent):
        ctk.CTkLabel(parent, text="BookReaderOldVersion", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=COLORS["text_main"]).pack(pady=(30, 10))
        ctk.CTkLabel(parent, text="Узнайте, сколько процентов книги вы уже прочитали", font=ctk.CTkFont(size=14),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 30))

        self.total_pages_var = ctk.StringVar()
        self.current_pages_var = ctk.StringVar()

        entry_style = {"width": 350, "height": 45, "corner_radius": 12, "font": ctk.CTkFont(size=17)}
        label_style = {"font": ctk.CTkFont(size=15, weight="bold"), "text_color": COLORS["text_main"]}

        ctk.CTkLabel(parent, text="Всего страниц в книге", **label_style).pack(pady=(0, 5))
        ctk.CTkEntry(parent, textvariable=self.total_pages_var, placeholder_text="Например: 350", **entry_style).pack(
            pady=(0, 20))

        ctk.CTkLabel(parent, text="Уже прочитано страниц", **label_style).pack(pady=(0, 5))
        ctk.CTkEntry(parent, textvariable=self.current_pages_var, placeholder_text="Например: 120", **entry_style).pack(
            pady=(0, 30))

        ctk.CTkButton(parent, text="Рассчитать прогресс", height=50, corner_radius=14,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="#11111b", font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.calculate_progress).pack(pady=10)

        self.result_label = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=26, weight="bold"),
                                         text_color=COLORS["accent"])
        self.result_label.pack(pady=(30, 10))

        self.progress_bar = ctk.CTkProgressBar(parent, width=400, height=22, corner_radius=11,
                                               progress_color=COLORS["success"])
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

    def calculate_progress(self):
        try:
            total = int(self.total_pages_var.get())
            current = int(self.current_pages_var.get())

            if total <= 0 or current < 0:
                raise ValueError
            if current > total:
                current = total

            percentage = (current / total) * 100
            self.result_label.configure(text=f"{percentage:.1f}%", text_color=COLORS["accent"])
            self.progress_bar.set(percentage / 100)

            if percentage == 100:
                self.result_label.configure(text="🎉 Книга полностью прочитана! 🎉", text_color=COLORS["success"])

        except ValueError:
            self.result_label.configure(text="⚠️ Проверьте введенные данные", text_color=COLORS["error"])
            self.progress_bar.set(0)

    # =================================================================
    # ФУНКЦИЯ 2: Обычный калькулятор
    # =================================================================
    def build_calculator(self, parent):
        ctk.CTkLabel(parent, text="Калькулятор", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=COLORS["text_main"]).pack(pady=(30, 10))
        ctk.CTkLabel(parent, text="Быстрые вычисления для ваших заметок", font=ctk.CTkFont(size=14),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 30))

        self.calc_var1 = ctk.StringVar()
        self.calc_var2 = ctk.StringVar()
        self.calc_op = ctk.StringVar(value="+")

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=10)

        entry_style = {"width": 140, "height": 50, "corner_radius": 12, "font": ctk.CTkFont(size=18, weight="bold")}

        ctk.CTkEntry(frame, textvariable=self.calc_var1, placeholder_text="0", **entry_style).grid(row=0, column=0,
                                                                                                   padx=10, pady=15)
        ctk.CTkOptionMenu(frame, values=["+", "-", "*", "/"], variable=self.calc_op, width=70, height=50,
                          corner_radius=12, fg_color=COLORS["bg_main"], button_color=COLORS["accent"],
                          font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=1, padx=10, pady=15)
        ctk.CTkEntry(frame, textvariable=self.calc_var2, placeholder_text="0", **entry_style).grid(row=0, column=2,
                                                                                                   padx=10, pady=15)

        ctk.CTkButton(parent, text="Вычислить", height=50, corner_radius=14, width=300,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="#11111b", font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.calculate_math).pack(pady=30)

        self.calc_result = ctk.CTkLabel(parent, text="Результат: —", font=ctk.CTkFont(size=32, weight="bold"),
                                        text_color=COLORS["success"])
        self.calc_result.pack(pady=10)

    def calculate_math(self):
        try:
            v1 = float(self.calc_var1.get())
            v2 = float(self.calc_var2.get())
            op = self.calc_op.get()

            if op == "+":
                res = v1 + v2
            elif op == "-":
                res = v1 - v2
            elif op == "*":
                res = v1 * v2
            elif op == "/":
                if v2 == 0: raise ZeroDivisionError
                res = v1 / v2

            self.calc_result.configure(text=f"= {res:g}")
        except (ValueError, ZeroDivisionError):
            self.calc_result.configure(text="Ошибка ввода", text_color=COLORS["error"])

    # =================================================================
    # ФУНКЦИЯ 3: Цель чтения
    # =================================================================
    def build_goal(self, parent):
        ctk.CTkLabel(parent, text="Планирование чтения", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=COLORS["text_main"]).pack(pady=(30, 10))
        ctk.CTkLabel(parent, text="Рассчитайте ежедневную норму страниц", font=ctk.CTkFont(size=14),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 30))

        self.pages_left_var = ctk.StringVar()
        self.days_left_var = ctk.StringVar()

        entry_style = {"width": 350, "height": 45, "corner_radius": 12, "font": ctk.CTkFont(size=16)}
        label_style = {"font": ctk.CTkFont(size=15, weight="bold"), "text_color": COLORS["text_main"]}

        ctk.CTkLabel(parent, text="Осталось прочитать (страниц)", **label_style).pack(pady=(0, 5))
        ctk.CTkEntry(parent, textvariable=self.pages_left_var, placeholder_text="Например: 200", **entry_style).pack(
            pady=(0, 20))

        ctk.CTkLabel(parent, text="Количество дней до дедлайна", **label_style).pack(pady=(0, 5))
        ctk.CTkEntry(parent, textvariable=self.days_left_var, placeholder_text="Например: 10", **entry_style).pack(
            pady=(0, 30))

        ctk.CTkButton(parent, text="Рассчитать норму", height=50, corner_radius=14,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="#11111b", font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.calculate_goal).pack(pady=10)

        self.goal_result = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=26, weight="bold"),
                                        text_color=COLORS["success"])
        self.goal_result.pack(pady=(30, 10))

    def calculate_goal(self):
        try:
            pages = int(self.pages_left_var.get())
            days = int(self.days_left_var.get())

            if days <= 0 or pages < 0:
                raise ValueError

            per_day = math.ceil(pages / days)
            self.goal_result.configure(text=f"📖 {per_day} стр. в день")

        except ValueError:
            self.goal_result.configure(text="⚠️ Проверьте введенные данные", text_color=COLORS["error"])

    # =================================================================
    # ФУНКЦИЯ 4 (НОВАЯ): Расчет страниц по проценту
    # =================================================================
    def build_pages_from_percent(self, parent):
        ctk.CTkLabel(parent, text="Страниц из процента", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=COLORS["text_main"]).pack(pady=(30, 10))
        ctk.CTkLabel(parent, text="Узнайте, сколько страниц составляет указанный % от книги", font=ctk.CTkFont(size=14),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 30))

        self.pfp_total_var = ctk.StringVar()
        self.pfp_percent_var = ctk.StringVar()

        entry_style = {"width": 350, "height": 45, "corner_radius": 12, "font": ctk.CTkFont(size=16)}
        label_style = {"font": ctk.CTkFont(size=15, weight="bold"), "text_color": COLORS["text_main"]}

        ctk.CTkLabel(parent, text="Всего страниц в книге", **label_style).pack(pady=(0, 5))
        ctk.CTkEntry(parent, textvariable=self.pfp_total_var, placeholder_text="Например: 400", **entry_style).pack(
            pady=(0, 20))

        ctk.CTkLabel(parent, text="Процент прочтения (%)", **label_style).pack(pady=(0, 5))
        ctk.CTkEntry(parent, textvariable=self.pfp_percent_var, placeholder_text="Например: 25.5", **entry_style).pack(
            pady=(0, 30))

        ctk.CTkButton(parent, text="Рассчитать страницы", height=50, corner_radius=14,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="#11111b", font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.calculate_pages_from_percent).pack(pady=10)

        self.pfp_result_label = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=26, weight="bold"),
                                             text_color=COLORS["success"])
        self.pfp_result_label.pack(pady=(30, 10))

    def calculate_pages_from_percent(self):
        try:
            total = float(self.pfp_total_var.get())
            percent = float(self.pfp_percent_var.get())

            if total <= 0:
                raise ValueError("Общее кол-во страниц должно быть больше 0")
            if percent < 0 or percent > 100:
                raise ValueError("Процент должен быть от 0 до 100")

            # Округляем до ближайшего целого числа страниц
            pages_read = round((total * percent) / 100)

            self.pfp_result_label.configure(
                text=f"📖 Это {pages_read} страниц от книги",
                text_color=COLORS["success"]
            )

        except ValueError:
            self.pfp_result_label.configure(
                text="⚠️ Введите корректные числа (0-100%)",
                text_color=COLORS["error"]
            )


if __name__ == "__main__":
    app = BookApp()
    app.mainloop()