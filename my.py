# Версия v1.0.3b - Минимализм + Настройки + Вкладки + Gemini + Темная Тема + Discord Webhook + GitHub Update Checker (Исправлены ошибки)
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext, Menu
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service # Service не используется напрямую в этом коде
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import requests # Used for API calls, avatar display, Discord webhook, GitHub updates
import os
import shutil
from bs4 import BeautifulSoup
import re
import threading
import json # Used for settings and API communication
from PIL import Image, ImageTk
import traceback # Used for error logging
import asyncio
import webbrowser # Для открытия URL при обновлении

# --- Библиотеки для платформ и функций ---
# Инициализация root нужна до первого вызова messagebox, если он происходит до root = tk.Tk()
# Это редкий случай, но для безопасности можно сделать так:
_tk_root_for_import_errors = tk.Tk()
_tk_root_for_import_errors.withdraw() # Скрыть временное окно

try:
    import pytube; from pytube.exceptions import PytubeError
except ImportError: messagebox.showerror("Import Error", "Pytube не найден. pip install pytube"); pytube = None
try:
    import aiogram; from aiogram import Bot; from aiogram.types import FSInputFile
    from aiogram.exceptions import (TelegramAPIError, TelegramBadRequest, TelegramForbiddenError, TelegramNotFound)
except ImportError: messagebox.showerror("Import Error", "Aiogram не найден. pip install aiogram>=3.0"); aiogram = None
try:
    import packaging.version
except ImportError: messagebox.showerror("Import Error", "Packaging не найден. pip install packaging"); packaging = None

_tk_root_for_import_errors.destroy() # Уничтожить временное окно
del _tk_root_for_import_errors


# --- Global Variables & Settings ---
APP_VERSION = "1.0.3b" # Версия приложения
# ЗАПОЛНИТЕ ЭТИ ДАННЫЕ ДЛЯ ПРОВЕРКИ ОБНОВЛЕНИЙ GITHUB:
GITHUB_REPO_OWNER = "sas937"  # Имя пользователя или организации на GitHub
GITHUB_REPO_NAME = "MediaDownloader" # Название вашего репозитория на GitHub

# Глобальная константа для базовой темы TTK
OS_BASE_THEME = 'vista' if os.name == 'nt' else ('aqua' if os.name == 'darwin' else 'clam')

media_urls_checkboxes = []; driver = None
INSTAGRAM_LOGIN_URL = "https://www.instagram.com/accounts/login/"
TIKTOK_LOGIN_URL = "https://www.tiktok.com/login/phone-or-email/email"
YOUTUBE_LOGIN_URL = "https://accounts.google.com/ServiceLogin?service=youtube"
is_instagram_logged_in = False; is_tiktok_logged_in = False; is_youtube_logged_in = False
SETTINGS_FILE = "app_settings.json"

# Настройки по умолчанию
app_settings = {
    "telegram_token": "",
    "telegram_chat_id": "",
    "gemini_api_key": "AIzaSyAZqoRPw1gMVfcQOqvDAl9evj1vxaSFcV4", # Используется внутренний ключ для Gemini
    "discord_webhook_url": "",
    "theme": "light" # 'light' или 'dark'
}

# --- Цветовые схемы для тем ---
THEMES = {
    "light": {
        "bg": "#F0F0F0", "fg": "black", "entry_bg": "white", "entry_fg": "black",
        "button_bg": "#E1E1E1", "button_fg": "black", "accent_button_bg": "#0078D7", "accent_button_fg": "white",
        "text_bg": "white", "text_fg": "black", "listbox_bg": "white", "listbox_fg": "black",
        "label_frame_bg": "#F0F0F0", "status_bar_bg": "#E0E0E0", "menu_bg": "#F0F0F0", "menu_fg": "black",
        "disabled_fg": "grey", "avatar_placeholder_bg": "lightgrey", "relief": "groove", "entry_insert": "black",
        "notebook_tab_bg": "#E1E1E1", "notebook_tab_fg": "black", "notebook_tab_selected_bg": "#0078D7", "notebook_tab_selected_fg": "white",
        "scrollbar_bg": "#E1E1E1", "scrollbar_trough": "#F0F0F0", "progressbar_bg": "#0078D7", "progressbar_trough": "#E1E1E1"
    },
    "dark": {
        "bg": "#2E2E2E", "fg": "white", "entry_bg": "#3C3C3C", "entry_fg": "white",
        "button_bg": "#505050", "button_fg": "white", "accent_button_bg": "#005A9E", "accent_button_fg": "white",
        "text_bg": "#3C3C3C", "text_fg": "white", "listbox_bg": "#3C3C3C", "listbox_fg": "white",
        "label_frame_bg": "#2E2E2E", "status_bar_bg": "#1E1E1E", "menu_bg": "#2E2E2E", "menu_fg": "white",
        "disabled_fg": "darkgrey", "avatar_placeholder_bg": "#4A4A4A", "relief": "solid", "entry_insert": "white",
        "notebook_tab_bg": "#505050", "notebook_tab_fg": "white", "notebook_tab_selected_bg": "#005A9E", "notebook_tab_selected_fg": "white",
        "scrollbar_bg": "#505050", "scrollbar_trough": "#2E2E2E", "progressbar_bg": "#005A9E", "progressbar_trough": "#505050"
    }
}
current_theme_colors = THEMES["light"] # По умолчанию светлая


# --- Функции Настроек, Драйвера, Аватарок, Логина/Логаута ---
def load_settings():
    global app_settings, current_theme_colors
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                for key in app_settings:
                    if key in loaded_settings:
                        app_settings[key] = loaded_settings[key]
            print("Настройки загружены из", SETTINGS_FILE)
        else:
            print("Файл настроек не найден. Используются значения по умолчанию.")
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка загрузки настроек: {e}. Используются значения по умолчанию.")

    current_theme_colors = THEMES.get(app_settings.get("theme", "light"), THEMES["light"])
    app_settings["gemini_api_key"] = "AIzaSyAZqoRPw1gMVfcQOqvDAl9evj1vxaSFcV4"


def save_settings():
    global app_settings
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_settings, f, indent=4, ensure_ascii=False)
        print("Настройки сохранены в", SETTINGS_FILE)
        if 'status_label' in globals() and status_label: update_status("Настройки сохранены.")
    except IOError as e:
        print(f"Ошибка сохранения настроек: {e}")
        messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

def open_settings_window():
    global app_settings
    settings_win = tk.Toplevel(root)
    settings_win.title("Настройки API и Приложения")
    settings_win.geometry("600x250")
    settings_win.resizable(False, False)
    settings_win.transient(root)
    settings_win.grab_set()

    main_frame = ttk.Frame(settings_win, padding="10")
    main_frame.pack(expand=True, fill="both")

    tg_token_var = tk.StringVar(value=app_settings.get("telegram_token", ""))
    tg_chat_id_var = tk.StringVar(value=app_settings.get("telegram_chat_id", ""))
    gemini_key_var = tk.StringVar(value=app_settings.get("gemini_api_key", "AIzaSyAZqoRPw1gMVfcQOqvDAl9evj1vxaSFcV4"))
    discord_webhook_var = tk.StringVar(value=app_settings.get("discord_webhook_url", ""))

    ttk.Label(main_frame, text="Telegram Bot Token:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(main_frame, textvariable=tg_token_var, width=60, show="*").grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(main_frame, text="Telegram Chat ID / @user:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(main_frame, textvariable=tg_chat_id_var, width=60).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(main_frame, text="Discord Webhook URL:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(main_frame, textvariable=discord_webhook_var, width=60, show="*").grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(main_frame, text="Gemini API Key (для информации):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    gemini_entry = ttk.Entry(main_frame, textvariable=gemini_key_var, width=60, show="*")
    gemini_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    main_frame.columnconfigure(1, weight=1)
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="e")

    def save_and_close_settings():
        app_settings["telegram_token"] = tg_token_var.get().strip()
        app_settings["telegram_chat_id"] = tg_chat_id_var.get().strip()
        app_settings["gemini_api_key"] = gemini_key_var.get().strip()
        app_settings["discord_webhook_url"] = discord_webhook_var.get().strip()
        save_settings()
        apply_theme_to_all_widgets(root)
        settings_win.destroy()

    save_button = ttk.Button(button_frame, text="Сохранить", command=save_and_close_settings, style='Accent.TButton')
    save_button.pack(side="left", padx=5)
    cancel_button = ttk.Button(button_frame, text="Отмена", command=settings_win.destroy)
    cancel_button.pack(side="left", padx=5)

    settings_win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (settings_win.winfo_width() // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (settings_win.winfo_height() // 2)
    settings_win.geometry(f'+{x}+{y}')
    settings_win.focus_set()
    apply_theme_to_all_widgets(settings_win)


def init_driver():
    global driver
    if driver is None:
        chrome_options = Options(); user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"--user-agent={user_agent}"); chrome_options.add_argument("--disable-gpu"); chrome_options.add_argument("--log-level=3"); chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled"); chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False); chrome_options.add_argument("--no-sandbox"); chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions"); chrome_options.add_argument("--start-maximized")
        try: driver = webdriver.Chrome(options=chrome_options); update_status("Драйвер запущен.")
        except Exception as e: messagebox.showerror("Ошибка драйвера", f"{e}"); update_status("Ошибка драйвера."); driver = None
    return driver

def close_driver():
    global driver,is_instagram_logged_in,is_tiktok_logged_in,is_youtube_logged_in
    if driver:
        try: driver.quit()
        except Exception as e: print(f"Ошибка закрытия драйвера: {e}")
        finally: driver = None; is_instagram_logged_in = False; is_tiktok_logged_in = False; is_youtube_logged_in = False; reset_login_ui("instagram"); reset_login_ui("tiktok"); reset_login_ui("youtube"); update_status("Драйвер остановлен.")

def display_avatar_in_label(avatar_url, label_widget, platform_name="User"):
    def _task():
        try:
            response = requests.get(avatar_url, stream=True, timeout=15); response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower();
            if 'image' not in content_type: raise ValueError(f"URL не изображение (Content-Type: {content_type})")
            img = Image.open(response.raw); img = img.resize((40, 40), Image.Resampling.LANCZOS); photo = ImageTk.PhotoImage(img)
            label_widget.config(image=photo, text="", bg="", relief="flat"); label_widget.image = photo; # Убираем фон и рамку, если картинка есть
        except Exception as e:
            print(f"Ошибка аватара {platform_name}: {e}")
            label_widget.config(text="N/A", image='', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"])
            label_widget.image = None
    label_widget.config(image='', text='...', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"]); label_widget.image = None; threading.Thread(target=_task, daemon=True).start()

def reset_login_ui(platform):
    global current_theme_colors
    avatar_bg = current_theme_colors["avatar_placeholder_bg"]
    avatar_relief = current_theme_colors["relief"]
    if platform == "instagram":
        instagram_avatar_label.config(text=" ",image='', bg=avatar_bg, relief=avatar_relief); instagram_avatar_label.image=None
        instagram_login_button.config(text="Войти в Instagram",command=login_to_instagram)
    elif platform == "tiktok":
        tiktok_avatar_label.config(text=" ",image='', bg=avatar_bg, relief=avatar_relief); tiktok_avatar_label.image=None
        tiktok_login_button.config(text="Войти в TikTok",command=login_to_tiktok)
    elif platform == "youtube":
        youtube_avatar_label.config(text=" ",image='', bg=avatar_bg, relief=avatar_relief); youtube_avatar_label.image=None
        youtube_login_button.config(text="Войти в YouTube",command=login_to_youtube)

def logout_from(platform):
    global is_instagram_logged_in,is_tiktok_logged_in,is_youtube_logged_in
    print(f"Logout (UI reset) for {platform}")
    if platform=="instagram": is_instagram_logged_in=False; reset_login_ui("instagram")
    elif platform=="tiktok": is_tiktok_logged_in=False; reset_login_ui("tiktok")
    elif platform=="youtube": is_youtube_logged_in=False; reset_login_ui("youtube")
    update_status(f"Выполнен выход (UI) из {platform.capitalize()}.")

def login_to_instagram():
    global driver, is_instagram_logged_in, current_theme_colors
    if is_instagram_logged_in: return
    if not init_driver():return
    username = instagram_username_entry.get()
    password = instagram_password_entry.get()
    if not username or not password: messagebox.showerror("Ошибка (Instagram)", "Введите данные."); return
    try:
        driver.get(INSTAGRAM_LOGIN_URL);update_status("Instagram: Загрузка...");
        WebDriverWait(driver,15).until(EC.presence_of_element_located((By.NAME,"username"))).send_keys(username)
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.NAME,"password"))).send_keys(password)
        time.sleep(0.5);WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"//button[@type='submit']"))).click()
        update_status("Instagram: Вход...");time.sleep(8)
        selectors=["//button[contains(text(),'Not Now')]","//button[contains(text(),'Не сейчас')]","//div[@role='button'][contains(.,'Not Now')]","//div[@role='button'][contains(.,'Не сейчас')]"];
        for _ in range(2):
            found=False;
            for sel in selectors:
                try:
                    btns=driver.find_elements(By.XPATH,sel)
                    if btns:
                        for btn in btns:
                            if btn.is_displayed()and btn.is_enabled():btn.click();update_status("Insta: Pop-up...");time.sleep(2.5);found=True;break
                        if found:break
                except:pass
            if not found:break;time.sleep(1)
        url_page=driver.current_url
        if"instagram.com"in url_page and"accounts/login"not in url_page and"challenge"not in url_page:
            update_status("Instagram: Вход выполнен.");messagebox.showinfo("Вход (Instagram)","Успешно!")
            is_instagram_logged_in=True;instagram_login_button.config(text="Выйти из Instagram",command=lambda:logout_from("instagram"))
            try:
                avatar_img_el=None;url_av=None;print("INFO: Ищем аватар...");xpath_list=[f"//header//a[contains(@href,'/{username}/')]//img[contains(@alt,'profile')or contains(@alt,'Профиль')]",f"//header//img[contains(@alt,'profile picture')or contains(@alt,'Фото профиля')or contains(@alt,'{username}')]","//header//button[.//img[contains(@alt,'Profile')or contains(@alt,'Профиль')]]//img","//header//span[@role='link'][.//img[contains(@alt,'profile')]]//img"]
                for xp in xpath_list:
                    try:
                        elements=driver.find_elements(By.XPATH,xp)
                        for el in elements:
                            if el.is_displayed()and int(el.get_attribute("height")or 0)>20:avatar_img_el=el;print(f"Аватар найден по {xp}");break
                        if avatar_img_el:break
                    except Exception as e:print(f"Ошибка XPath {xp}: {e}")
                if avatar_img_el and avatar_img_el.is_displayed():
                    avatar_url_found=avatar_img_el.get_attribute("src")
                    if avatar_url_found:url_av=avatar_url_found;print(f"URL аватара: {url_av}");display_avatar_in_label(url_av,instagram_avatar_label,"Instagram")
                    else:print("Атрибут src пуст."); instagram_avatar_label.config(text="N/A",image='', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"]);instagram_avatar_label.image=None
                if not url_av:print("Аватар Instagram не найден.");instagram_avatar_label.config(text="N/A",image='', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"]);instagram_avatar_label.image=None
            except Exception as e:print(f"Общая ошибка поиска аватара: {e}");traceback.print_exc();instagram_avatar_label.config(text="N/A",image='',bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"]);instagram_avatar_label.image=None
        elif"challenge"in url_page:update_status("Insta: Проверка.");messagebox.showwarning("Insta","Требуется проверка.");reset_login_ui("instagram")
        else:update_status("Insta: Ошибка входа.");messagebox.showerror("Insta","Не удалось войти.");reset_login_ui("instagram")
    except Exception as e:messagebox.showerror("Insta Ошибка",f"{e}");update_status(f"Insta: Ошибка: {type(e).__name__}");traceback.print_exc();reset_login_ui("instagram")

def login_to_youtube():
    global driver, is_youtube_logged_in, current_theme_colors
    if is_youtube_logged_in: return
    if not init_driver():return
    email = youtube_email_entry.get()
    password = youtube_password_entry.get()
    if not email or not password: messagebox.showerror("Ошибка (YouTube)", "Введите Email и Пароль."); return
    try:
        driver.get(YOUTUBE_LOGIN_URL);update_status("YouTube: Загрузка...");time.sleep(2)
        email_xpath="//input[@type='email' or @name='identifier']";next_xpath="//button[.//span[contains(text(),'Next')or contains(text(),'Далее')]]|//div[@id='identifierNext']//button"
        email_f=WebDriverWait(driver,15).until(EC.presence_of_element_located((By.XPATH,email_xpath)));email_f.send_keys(email);time.sleep(0.5)
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,next_xpath))).click();update_status("YouTube: Email введен...");time.sleep(2)
        pass_xpath="//input[@type='password' or @name='Passwd' or @name='password']";pass_next_xpath="//button[.//span[contains(text(),'Next')or contains(text(),'Далее')]]|//div[@id='passwordNext']//button"
        pass_f=WebDriverWait(driver,15).until(EC.presence_of_element_located((By.XPATH,pass_xpath)));pass_f.send_keys(password);time.sleep(0.5)
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,pass_next_xpath))).click();update_status("YouTube: Пароль введен/Ожидание 2FA...")
        time.sleep(10)
        if "accounts.google.com" not in driver.current_url and ("youtube.com" in driver.current_url or "myaccount.google.com" in driver.current_url) :
            update_status("YouTube: Вход выполнен (?).");messagebox.showinfo("Вход (YouTube)","Вход выполнен!")
            is_youtube_logged_in=True;youtube_login_button.config(text="Выйти из YouTube",command=lambda:logout_from("youtube"))
            try:
                if "youtube.com" not in driver.current_url: driver.get("https://www.youtube.com"); time.sleep(3)
                avatar_el_yt=None;url_ytav=None;yt_selectors=["//img[@id='img' and contains(@alt,'Avatar')]", "//button[@id='avatar-btn']//img", "ytd-topbar-menu-button-renderer img.yt-img-shadow"]
                for xp in yt_selectors:
                    try:
                        elements=driver.find_elements(By.CSS_SELECTOR if "img.yt-img-shadow" in xp else By.XPATH, xp)
                        for el in elements:
                            if el.is_displayed():avatar_el_yt=el;break
                        if avatar_el_yt:break
                    except:pass
                if avatar_el_yt:url_ytav=avatar_el_yt.get_attribute("src");
                if url_ytav:display_avatar_in_label(url_ytav,youtube_avatar_label,"YouTube")
                else:print("YT Аватар не найден.");youtube_avatar_label.config(text="N/A",image='', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"])
            except Exception as e:print(f"Ошибка аватара YT: {e}");youtube_avatar_label.config(text="N/A",image='', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"])
        else:update_status("YouTube: Не удалось войти.");messagebox.showwarning("Вход (YouTube)","Не удалось войти/2FA?. Проверьте браузер.");reset_login_ui("youtube")
    except Exception as e:messagebox.showerror("Ошибка (YouTube)",f"{e}");update_status(f"YouTube: Ошибка: {type(e).__name__}");traceback.print_exc();reset_login_ui("youtube")

def login_to_tiktok():
    global driver, is_tiktok_logged_in, current_theme_colors
    if is_tiktok_logged_in: return
    if not init_driver():return
    username = tiktok_username_entry.get()
    password = tiktok_password_entry.get()
    if not username or not password: messagebox.showerror("Ошибка (TikTok)", "Введите данные."); return
    try:
        driver.get(TIKTOK_LOGIN_URL);update_status("TikTok: Загрузка...");time.sleep(4)
        tab_sels=["//div[p/span[text()='Use phone / email / username']]","//div[contains(text(),'Log in with email or username')]","//a[contains(text(),'Use email / username')]","//div[text()='Email / Username']"];email_tab=None
        for sel in tab_sels:
            try:email_tab=WebDriverWait(driver,7).until(EC.element_to_be_clickable((By.XPATH,sel)));break
            except:pass
        if email_tab:email_tab.click();time.sleep(1.5)
        else:print("WARNING: TikTok tab not found.");
        user_xpaths=["//input[@name='username']","//input[@type='text' and contains(@placeholder,'Email')or contains(@placeholder,'username')]","//input[@aria-label='Email or username']"];user_field=None
        for xp in user_xpaths:
            try:user_field=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,xp)));break
            except:pass
        if not user_field:raise Exception("Поле username TikTok не найдено")
        user_field.send_keys(username);time.sleep(0.5)
        pass_xpaths=["//input[@name='password']","//input[@type='password']","//input[contains(@placeholder,'Password')]","//input[@aria-label='Password']"];pass_field=None
        for xp in pass_xpaths:
            try:pass_field=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,xp)));break
            except:pass
        if not pass_field:raise Exception("Поле password TikTok не найдено")
        pass_field.send_keys(password);time.sleep(0.5)
        btn_xpaths=["//button[@type='submit' and(contains(.,'Log in')or contains(.,'Войти'))]","//button[@data-e2e='login-button']"];login_btn=None
        for xp in btn_xpaths:
            try:login_btn=WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.XPATH,xp)));break
            except:pass
        if not login_btn:raise Exception("Кнопка login TikTok не найдена")
        login_btn.click();update_status("TikTok: Вход...");time.sleep(8)
        if"tiktok.com"in driver.current_url and"login"not in driver.current_url and"error"not in driver.current_url:
            update_status("TikTok: Вход (?).");messagebox.showinfo("Вход (TikTok)","Вход (?) выполнен! Проверьте браузер, если есть сомнения.")
            is_tiktok_logged_in=True;tiktok_login_button.config(text="Выйти из TikTok",command=lambda:logout_from("tiktok"))
            try:
                avatar_el_tk=None;url_tkav=None
                uname_url=username.split('@')[-1] if '@' in username else username # Исправлено
                selectors=[f"//header//a[contains(@href,'@{uname_url}')]//img","//header//div[contains(@class,'-avatar')]//img","//img[contains(@class,'tiktok-avatar')]", "span[data-e2e='user-avatar'] img"]
                for sel in selectors:
                    try:
                        cands=driver.find_elements(By.XPATH,sel)
                        for cand in cands:
                            if cand.is_displayed()and int(cand.get_attribute('width')or 0)>20:avatar_el_tk=cand;break
                        if avatar_el_tk:break
                    except:pass
                if avatar_el_tk:url_tkav=avatar_el_tk.get_attribute("src")
                if url_tkav:display_avatar_in_label(url_tkav,tiktok_avatar_label,"TikTok")
                else:print("TikTok аватар не найден."); tiktok_avatar_label.config(text="N/A",image='', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"])
            except Exception as e:print(f"Ошибка аватара TikTok: {e}"); tiktok_avatar_label.config(text="N/A",image='', bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"])
        else:update_status("TikTok: Ошибка/CAPTCHA.");messagebox.showwarning("Вход (TikTok)","Не удалось войти/проверка CAPTCHA. Проверьте браузер.");reset_login_ui("tiktok")
    except Exception as e:messagebox.showerror("Ошибка (TikTok)",f"{e}");update_status(f"TikTok: Ошибка: {type(e).__name__}");traceback.print_exc();reset_login_ui("tiktok")

def get_post_links_from_profile(profile_url):
    global driver
    if not driver: messagebox.showerror("Ошибка", "Драйвер не запущен."); return []
    driver.get(profile_url);update_status(f"Insta: Загрузка {profile_url[:40]}...");WebDriverWait(driver,15).until(lambda d:d.execute_script('return document.readyState')=='complete');time.sleep(3)
    SCROLL_T=3;MAX_P=30;urls=set();update_progress(0,MAX_P)
    try:last_h=driver.execute_script("return document.body.scrollHeight")
    except Exception as e:print(f"Insta Err: {e}");messagebox.showerror("Insta Err","Высота?");return[]
    scroll_att=0;MAX_NO=3
    while len(urls)<MAX_P:
        cnt=len(urls);soup=BeautifulSoup(driver.page_source,"html.parser")
        for a in soup.find_all("a",href=True):
            hr=a["href"]
            if re.match(r"^/(p|reel)/[\w-]+/?$",hr):urls.add("https://www.instagram.com"+hr);update_progress(len(urls),MAX_P)
            if len(urls)>=MAX_P:break
        if len(urls)>=MAX_P:update_status(f"Insta: Лимит {MAX_P}.");break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);");time.sleep(SCROLL_T)
        try:new_h=driver.execute_script("return document.body.scrollHeight")
        except Exception:break
        if new_h==last_h:
            if len(urls)==cnt:scroll_att+=1
            else:scroll_att=0
            if scroll_att>=MAX_NO:update_status(f"Insta: Прокрутка ({len(urls)}).");break
        else:scroll_att=0
        last_h=new_h;update_status(f"Insta: Ссылок: {len(urls)}...")
    update_progress_indeterminate(stop=True);update_progress(len(urls),MAX_P,finished=True)
    if not urls:
        msg="Insta: Ссылки не найдены.";txt=driver.page_source.lower()
        if"no posts yet"in txt or"нет публикаций"in txt:msg="Insta: Нет публикаций."
        elif"this account is private"in txt or"закрытый аккаунт"in txt:msg="Insta: Приватный."
        messagebox.showinfo("Insta Инфо",msg);update_status("Insta: Ссылки не найдены.")
    return list(urls)[:MAX_P]

def extract_instagram_media_urls(insta_post_url):
    global driver
    if not driver: messagebox.showerror("Ошибка", "Драйвер не запущен."); return []
    media_list=[];p_source=""
    try:driver.get(insta_post_url);WebDriverWait(driver,20).until(lambda d:d.execute_script('return document.readyState')=='complete');time.sleep(5)
    except Exception as e:print(f"Insta Err Load {insta_post_url}: {e}");return[]
    try:p_source=driver.page_source;soup=BeautifulSoup(p_source,"html.parser")
    except Exception as e:print(f"Insta Err Source: {e}");return[]
    try:s_area=soup.find('article')or soup;v_tags=s_area.find_all("video",src=True)
    except Exception as e:print(f"Insta Err Find <video>: {e}");v_tags=[]
    for v in v_tags:
        try: src = v.get("src")
        except Exception as e: print(f"Error extracting src from video tag: {e}"); src = None
        if src and src.startswith("http")and not any(i[0]==src for i in media_list):print(f"DEBUG: Insta <video>: {src[:60]}");media_list.append((src,"mp4"))
    scripts=soup.find_all("script",type="application/ld+json")
    for s in scripts:
        cont = s.string
        if not cont: continue
        try:
            data = json.loads(cont)
            if isinstance(data, list): data = data[0]
            def find_content_urls(item):
                urls = []
                if isinstance(item, dict):
                    if item.get("@type") == "VideoObject" and "contentUrl" in item:
                        if not any(u[0] == item["contentUrl"] for u in media_list): urls.append((item["contentUrl"], "mp4"))
                    if item.get("@type") == "ImageObject" and "contentUrl" in item:
                        if not any(u[0] == item["contentUrl"] for u in media_list): urls.append((item["contentUrl"], "jpg"))
                    if "image" in item and isinstance(item["image"], dict) and item["image"].get("@type") == "ImageObject" and "contentUrl" in item["image"]:
                        if not any(u[0] == item["image"]["contentUrl"] for u in media_list): urls.append((item["image"]["contentUrl"], "jpg"))
                    if "video" in item and isinstance(item["video"], dict) and item["video"].get("@type") == "VideoObject" and "contentUrl" in item["video"]:
                        if not any(u[0] == item["video"]["contentUrl"] for u in media_list): urls.append((item["video"]["contentUrl"], "mp4"))
                    for key_item in item: # Исправлено: key -> key_item
                        if isinstance(item[key_item], (dict, list)): # Проверка, что это итерируемый объект для рекурсии
                           urls.extend(find_content_urls(item[key_item]))
                elif isinstance(item, list):
                    for sub_item in item: urls.extend(find_content_urls(sub_item))
                return urls
            media_list.extend(find_content_urls(data))
        except Exception as e:print(f"Insta Err JSON-LD {insta_post_url}: {e}")
    try:
        og_v=soup.find("meta",property="og:video")
        url_ogv = None # Инициализация
        if og_v and og_v.get("content"): url_ogv=og_v["content"].replace("&amp;", "&") # Декодируем HTML entity
        if url_ogv and not any(i[0]==url_ogv for i in media_list): media_list.append((url_ogv,"mp4"))

        og_i=soup.find_all("meta",property="og:image")
        for tag in og_i:
            url_ogi = None # Инициализация
            if tag.get("content"): url_ogi=tag["content"].replace("&amp;", "&") # Декодируем HTML entity
            if url_ogi and not any(i[0]==url_ogi for i in media_list): media_list.append((url_ogi,"jpg"))
    except Exception as e:print(f"Insta Err OG: {e}")

    if not media_list or (len(media_list)==1 and media_list[0][1]=="jpg" and ("/p/" in insta_post_url or "/reel/" in insta_post_url)):
        try:
            img_area=soup.find('article') or soup
            img_tags_direct = img_area.find_all("img", {"src": True, "style": lambda x: "object-fit: cover;" in x if x else False})
            if not img_tags_direct: img_tags_direct = img_area.find_all("img", {"src": True})
            carousel_imgs=[]
            for img in img_tags_direct:
                src=img.get("src"); srcset=img.get("srcset")
                if srcset:
                    sources=[s.strip().split(" ")[0] for s in srcset.split(",") if s.strip()]
                    if sources: src = sources[-1]
                if src and src.startswith("https://scontent") and "150x150" not in src and "64x64" not in src and "_n.jpg" in src:
                    cleaned_src = src.split('?')[0]
                    is_new=True
                    for ex_url,_ in media_list+carousel_imgs:
                        if cleaned_src in ex_url or ex_url in cleaned_src:is_new=False;break
                    if is_new:carousel_imgs.append((src,"jpg"))
            if carousel_imgs:
                is_video_present = any(item[1] == "mp4" for item in media_list)
                if not is_video_present:
                    if len(media_list) == 1 and media_list[0][1] == "jpg":
                        og_base = media_list[0][0].split('?')[0]
                        temp_list = []
                        for p_url, p_ext in carousel_imgs:
                            if og_base not in p_url.split('?')[0]:
                                if not any(i[0].split('?')[0] == p_url.split('?')[0] for i in media_list + temp_list):
                                    temp_list.append((p_url, p_ext))
                        if temp_list: media_list.extend(temp_list)
                    elif not media_list: media_list.extend(carousel_imgs)
                else:
                    for p_url,p_ext in carousel_imgs:
                        if not any(i[0].split('?')[0]==p_url.split('?')[0]for i in media_list):media_list.append((p_url,p_ext))
        except Exception as e:print(f"Insta Err fallback image: {e}")
    final_list=[];seen=set()
    for url_f,ext_f in media_list:
        if url_f not in seen:final_list.append((url_f,ext_f));seen.add(url_f)
    if not final_list:print(f"Insta медиа не найдены: {insta_post_url}.")
    return final_list

def extract_tiktok_video_url(tiktok_post_url):
    global driver
    if not driver: messagebox.showerror("Ошибка", "Драйвер не запущен."); return []
    media_list=[];page_source=""
    try:update_status(f"TikTok: Загрузка: {tiktok_post_url[-25:]}...");driver.get(tiktok_post_url);update_status(f"TikTok: Загружен.");wait_timeout=25
    except Exception as e:print(f"КРИТ TikTok get URL {tiktok_post_url}: {e}");traceback.print_exc();return[]
    try:WebDriverWait(driver,wait_timeout).until(EC.presence_of_element_located((By.XPATH,"//video | //div[@data-e2e='video-desc'] | //div[contains(@class,'DivPlayerContainer')] | //div[contains(@class,'xgplayer')] | //script[@id='SIGI_STATE']")))
    except TimeoutException:print(f"WARNING: Таймаут ({wait_timeout}с) TikTok.")
    try:time.sleep(7);page_source=driver.page_source;soup=BeautifulSoup(page_source,"html.parser")
    except Exception as e:print(f"КРИТ TikTok get source {tiktok_post_url}: {e}");traceback.print_exc();return[]
    try:
        video_tags=soup.find_all("video",src=True)
        for tag in video_tags:src=tag.get("src");
        if src and src.startswith("http")and not any(i[0]==src for i in media_list):media_list.append((src,"mp4"));print(f"INFO: TikTok <video>: {src[:60]}...")
        selectors=["script#SIGI_STATE","script#RENDER_DATA","script#NEXT_DATA"];found_json=False
        for sel in selectors:
            try:
                tag_sel=soup.select_one(sel);
                if tag_sel and tag_sel.string:
                    data=json.loads(tag_sel.string)
                    def find_urls_in_tiktok_json(o):
                        urls_found=[];
                        if isinstance(o,dict):
                            for k,v in o.items():
                                if isinstance(v,str):
                                    if ("tiktokcdn.com" in v or "tiktokv.com" in v) and (".mp4" in v or "video_id" in v) and "watermark=1" not in v and "詡" not in v:
                                        try: v_decoded = bytes(v, 'utf-8').decode('unicode_escape')
                                        except: v_decoded = v
                                        if not any(i[0]==v_decoded for i in media_list + urls_found): urls_found.append(v_decoded)
                                elif k in['playAddr','downloadAddr', 'videoUrl']and isinstance(v,str) and ("tiktokcdn.com" in v or "tiktokv.com" in v) and "watermark=1" not in v and "詡" not in v:
                                    try: v_decoded = bytes(v, 'utf-8').decode('unicode_escape')
                                    except: v_decoded = v
                                    if not any(i[0]==v_decoded for i in media_list + urls_found): urls_found.append(v_decoded)
                                elif isinstance(v,(dict,list)):urls_found.extend(find_urls_in_tiktok_json(v))
                        elif isinstance(o,list):
                            for i_item in o:urls_found.extend(find_urls_in_tiktok_json(i_item))
                        return list(set(urls_found))
                    urls_json=find_urls_in_tiktok_json(data)
                    for url_item in urls_json:
                        if not any(i[0]==url_item for i in media_list):
                            media_list.append((url_item,"mp4"));print(f"INFO: TikTok JSON ({sel}): {url_item[:60]}...");found_json=True
                    if found_json and media_list:break
            except Exception as e:print(f"DEBUG: TikTok JSON parse ({sel}): {e}")
        if not media_list:
            matches=re.findall(r'"(https?://(?:v\d{1,2}[^.]*\.(?:tiktokcdn|tiktokv)\.com/[^"]+|[^"]*tiktokcdn\.com/video/tos/[^"]+)"',page_source)
            for url_match in matches:
                try: url_dec=bytes(url_match, 'utf-8').decode('unicode_escape')
                except: url_dec = url_match
                if (".mp4" in url_dec or "obj_type=video" in url_dec) and "watermark=1" not in url_dec and "詡" not in url_dec and "preview" not in url_dec:
                    if not any(i[0]==url_dec for i in media_list):media_list.append((url_dec,"mp4"));print(f"INFO: TikTok Regex: {url_dec[:60]}...")
    except Exception as e:print(f"КРИТ парсинга TikTok {tiktok_post_url}: {e}");traceback.print_exc();return[]
    if not media_list:print(f"INFO: Медиа TikTok не найдены: {tiktok_post_url}.")
    unique=[];seen_bases=set()
    for url_s,ext_s in sorted(media_list,key=lambda x:len(x[0]),reverse=True):
        base=url_s.split('?')[0];
        if base not in seen_bases:unique.append((url_s,ext_s));seen_bases.add(base)
    return unique[:1]

def extract_youtube_info(youtube_url):
    if not pytube:return[]
    try:
        yt=pytube.YouTube(youtube_url);streams=yt.streams.filter(progressive=True,file_extension='mp4').order_by('resolution').desc()
        media_items=[];title=yt.title;thumbnail_url=yt.thumbnail_url
        if not streams:print("INFO: No progressive MP4 YT.");media_items.append({"title":title,"thumbnail_url":thumbnail_url,"resolution":"N/A","url":youtube_url,"stream":None,"video_id":yt.video_id,"platform":"youtube","ext":"mp4"})
        else:
            added_res=set()
            for stream in streams:
                if stream.resolution not in added_res:media_items.append({"title":title,"thumbnail_url":thumbnail_url,"resolution":stream.resolution,"url":stream.url,"stream":None,"video_id":yt.video_id,"platform":"youtube","ext":"mp4"});added_res.add(stream.resolution)
        return media_items
    except PytubeError as e:print(f"Ошибка Pytube {youtube_url}: {e}");messagebox.showerror("Ошибка YouTube",f"{e}");return[]
    except Exception as e:print(f"Общая ошибка YouTube {youtube_url}: {e}");messagebox.showerror("Ошибка YouTube",f"{e}");return[]

async def async_send_telegram_file(bot_token,chat_id,file_path,caption=""):
    bot=aiogram.Bot(token=bot_token);file_sent=False
    try:
        _,ext=os.path.splitext(file_path);ext=ext.lower();input_file=FSInputFile(file_path)
        print(f"INFO: Aiogram - Sending {ext} to {chat_id}...");update_status(f"TG: Отправка {os.path.basename(file_path)}...")
        if ext in['.jpg','.jpeg','.png','.webp']:await bot.send_photo(chat_id=chat_id,photo=input_file,caption=caption)
        elif ext in['.mp4','.avi','.mov','.mkv']:await bot.send_video(chat_id=chat_id,video=input_file,caption=caption)
        else:await bot.send_document(chat_id=chat_id,document=input_file,caption=caption)
        print(f"INFO: Aiogram - Sent {os.path.basename(file_path)} to {chat_id}");file_sent=True
    except TelegramNotFound as e:print(f"ERROR: Aiogram - Chat not found: {e}");messagebox.showerror("TG Error",f"Чат '{chat_id}' не найден.");update_status("TG Error: Чат не найден.")
    except TelegramBadRequest as e:print(f"ERROR: Aiogram - Bad Request: {e}");messagebox.showerror("TG Error",f"Неверный запрос: {e}");update_status("TG Error: Неверный запрос.")
    except TelegramForbiddenError as e:print(f"ERROR: Aiogram - Forbidden: {e}");messagebox.showerror("TG Error",f"Доступ запрещен '{chat_id}': {e}");update_status("TG Error: Доступ запрещен.")
    except TelegramAPIError as e:
        print(f"ERROR: Aiogram - API Error: {e}");msg=f"{e}";limit_msg="File is too big";
        if limit_msg in str(e).lower():msg=limit_msg;update_status("TG Error: Файл большой.")
        else:update_status(f"TG Error: API {type(e).__name__}")
        messagebox.showerror("TG Error",f"Ошибка API Telegram: {msg}")
    except Exception as e:print(f"ERROR: Aiogram - Send Error: {e}");messagebox.showerror("TG Error",f"{e}");update_status(f"TG Error: {type(e).__name__}");traceback.print_exc()
    finally:
        try:await bot.session.close();print("INFO: Aiogram - Session closed.")
        except Exception as e:print(f"ERROR: Aiogram - Session close error: {e}")
    return file_sent

def run_telegram_send_sync(file_path,caption=""):
    if not aiogram:update_status("Ошибка: Aiogram не импортирован.");print("ERROR: aiogram module not available.");return False
    bot_token = app_settings.get("telegram_token")
    chat_id = app_settings.get("telegram_chat_id")
    if not bot_token or not chat_id:messagebox.showerror("TG Error","Токен/ID чата не настроены (Файл->Настройки).");update_status("TG Error: Нет токена/ID.");return False
    update_status(f"TG: Подготовка {os.path.basename(file_path)}...");result=False
    try:result=asyncio.run(async_send_telegram_file(bot_token,chat_id,file_path,caption))
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(async_send_telegram_file(bot_token, chat_id, file_path, caption))
            except Exception as e_nest:
                 print(f"ERROR: asyncio nested run: {e_nest}");messagebox.showerror("Asyncio Error",f"Ошибка вложенного запуска: {e_nest}");update_status("TG Error: asyncio nested.");return False
        else:
            print(f"ERROR: asyncio runtime: {e}");messagebox.showerror("Asyncio Error",f"{e}");update_status("TG Error: asyncio.");return False
    except Exception as e:print(f"ERROR: TG sync wrapper: {e}");messagebox.showerror("TG Error",f"{e}");update_status("TG Error: Общая.");traceback.print_exc();return False
    if result:update_status(f"TG: Файл {os.path.basename(file_path)} отправлен.")
    else:update_status(f"TG: Ошибка отправки {os.path.basename(file_path)}.")
    return result

# --- Discord Webhook Functions ---
def send_discord_webhook_file_sync(file_path, caption=""):
    webhook_url = app_settings.get("discord_webhook_url")
    if not webhook_url:
        messagebox.showerror("Discord Error", "URL Discord Webhook не настроен (Файл->Настройки).")
        update_status("Discord Error: Нет Webhook URL.")
        return False

    if not os.path.exists(file_path):
        print(f"Файл не найден для Discord: {file_path}")
        update_status(f"Discord Error: Файл {os.path.basename(file_path)} не найден.")
        return False

    update_status(f"Discord: Подготовка {os.path.basename(file_path)}...")
    file_name = os.path.basename(file_path)
    discord_caption = caption if caption else f"Файл: {file_name}"

    files_payload = None
    fp_to_close = None # Для корректного закрытия файла
    sent = False

    try:
        fp_to_close = open(file_path, 'rb')
        files_payload = {'file': (file_name, fp_to_close)}
        data_payload = {"content": discord_caption}

        print(f"INFO: Discord Webhook - Sending {file_name}...")
        update_status(f"Discord: Отправка {file_name}...")
        response = requests.post(webhook_url, files=files_payload, data=data_payload, timeout=180)
        response.raise_for_status()
        print(f"INFO: Discord Webhook - Sent {file_name}. Status: {response.status_code}")
        sent = True
    except requests.exceptions.HTTPError as err:
        error_message = f"HTTP Error: {err.response.status_code} - {err.response.reason}"
        try:
            error_details = err.response.json()
            error_message += f"\nDetails: {json.dumps(error_details, indent=2)}"
            if "message" in error_details and "code" in error_details:
                 if error_details.get("code") == 40005 or (isinstance(error_details.get("errors"), dict) and ".UPLOAD_TOO_LARGE" in str(error_details.get("errors"))): # Request entity too large
                     error_message = "Файл слишком большой для Discord Webhook (лимит ~8MB или 25MB для Nitro-бущенных серверов)."
        except json.JSONDecodeError:
            error_message += f"\nResponse body: {err.response.text}"

        print(f"ERROR: Discord Webhook - {error_message}")
        messagebox.showerror("Discord Error", f"Ошибка API Discord Webhook: {error_message}")
        update_status("Discord Error: Ошибка API.")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Discord Webhook - Request Error: {e}")
        messagebox.showerror("Discord Error", f"Ошибка сети при отправке в Discord: {e}")
        update_status("Discord Error: Ошибка сети.")
        traceback.print_exc()
    except Exception as e:
        print(f"ERROR: Discord Webhook - Send Error: {e}")
        messagebox.showerror("Discord Error", f"Неизвестная ошибка при отправке в Discord: {e}")
        update_status("Discord Error: Общая.")
        traceback.print_exc()
    finally:
        if fp_to_close: # Закрываем файл, если он был открыт
            fp_to_close.close()

    if sent:
        update_status(f"Discord: Файл {file_name} отправлен.")
    else:
        update_status(f"Discord: Ошибка отправки {file_name}.")
    return sent

# --- Gemini Interaction ---
def ask_gemini_api(question):
    print(f"Вопрос Gemini: {question}")
    hardcoded_api_key = "AIzaSyAZqoRPw1gMVfcQOqvDAl9evj1vxaSFcV4"
    if not question: return "Пожалуйста, введите вопрос."
    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={hardcoded_api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": question}]}]}
    try:
        response = requests.post(gemini_api_url, headers=headers, json=data, timeout=180)
        response.raise_for_status()
        response_json = response.json()
        if "candidates" in response_json and \
           len(response_json["candidates"]) > 0 and \
           "content" in response_json["candidates"][0] and \
           "parts" in response_json["candidates"][0]["content"] and \
           len(response_json["candidates"][0]["content"]["parts"]) > 0 and \
           "text" in response_json["candidates"][0]["content"]["parts"][0]:
            return response_json["candidates"][0]["content"]["parts"][0]["text"]
        elif "promptFeedback" in response_json and "blockReason" in response_json["promptFeedback"]:
            block_reason = response_json["promptFeedback"]["blockReason"]
            block_message = f"Запрос к Gemini был заблокирован. Причина: {block_reason}."
            if "safetyRatings" in response_json["promptFeedback"]:
                try:
                    details = ", ".join([f"{rating['category'].split('/')[-1]}: {rating['probability']}" for rating in response_json["promptFeedback"]["safetyRatings"]])
                    block_message += f" Детали безопасности: {details}"
                except Exception as e_parse: print(f"Error parsing safety ratings: {e_parse}")
            return block_message
        else:
            print(f"DEBUG: Неожиданная структура ответа Gemini: {json.dumps(response_json, indent=2)}")
            return "Не удалось извлечь текстовый ответ из данных API Gemini."
    except requests.exceptions.HTTPError as http_err:
        error_message = f"Ошибка HTTP API Gemini: {http_err.response.status_code}"
        try:
            error_details_json = http_err.response.json()
            if "error" in error_details_json and "message" in error_details_json["error"]:
                error_message += f"\nПодробности: {error_details_json['error']['message']}"
            else: error_message += f"\nТело ответа: {http_err.response.text}"
        except json.JSONDecodeError: error_message += f"\nТело ответа (не JSON): {http_err.response.text}"
        except Exception: pass
        print(error_message)
        return error_message
    except requests.exceptions.RequestException as req_err:
        print(f"Ошибка запроса к API Gemini: {req_err}"); return f"Ошибка подключения к API Gemini: {req_err}"
    except Exception as e:
        print(f"Непредвиденная ошибка при обращении к Gemini: {e}"); traceback.print_exc()
        return f"Непредвиденная ошибка при обработке запроса Gemini: {e}"

def handle_ask_gemini_thread_target():
    question = gemini_question_text.get("1.0", tk.END).strip()
    if not question: messagebox.showinfo("Gemini", "Введите вопрос."); return
    update_status("Gemini: Обработка запроса...");
    gemini_answer_text.config(state=tk.NORMAL)
    gemini_answer_text.delete("1.0",tk.END)
    gemini_answer_text.insert(tk.END,"Отправка запроса к Gemini API...")
    gemini_answer_text.config(state=tk.DISABLED); root.update_idletasks()
    try:
        response_text = ask_gemini_api(question)
        gemini_answer_text.config(state=tk.NORMAL); gemini_answer_text.delete("1.0",tk.END); gemini_answer_text.insert(tk.END,response_text); gemini_answer_text.config(state=tk.DISABLED)
        update_status("Gemini: Ответ получен.")
    except Exception as e:
        gemini_answer_text.config(state=tk.NORMAL); gemini_answer_text.delete("1.0",tk.END); gemini_answer_text.insert(tk.END,f"Критическая ошибка в потоке Gemini: {e}"); gemini_answer_text.config(state=tk.DISABLED)
        update_status("Gemini: Критическая ошибка."); traceback.print_exc()

def handle_ask_gemini():
    threading.Thread(target=handle_ask_gemini_thread_target, daemon=True).start()

# --- Core Fetch/Download Logic ---
def fetch_media_urls_thread_entry():
    global media_urls_checkboxes;media_urls_checkboxes.clear()
    for widget in result_frame_content.winfo_children():widget.destroy()
    input_url_val=url_entry.get().strip()
    if not input_url_val:messagebox.showerror("Ошибка","Введите ссылку!");update_status("Ошибка: URL не введен.");return
    update_status("Начало обработки...");update_progress_indeterminate(start=True);all_media_items_data=[]
    try:
        if any(yt_prefix in input_url_val for yt_prefix in ["youtube.com/", "youtu.be/"]):
            if not pytube:raise ImportError("Pytube не импортирован.")
            update_status(f"YouTube: Обработка... {input_url_val[-20:]}");yt_media_info_list=extract_youtube_info(input_url_val)
            for item_info in yt_media_info_list:all_media_items_data.append(item_info)
        elif re.match(r"https://(www\.)?instagram\.com/(p|reel|tv|stories)/[\w-]+/?",input_url_val):
            if "/stories/" in input_url_val and "/highlights/" not in input_url_val:
                messagebox.showinfo("Инфо","Скачивание отдельных Instagram Stories в данный момент не полностью поддерживается.");
                update_status("Insta Stories: Ограниченная поддержка."); update_progress_indeterminate(stop=True); return
            if not driver:messagebox.showerror("Ошибка","Драйвер не запущен (Insta).");update_progress_indeterminate(stop=True);return
            update_status(f"Instagram: Пост... {input_url_val[-25:]}");media_items=extract_instagram_media_urls(input_url_val)
            for url_item,ext_item in media_items:all_media_items_data.append({"url":url_item,"ext":ext_item,"original_url":input_url_val,"platform":"instagram"})
        elif re.match(r"https://(www\.)?instagram\.com/([a-zA-Z0-9_.]+)/?$",input_url_val)and"/p/"not in input_url_val and"/reel/"not in input_url_val and"/tv/"not in input_url_val and"/stories/"not in input_url_val:
            if not driver:messagebox.showerror("Ошибка","Драйвер не запущен (Insta профиль).");update_progress_indeterminate(stop=True);return
            if"/stories/highlights/"in input_url_val:messagebox.showinfo("Инфо","Highlights не подд.");update_status("Highlights не подд.");update_progress_indeterminate(stop=True);return
            update_status("Instagram: Профиль. Сбор...");post_links=get_post_links_from_profile(input_url_val)
            if not post_links:update_status("Insta: Посты не найдены.");update_progress_indeterminate(stop=True);return
            total_posts=len(post_links)
            for i,link_url_item in enumerate(post_links):
                update_status(f"Instagram: {i+1}/{total_posts}: ...{link_url_item.split('/')[-2 if link_url_item.endswith('/')else -1]}")
                update_progress(i+1,total_posts);media_items=extract_instagram_media_urls(link_url_item)
                for url_item,ext_item in media_items:all_media_items_data.append({"url":url_item,"ext":ext_item,"original_url":link_url_item,"platform":"instagram"})
            update_progress(total_posts,total_posts,finished=True)
        elif re.match(r"https://(www\.|vm\.)?tiktok\.com/(@[\w.-]+/video/\d+|t/\w+|[\w.-]+)",input_url_val):
            if not driver:messagebox.showerror("Ошибка","Драйвер не запущен (TikTok).");update_progress_indeterminate(stop=True);return
            actual_url_val=input_url_val
            if "vm.tiktok.com"in input_url_val or "/t/" in input_url_val:
                try:update_status(f"TikTok: Раскрытие короткой ссылки...");response=requests.get(input_url_val,allow_redirects=True,timeout=15, headers={'User-Agent': 'Mozilla/5.0'});actual_url_val=response.url
                except requests.RequestException as e:messagebox.showerror("TikTok Ошибка",f"Не удалось раскрыть ссылку: {e}");update_status("TikTok: Ошибка раскрытия.");update_progress_indeterminate(stop=True);return
                if"login"in actual_url_val or"error"in actual_url_val or "tiktok.com" not in actual_url_val :messagebox.showwarning("TikTok","Ссылка раскрылась на страницу входа/ошибки или не является TikTok видео.");update_status("TikTok: Ошибка раскрытия в корректную ссылку.");update_progress_indeterminate(stop=True);return
            update_status(f"TikTok: Видео... {actual_url_val[-35:]}");media_items=extract_tiktok_video_url(actual_url_val)
            for url_item,ext_item in media_items:all_media_items_data.append({"url":url_item,"ext":ext_item,"original_url":actual_url_val,"platform":"tiktok"})
        else:messagebox.showerror("Ошибка","Неверный формат ссылки или платформа не поддерживается (Insta, TikTok, YouTube).");update_status("Ошибка: Неверный URL.");update_progress_indeterminate(stop=True);return
        update_progress_indeterminate(stop=True)
        if not all_media_items_data:messagebox.showinfo("Пусто","Медиа не найдены для данной ссылки.");update_status("Готово. Медиа не найдены.");return
        for idx,data_item in enumerate(all_media_items_data):
            platform=data_item.get("platform","unknown");ext=data_item.get("ext","bin");original_url_item=data_item.get("original_url",input_url_val)
            fname=f"media_{idx}.{ext}";display_text=fname
            if platform=="instagram":match=re.search(r"/(p|reel|tv)/([^/]+)",original_url_item);pid=match.group(2)if match else f"insta_{idx}";fname=f"{pid}_{idx}.{ext}";display_text=f"{fname} (Instagram)"
            elif platform=="tiktok":match=re.search(r"/video/(\d+)",original_url_item);pid=f"tiktok_{match.group(1)if match else original_url_item.split('/')[-1].split('?')[0]}";fname=f"{pid}_{idx}.{ext}";display_text=f"{fname} (TikTok)"
            elif platform=="youtube":title=data_item.get('title','yt_video');res=data_item.get('resolution','N/A');vid=data_item.get('video_id',f"yt_{idx}");safe_title=re.sub(r'[\\/*?:"<>|]',"",title)[:50];fname=f"{safe_title}_{res}_{vid}.{ext}";display_text=f"{title} - {res} (YouTube)";data_item["filename"]=fname
            if "filename" not in data_item: data_item["filename"] = fname
            var=tk.BooleanVar(value=True);cb=ttk.Checkbutton(result_frame_content,text=display_text,variable=var,style='TCheckbutton');cb.var=var;cb.media_data=data_item;cb.pack(fill="x",padx=5,pady=2);media_urls_checkboxes.append(cb)
        result_frame_content.update_idletasks();canvas_for_results.configure(scrollregion=canvas_for_results.bbox("all"));update_status(f"Готово. Найдено медиа: {len(all_media_items_data)}.")
        apply_theme_to_all_widgets(result_frame_content)
    except ImportError as e:update_status(f"Ошибка импорта: {e}");update_progress_indeterminate(stop=True);messagebox.showerror("Ошибка библиотеки",f"{e}");
    except Exception as e:update_status(f"Крит. ошибка при получении медиа: {type(e).__name__}");update_progress_indeterminate(stop=True);messagebox.showerror("Крит. Ошибка",f"Произошла ошибка: {e}");traceback.print_exc()

def handle_download_and_send(send_tg=False, send_discord=False):
    selected_checkboxes=[cb for cb in media_urls_checkboxes if cb.var.get()]
    if not selected_checkboxes:messagebox.showinfo("Нет выбора","Файлы не выбраны.");update_status("Нет выбранных файлов.");return
    if send_tg and not aiogram:messagebox.showerror("Ошибка Telegram","Библиотека aiogram не установлена.");return
    thread=threading.Thread(target=download_send_worker,args=(selected_checkboxes,send_tg, send_discord),daemon=True);thread.start()

def download_send_worker(checkboxes_to_process, send_to_telegram_flag, send_to_discord_flag):
    save_dir="downloaded_media";os.makedirs(save_dir,exist_ok=True);total=len(checkboxes_to_process);downloaded_count=0;sent_tg_count=0; sent_discord_count=0
    update_status(f"Начало операции для {total} файлов...");update_progress(0,total)
    for i,cb in enumerate(checkboxes_to_process):
        media_data=cb.media_data;platform=media_data.get("platform");original_filename=media_data.get("filename",f"media_{platform}_{i}.{media_data.get('ext','bin')}")
        file_path_to_save=None;download_successful=False
        update_status(f"Обработка {i+1}/{total}: {original_filename[:50]}...");update_progress(i,total)
        try:
            base,ext=os.path.splitext(original_filename);count=1;temp_filename=original_filename
            temp_filename = re.sub(r'[\\/*?:"<>|\s]',"_",temp_filename)
            base = re.sub(r'[\\/*?:"<>|\s]',"_",base)
            while os.path.exists(os.path.join(save_dir,temp_filename)):temp_filename=f"{base}_{count}{ext}";count+=1
            file_path_to_save=os.path.join(save_dir,temp_filename)
            if platform=="youtube":
                if not pytube:raise ImportError("Pytube не импортирован для скачивания.")
                video_id=media_data.get("video_id");resolution=media_data.get("resolution")
                if not video_id:raise ValueError("Нет Video ID YouTube для скачивания.")
                print(f"INFO: YT - Re-fetch для скачивания: ID {video_id}, Res: {resolution}")
                yt_video_url = f"https://www.youtube.com/watch?v={video_id}"
                yt=pytube.YouTube(yt_video_url, use_oauth=False, allow_oauth_cache=False)
                stream=yt.streams.filter(progressive=True,file_extension='mp4',resolution=resolution).first()
                if not stream:stream=yt.streams.filter(progressive=True,file_extension='mp4').order_by('resolution').desc().first()
                if not stream:
                    print(f"WARNING: YT - Прогрессивный поток не найден для {video_id} ({resolution}). Попытка адаптивного (может требовать ffmpeg).")
                    stream = yt.streams.filter(adaptive=True, file_extension='mp4', resolution=resolution).first()
                    if not stream: stream = yt.streams.get_highest_resolution()
                if not stream:raise PytubeError(f"Не найден поток YouTube {video_id} ({resolution}).")
                print(f"INFO: YT - Скачивание потока: {stream.resolution}, {stream.mime_type}, progressive: {stream.is_progressive}")
                stream.download(output_path=save_dir,filename=temp_filename);download_successful=True
            elif platform in["instagram","tiktok"]:
                media_url_val=media_data.get("url");
                if not media_url_val:raise ValueError(f"Нет URL для скачивания {platform}.")
                headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                         'Referer':f'https://www.{platform}.com/'}
                response=requests.get(media_url_val,stream=True,timeout=120,headers=headers, allow_redirects=True);response.raise_for_status()
                with open(file_path_to_save,'wb')as f_out:
                    for chunk in response.iter_content(chunk_size=8192*4):f_out.write(chunk)
                download_successful=True
            else:print(f"WARNING: Неизвестная платформа для скачивания '{platform}'");continue
        except PytubeError as e_pytube: print(f"Ошибка Pytube при скачивании {original_filename}: {e_pytube}");update_status(f"Ошибка Pytube: {os.path.basename(original_filename)}");file_path_to_save=None;download_successful=False;traceback.print_exc()
        except requests.exceptions.RequestException as e_req: print(f"Ошибка Requests при скачивании {original_filename}: {e_req}");update_status(f"Ошибка сети: {os.path.basename(original_filename)}");file_path_to_save=None;download_successful=False;traceback.print_exc()
        except Exception as e_down:print(f"Ошибка скачивания {original_filename}: {e_down}");update_status(f"Ошибка скачивания: {os.path.basename(original_filename)}");file_path_to_save=None;download_successful=False;traceback.print_exc()

        if download_successful and file_path_to_save:
            downloaded_count+=1
            print(f"INFO: Файл успешно скачан: {file_path_to_save}")
            caption_text = os.path.basename(file_path_to_save)

            if send_to_telegram_flag:
                if run_telegram_send_sync(file_path_to_save,caption=caption_text):sent_tg_count+=1
                else:update_status(f"Ошибка отправки TG: {os.path.basename(file_path_to_save)}")

            if send_to_discord_flag:
                if send_discord_webhook_file_sync(file_path_to_save, caption=caption_text): sent_discord_count +=1
                else: update_status(f"Ошибка отправки Discord: {os.path.basename(file_path_to_save)}")

        elif not download_successful:
            print(f"FAIL: Не удалось скачать {original_filename}")
        update_progress(i+1,total)

    update_progress(total,total,finished=True)
    final_status=f"Завершено. Скачано: {downloaded_count}/{total}."
    if send_to_telegram_flag:final_status+=f" Отправлено в TG: {sent_tg_count}/{downloaded_count}."
    if send_to_discord_flag:final_status+=f" Отправлено в Discord: {sent_discord_count}/{downloaded_count}."

    if downloaded_count==total and \
       (not send_to_telegram_flag or sent_tg_count==downloaded_count) and \
       (not send_to_discord_flag or sent_discord_count==downloaded_count):
        messagebox.showinfo("Готово",final_status)
    else:
        messagebox.showwarning("Завершено с ошибками",final_status)
    update_status(final_status)

# --- GitHub Update Checker ---
def check_github_release_update_threaded():
    threading.Thread(target=check_github_release_update, daemon=True).start()

def check_github_release_update():
    global APP_VERSION, GITHUB_REPO_OWNER, GITHUB_REPO_NAME
    update_status("Проверка обновлений на GitHub...")
    if not packaging:
        messagebox.showerror("Ошибка", "Библиотека 'packaging' не найдена. Невозможно сравнить версии.")
        update_status("Ошибка: 'packaging' не найдена.")
        return

    if GITHUB_REPO_OWNER == "ВАШ_ПОЛЬЗОВАТЕЛЬ_GITHUB" or GITHUB_REPO_NAME == "ВАШ_РЕПОЗИТОРИЙ_GITHUB": # Исправлена опечатка GITHUB_REПО_NAME
        messagebox.showwarning("Настройка", "Пожалуйста, укажите GITHUB_REPO_OWNER и GITHUB_REPO_NAME в коде скрипта для проверки обновлений.")
        update_status("Проверка обновлений: не настроен репозиторий.")
        return

    github_api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"

    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(github_api_url, headers=headers, timeout=15)
        response.raise_for_status()
        latest_release_data = response.json()

        latest_tag_name = latest_release_data.get("tag_name", "").lstrip('v')
        release_notes = latest_release_data.get("body", "Описание отсутствует.")
        release_url = latest_release_data.get("html_url", f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases")

        if not latest_tag_name:
            update_status("Не удалось получить тег последнего релиза.")
            messagebox.showinfo("Обновления", "Не удалось получить информацию о последнем релизе.")
            return

        current_v = packaging.version.parse(APP_VERSION)
        latest_v = packaging.version.parse(latest_tag_name)

        if latest_v > current_v:
            info_msg = (f"Доступна новая версия: {latest_tag_name}!\n"
                        f"Ваша текущая версия: {APP_VERSION}\n\n"
                        f"Что нового:\n{release_notes}\n\n"
                        f"Перейти на страницу релиза?")
            if messagebox.askyesno("Обновление доступно!", info_msg):
                webbrowser.open_new_tab(release_url)
            update_status(f"Обновление {latest_tag_name} доступно.")
        else:
            messagebox.showinfo("Обновления", f"У вас установлена последняя версия: {APP_VERSION}")
            update_status("Последняя версия установлена.")

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            msg = "Релизы для данного репозитория не найдены на GitHub."
            messagebox.showinfo("Обновления", msg)
            update_status("Обновления: Релизы не найдены.")
        elif http_err.response.status_code == 403:
            msg = "Превышен лимит запросов к GitHub API. Попробуйте позже."
            messagebox.showwarning("Обновления", msg)
            update_status("Обновления: Превышен лимит GitHub API.")
        else:
            msg = f"Ошибка HTTP API GitHub: {http_err}"
            messagebox.showerror("Ошибка обновления", msg)
            update_status("Обновления: Ошибка API GitHub.")
        print(msg)
    except requests.exceptions.RequestException as e:
        msg = f"Ошибка сети при проверке обновлений: {e}"
        messagebox.showerror("Ошибка обновления", msg)
        update_status("Обновления: Ошибка сети.")
        print(msg)
    except packaging.version.InvalidVersion:
        msg = f"Некорректный формат версии: локальная '{APP_VERSION}' или удаленная '{latest_tag_name or 'N/A'}'"
        messagebox.showerror("Ошибка обновления", msg)
        update_status("Обновления: Ошибка формата версии.")
        print(msg)
    except Exception as e_gen:
        msg = f"Непредвиденная ошибка при проверке обновлений: {e_gen}"
        messagebox.showerror("Критическая ошибка", msg)
        update_status("Обновления: Неизвестная ошибка.")
        traceback.print_exc()
        print(msg)

# --- Theme Functions ---
def set_theme(theme_name):
    global current_theme_colors, app_settings
    if theme_name in THEMES:
        app_settings["theme"] = theme_name
        current_theme_colors = THEMES[theme_name]
        apply_theme_to_all_widgets(root)
        save_settings()
        update_status(f"Тема изменена на: {theme_name}")
    else:
        print(f"Тема '{theme_name}' не найдена.")

def apply_theme_to_all_widgets(parent_widget):
    global current_theme_colors, style, OS_BASE_THEME

    # Цвета для ttk стиля
    style.configure('.',
                    background=current_theme_colors["bg"],
                    foreground=current_theme_colors["fg"],
                    fieldbackground=current_theme_colors["entry_bg"],
                    selectbackground=current_theme_colors["accent_button_bg"],
                    selectforeground=current_theme_colors["accent_button_fg"])

    style.configure('TButton',
                    background=current_theme_colors["button_bg"],
                    foreground=current_theme_colors["button_fg"],
                    padding=5, font=('Segoe UI', 10))
    style.map('TButton',
              background=[('active', current_theme_colors["accent_button_bg"]), ('disabled', current_theme_colors["button_bg"])],
              foreground=[('disabled', current_theme_colors["disabled_fg"])])

    style.configure('Accent.TButton',
                    foreground=current_theme_colors["accent_button_fg"],
                    background=current_theme_colors["accent_button_bg"],
                    font=('Segoe UI', 10, 'bold'))
    style.map('Accent.TButton',
              background=[('active', THEMES['dark']['accent_button_bg'] if app_settings.get('theme', 'light') == 'dark' else THEMES['light']['accent_button_bg'])],
              foreground=[('disabled', current_theme_colors["disabled_fg"])])

    style.configure('TLabel',
                    background=current_theme_colors["bg"],
                    foreground=current_theme_colors["fg"],
                    font=('Segoe UI', 10))

    style.configure('TEntry',
                    fieldbackground=current_theme_colors["entry_bg"],
                    foreground=current_theme_colors["entry_fg"],
                    insertcolor=current_theme_colors["entry_insert"])

    style.configure('TCheckbutton',
                    background=current_theme_colors["bg"],
                    foreground=current_theme_colors["fg"],
                    indicatorcolor=current_theme_colors["fg"])
    style.map('TCheckbutton',
              indicatorcolor=[('selected', current_theme_colors["accent_button_bg"]), ('active', current_theme_colors["accent_button_bg"])],
              foreground=[('disabled', current_theme_colors["disabled_fg"])])

    style.configure('TLabelframe',
                    background=current_theme_colors["bg"],
                    bordercolor=current_theme_colors["fg"],
                    relief=current_theme_colors["relief"])
    style.configure('TLabelframe.Label',
                    background=current_theme_colors["bg"],
                    foreground=current_theme_colors["fg"],
                    font=('Segoe UI', 10, 'bold'))

    style.configure('TNotebook', background=current_theme_colors["bg"])
    style.configure('TNotebook.Tab',
                    background=current_theme_colors["notebook_tab_bg"],
                    foreground=current_theme_colors["notebook_tab_fg"],
                    padding=[5, 2], font=('Segoe UI', 9))
    style.map('TNotebook.Tab',
              background=[('selected', current_theme_colors["notebook_tab_selected_bg"])],
              foreground=[('selected', current_theme_colors["notebook_tab_selected_fg"])])

    style.configure('TScrollbar',
                    background=current_theme_colors["scrollbar_bg"],
                    troughcolor=current_theme_colors["scrollbar_trough"],
                    relief=current_theme_colors["relief"], borderwidth=1) # relief может быть не для всех тем ttk
    style.map('TScrollbar',arrowcolor=[('!disabled',current_theme_colors["fg"])])


    style.configure('TProgressbar',
                    background=current_theme_colors["progressbar_bg"],
                    troughcolor=current_theme_colors["progressbar_trough"],
                    thickness=15)
    
    style.configure('StatusBar.TFrame', background=current_theme_colors["status_bar_bg"], relief=current_theme_colors["relief"])


    parent_widget.configure(bg=current_theme_colors["bg"])

    widgets_to_style = []
    if parent_widget: # Добавлена проверка, что parent_widget существует
        widgets_to_style = list(parent_widget.winfo_children())


    if parent_widget == root and hasattr(parent_widget, 'config') and 'menu' in parent_widget.config():
        try:
            menu_path = parent_widget.cget('menu')
            if menu_path: # Убедимся, что путь к меню не пустой
                menu = parent_widget.nametowidget(menu_path)
                if menu:
                    # widgets_to_style.append(menu) # Не добавляем в общий список, стилизуем отдельно
                    def style_menu(m):
                        try:
                            m.configure(bg=current_theme_colors["menu_bg"],
                                        fg=current_theme_colors["menu_fg"],
                                        activebackground=current_theme_colors["accent_button_bg"],
                                        activeforeground=current_theme_colors["accent_button_fg"],
                                        relief=current_theme_colors["relief"],
                                        tearoffbackground=current_theme_colors["menu_bg"],
                                        selectcolor=current_theme_colors["accent_button_fg"])

                            for i in range(m.index('end') + 1 if m.index('end') is not None else 0):
                                entry_type = m.type(i)
                                if entry_type in ["cascade", "command", "checkbutton", "radiobutton"]:
                                    m.entryconfigure(i, background=current_theme_colors["menu_bg"],
                                                     foreground=current_theme_colors["menu_fg"],
                                                     activebackground=current_theme_colors["accent_button_bg"],
                                                     activeforeground=current_theme_colors["accent_button_fg"])
                                if entry_type == "cascade":
                                    submenu_name = m.entrycget(i, "menu")
                                    if submenu_name:
                                        submenu = m.nametowidget(submenu_name)
                                        style_menu(submenu)
                        except tk.TclError as e_menu:
                            # print(f"Не удалось полностью стилизовать меню {m}: {e_menu}")
                            pass
                    style_menu(menu)
        except tk.TclError as e_main_menu:
            # print(f"Ошибка при получении главного меню: {e_main_menu}")
            pass


    for widget in widgets_to_style:
        # Добавляем дочерние элементы в очередь только если они существуют
        try:
            if widget.winfo_exists():
                 widgets_to_style.extend(widget.winfo_children())
        except tk.TclError: # Виджет мог быть уничтожен
            continue


        widget_class = widget.winfo_class()

        try:
            if not widget.winfo_exists(): # Пропускаем уничтоженные виджеты
                continue

            if widget_class.startswith("T"):
                 pass # Уже в основном стилизовано

            elif widget_class == "Frame":
                widget.configure(bg=current_theme_colors["bg"])
            elif widget_class == "Label":
                widget.configure(bg=current_theme_colors["bg"], fg=current_theme_colors["fg"])
                if widget in [instagram_avatar_label, tiktok_avatar_label, youtube_avatar_label] and hasattr(widget, 'image') and not widget.image:
                     widget.configure(bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"])
                elif hasattr(widget, 'image') and widget.image:
                     widget.configure(bg="", relief="flat") # Убираем фон и рамку для картинки
            elif widget_class == "Entry":
                widget.configure(bg=current_theme_colors["entry_bg"], fg=current_theme_colors["entry_fg"],
                                 disabledbackground=THEMES[app_settings.get('theme', 'light')]['button_bg'],
                                 readonlybackground=THEMES[app_settings.get('theme', 'light')]['button_bg'],
                                 insertbackground=current_theme_colors["entry_insert"], relief=current_theme_colors["relief"])
            elif widget_class == "Button":
                widget.configure(bg=current_theme_colors["button_bg"], fg=current_theme_colors["button_fg"],
                                 activebackground=current_theme_colors["accent_button_bg"],
                                 activeforeground=current_theme_colors["accent_button_fg"],
                                 relief=current_theme_colors["relief"],
                                 disabledforeground=current_theme_colors["disabled_fg"])
            elif widget_class == "Text" or isinstance(widget, scrolledtext.ScrolledText):
                text_widget_to_style = widget
                if isinstance(widget, scrolledtext.ScrolledText):
                    text_widget_to_style = widget.text

                text_widget_to_style.configure(bg=current_theme_colors["text_bg"], fg=current_theme_colors["text_fg"],
                                 insertbackground=current_theme_colors["entry_insert"],
                                 selectbackground=current_theme_colors["accent_button_bg"],
                                 selectforeground=current_theme_colors["accent_button_fg"],
                                 relief=current_theme_colors["relief"], borderwidth=1)
                if isinstance(widget, scrolledtext.ScrolledText):
                    try:
                        widget.configure(bg=current_theme_colors["text_bg"])
                    except: pass
            elif widget_class == "Canvas":
                 widget.configure(bg=current_theme_colors["bg"], relief="flat", highlightthickness=0)
            elif widget_class == "Listbox":
                widget.configure(bg=current_theme_colors["listbox_bg"], fg=current_theme_colors["listbox_fg"],
                                 selectbackground=current_theme_colors["accent_button_bg"],
                                 selectforeground=current_theme_colors["accent_button_fg"],
                                 relief=current_theme_colors["relief"], borderwidth=1)
            elif widget_class == "Scrollbar":
                widget.configure(bg=current_theme_colors["scrollbar_bg"],
                                 troughcolor=current_theme_colors["scrollbar_trough"],
                                 activebackground=current_theme_colors["accent_button_bg"], relief="flat")


        except tk.TclError as e:
            # print(f"Не удалось применить тему к {widget_class} ({widget}): {e}")
            pass

    # Обновить стиль для статус бара
    if 'status_bar_frame' in globals() and status_bar_frame and status_bar_frame.winfo_exists():
        status_bar_frame.configure(style='StatusBar.TFrame') # Используем стиль
    if 'status_label' in globals() and status_label and status_label.winfo_exists():
        # status_label это ttk.Label, он должен подхватить стиль '.' или 'TLabel'
        # Для явного указания фона, если стиль не сработал:
        status_label.configure(background=current_theme_colors["status_bar_bg"])

    for avatar_label_widget in [instagram_avatar_label, tiktok_avatar_label, youtube_avatar_label]:
        if avatar_label_widget and avatar_label_widget.winfo_exists(): # Проверка существования виджета
            if hasattr(avatar_label_widget, 'image') and not avatar_label_widget.image:
                avatar_label_widget.config(bg=current_theme_colors["avatar_placeholder_bg"], relief=current_theme_colors["relief"])
            elif hasattr(avatar_label_widget, 'image') and avatar_label_widget.image:
                 avatar_label_widget.config(bg="", relief="flat")


# --- GUI Setup ---
root = tk.Tk()
root.title(f"Media Downloader v{APP_VERSION} (Gemini, Discord, Themes, Updates)")
root.minsize(width=850, height=700)

load_settings()

style = ttk.Style(root)
try:
    style.theme_use(OS_BASE_THEME)
    print(f"Using initial ttk base theme: {style.theme_use()}")
except tk.TclError as e_theme:
    print(f"Failed to set initial ttk theme '{OS_BASE_THEME}': {e_theme}. Using default.")
    try:
        style.theme_use('clam') # 'clam' обычно доступна на большинстве систем
        OS_BASE_THEME = 'clam'
        print(f"Fallback to 'clam' theme.")
    except tk.TclError:
        print("Could not set 'clam' theme either. TTK theming might be limited.")

# --- Меню ---
menubar = Menu(root)

file_menu = Menu(menubar, tearoff=0)
file_menu.add_command(label="Настройки...", command=open_settings_window)
file_menu.add_separator()
file_menu.add_command(label="Проверить обновления...", command=check_github_release_update_threaded)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=lambda: on_closing(ask=True))
menubar.add_cascade(label="Файл", menu=file_menu)

theme_menu = Menu(menubar, tearoff=0)
theme_menu.add_command(label="Светлая", command=lambda: set_theme("light"))
theme_menu.add_command(label="Темная", command=lambda: set_theme("dark"))
menubar.add_cascade(label="Тема", menu=theme_menu)

root.config(menu=menubar)

# --- Notebook (Вкладки) ---
notebook = ttk.Notebook(root, padding=(0, 5, 0, 0))

# --- Вкладка 1: Основное ---
tab_main = ttk.Frame(notebook, padding=10)
notebook.add(tab_main, text=' Загрузчик 📥 ')

login_main_frame = ttk.Frame(tab_main); login_main_frame.pack(pady=5, fill="x")

# Insta UI
insta_login_frame=ttk.LabelFrame(login_main_frame,text="Instagram",padding=(10,5));insta_login_frame.pack(pady=5,fill="x",side=tk.TOP)
ttk.Label(insta_login_frame,text="Логин:").grid(row=0,column=0,padx=5,pady=3,sticky="w");instagram_username_entry=ttk.Entry(insta_login_frame,width=25);instagram_username_entry.grid(row=0,column=1,padx=5,pady=3,sticky="ew")
ttk.Label(insta_login_frame,text="Пароль:").grid(row=1,column=0,padx=5,pady=3,sticky="w");instagram_password_entry=ttk.Entry(insta_login_frame,width=25,show="*");instagram_password_entry.grid(row=1,column=1,padx=5,pady=3,sticky="ew")
instagram_avatar_label=tk.Label(insta_login_frame,text=" ",width=5,height=2);instagram_avatar_label.grid(row=0,column=2,rowspan=2,padx=(10,0),pady=2)
instagram_login_button=ttk.Button(insta_login_frame,text="Войти в Instagram",command=login_to_instagram,style='Accent.TButton');instagram_login_button.grid(row=0,column=3,rowspan=2,padx=10,pady=5,ipady=5)
insta_login_frame.columnconfigure(1,weight=1)

# TikTok UI
tiktok_login_frame=ttk.LabelFrame(login_main_frame,text="TikTok",padding=(10,5));tiktok_login_frame.pack(pady=5,fill="x",side=tk.TOP)
ttk.Label(tiktok_login_frame,text="Email/Логин:").grid(row=0,column=0,padx=5,pady=3,sticky="w");tiktok_username_entry=ttk.Entry(tiktok_login_frame,width=25);tiktok_username_entry.grid(row=0,column=1,padx=5,pady=3,sticky="ew")
ttk.Label(tiktok_login_frame,text="Пароль:").grid(row=1,column=0,padx=5,pady=3,sticky="w");tiktok_password_entry=ttk.Entry(tiktok_login_frame,width=25,show="*");tiktok_password_entry.grid(row=1,column=1,padx=5,pady=3,sticky="ew")
tiktok_avatar_label=tk.Label(tiktok_login_frame,text=" ",width=5,height=2);tiktok_avatar_label.grid(row=0,column=2,rowspan=2,padx=(10,0),pady=2)
tiktok_login_button=ttk.Button(tiktok_login_frame,text="Войти в TikTok",command=login_to_tiktok);tiktok_login_button.grid(row=0,column=3,rowspan=2,padx=10,pady=5,ipady=5)
tiktok_login_frame.columnconfigure(1,weight=1)

# YouTube UI
youtube_login_frame=ttk.LabelFrame(login_main_frame,text="YouTube/Google",padding=(10,5));youtube_login_frame.pack(pady=5,fill="x",side=tk.TOP)
ttk.Label(youtube_login_frame,text="Email/Тел.:").grid(row=0,column=0,padx=5,pady=3,sticky="w");youtube_email_entry=ttk.Entry(youtube_login_frame,width=25);youtube_email_entry.grid(row=0,column=1,padx=5,pady=3,sticky="ew")
ttk.Label(youtube_login_frame,text="Пароль:").grid(row=1,column=0,padx=5,pady=3,sticky="w");youtube_password_entry=ttk.Entry(youtube_login_frame,width=25,show="*");youtube_password_entry.grid(row=1,column=1,padx=5,pady=3,sticky="ew")
youtube_avatar_label=tk.Label(youtube_login_frame,text=" ",width=5,height=2);youtube_avatar_label.grid(row=0,column=2,rowspan=2,padx=(10,0),pady=2)
youtube_login_button=ttk.Button(youtube_login_frame,text="Войти в YouTube",command=login_to_youtube);youtube_login_button.grid(row=0,column=3,rowspan=2,padx=10,pady=5,ipady=5)
youtube_login_frame.columnconfigure(1,weight=1)

url_input_frame = ttk.Frame(tab_main); url_input_frame.pack(pady=5, fill="x")
ttk.Label(url_input_frame, text="Ссылка для скачивания (Instagram, TikTok, YouTube):").pack(anchor="w",pady=(0,3))
url_entry = ttk.Entry(url_input_frame, width=80); url_entry.pack(fill="x")

get_media_button = ttk.Button(tab_main, text="🔍 Получить медиа", command=fetch_media_urls_thread_entry, style='Accent.TButton', padding=10)
get_media_button.pack(pady=10, padx=0, fill="x")

results_outer_frame = ttk.LabelFrame(tab_main, text="Найденные медиа", padding=5); results_outer_frame.pack(fill="both", expand=True, pady=(0,5))
results_scrollbar = ttk.Scrollbar(results_outer_frame, orient="vertical")
canvas_for_results = tk.Canvas(results_outer_frame, borderwidth=0, highlightthickness=0, yscrollcommand=results_scrollbar.set)
results_scrollbar.config(command=canvas_for_results.yview)
result_frame_content = ttk.Frame(canvas_for_results)
result_frame_content.bind("<Configure>", lambda e: canvas_for_results.configure(scrollregion=canvas_for_results.bbox("all")))
canvas_for_results.create_window((0,0), window=result_frame_content, anchor="nw")
results_scrollbar.pack(side="right", fill="y"); canvas_for_results.pack(side="left", fill="both", expand=True)

# --- Вкладка 2: Gemini ---
tab_gemini = ttk.Frame(notebook, padding=10)
notebook.add(tab_gemini, text=' Gemini AI 🤖 ')

ttk.Label(tab_gemini, text="Задайте любой вопрос Gemini API (используется gemini-pro).").pack(pady=(0, 10))
ttk.Label(tab_gemini, text="Ваш вопрос:").pack(anchor="w")
gemini_question_text = scrolledtext.ScrolledText(tab_gemini, width=70, height=5, wrap=tk.WORD, font=('Segoe UI', 10))
gemini_question_text.pack(pady=5, fill="x", expand=False)

gemini_submit_button = ttk.Button(tab_gemini, text="✉️ Отправить запрос к Gemini", command=handle_ask_gemini, style='Accent.TButton')
gemini_submit_button.pack(pady=5)

ttk.Label(tab_gemini, text="Ответ от Gemini:").pack(anchor="w")
gemini_answer_text = scrolledtext.ScrolledText(tab_gemini, width=70, height=10, wrap=tk.WORD, state=tk.DISABLED, font=('Segoe UI', 10))
gemini_answer_text.pack(pady=5, fill="both", expand=True)

# --- Размещение Notebook и остального ---
notebook.pack(expand=True, fill='both', padx=10, pady=(5,0))

download_buttons_frame = ttk.Frame(root, padding="5"); download_buttons_frame.pack(pady=(5,5), padx=10, fill="x")
download_local_button = ttk.Button(download_buttons_frame, text="📥 Скачать выбранные", command=lambda: handle_download_and_send(send_tg=False, send_discord=False), style='Accent.TButton')
download_local_button.pack(side=tk.LEFT, padx=2, expand=True, fill="x", ipady=5)

download_tg_button = ttk.Button(download_buttons_frame, text="Скачать и в Telegram ✈️", command=lambda: handle_download_and_send(send_tg=True, send_discord=False))
download_tg_button.pack(side=tk.LEFT, padx=2, expand=True, fill="x", ipady=5)

download_discord_button = ttk.Button(download_buttons_frame, text="Скачать и в Discord 💬", command=lambda: handle_download_and_send(send_tg=False, send_discord=True))
download_discord_button.pack(side=tk.LEFT, padx=2, expand=True, fill="x", ipady=5)


status_bar_frame = ttk.Frame(root, borderwidth=1, style='StatusBar.TFrame'); status_bar_frame.pack(side=tk.BOTTOM, fill="x", pady=(0,0)) # Применяем стиль
status_label = ttk.Label(status_bar_frame, text="Ожидание действий...", anchor="w", padding=(5, 3)); status_label.pack(side=tk.LEFT, fill="x", expand=True)
progress_bar = ttk.Progressbar(status_bar_frame, orient="horizontal", length=150, mode="determinate"); progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)

# --- Остальные функции ---
def update_status(message):
    if 'status_label' in globals() and status_label.winfo_exists(): status_label.config(text=message); root.update_idletasks()
def update_progress(current_value, max_value, finished=False):
    if 'progress_bar' in globals() and progress_bar.winfo_exists():
        if progress_bar['mode']=='indeterminate': progress_bar.stop(); progress_bar.config(mode='determinate')
        progress_bar['maximum'] = max_value; progress_bar['value'] = current_value; root.update_idletasks()
def update_progress_indeterminate(start=False, stop=False):
    if 'progress_bar' in globals() and progress_bar.winfo_exists():
        if start: progress_bar.config(mode='indeterminate'); progress_bar.start(15)
        elif stop: progress_bar.stop(); progress_bar.config(mode='determinate', value=0)
        root.update_idletasks()

def on_closing(ask=True):
    if ask:
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти? Запущенный драйвер будет остановлен."):
            close_driver()
            root.destroy()
    else: # Для выхода без запроса, если это когда-либо понадобится
        close_driver()
        root.destroy()

# --- Завершение настройки GUI и запуск ---
if __name__ == "__main__":
    apply_theme_to_all_widgets(root)
    reset_login_ui("instagram") # Для корректного relief аватарок при старте
    reset_login_ui("tiktok")
    reset_login_ui("youtube")
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(ask=True))
    # Раскомментируйте для проверки обновлений при старте:
    # check_github_release_update_threaded()
    root.mainloop()