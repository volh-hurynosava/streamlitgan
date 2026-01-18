import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st

class TranslationManager:
    """Менеджер загрузки и управления переводами из JSON файлов"""
    def __init__(self, locales_dir: str = "locales", default_lang: str = "en"):
        """
        Инициализация менеджера переводов.
        
        Args:
            locales_dir: Директория с JSON файлами переводов
            default_lang: Язык по умолчанию
        """
        self.locales_dir = Path(locales_dir)
        self.default_lang = default_lang
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.available_languages: Dict[str, Dict[str, str]] = {}
        
        self.load_translations()
        self.init_available_languages()
    
    def load_translations(self) -> None:
        """Загружает все JSON файлы переводов из директории"""
        for json_file in self.locales_dir.glob("*.json"):
            lang_code = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                print(f"✓ Загружен язык: {lang_code}")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"✗ Ошибка загрузки {json_file}: {e}")
            except Exception as e:
                print(f"✗ Неожиданная ошибка с {json_file}: {e}")
    
    
    def init_available_languages(self) -> None:
        """Инициализирует информацию о доступных языках"""
        language_info = {
            "en": {"name": "English", "flag": "🇺🇸", "native": "English"},
            "ru": {"name": "Russian", "flag": "🇷🇺", "native": "Русский"}
        }
        
        self.available_languages = {
            code: info for code, info in language_info.items() 
            if code in self.translations
        }
    
    def get(self, lang: str, key: str, default: Optional[str] = None, **kwargs) -> str:
        """
        Получает перевод по ключу для указанного языка.
        
        Args:
            lang: Код языка (en, ru, es, etc.)
            key: Ключ перевода в формате 'section.subsection.key'
            default: Значение по умолчанию если перевод не найден
            **kwargs: Параметры для подстановки в строку
            
        Returns:
            Переведенная строка
        """
        if lang not in self.translations:
            lang = self.default_lang
        
        try:
            # Разбиваем ключ на части
            keys = key.split('.')
            value = self.translations[lang]
            
            # Рекурсивно получаем вложенное значение
            for k in keys:
                value = value[k]
            
            # Если это строка и есть параметры для подстановки
            if isinstance(value, str) and kwargs:
                try:
                    return value.format(**kwargs)
                except (KeyError, ValueError):
                    return value
            
            return str(value)
            
        except (KeyError, TypeError, AttributeError):
            # Пробуем язык по умолчанию
            if lang != self.default_lang:
                return self.get(self.default_lang, key, default, **kwargs)
            
            # Возвращаем значение по умолчанию или ключ
            if default is not None:
                return default
            
            # Если есть параметры, пробуем вставить их в ключ
            if kwargs:
                try:
                    return key.format(**kwargs)
                except:
                    return key
            
            return f"[{key}]"
    
    def get_nested(self, lang: str, key: str) -> Any:
        """Получает вложенный объект перевода (словарь, список)"""
        if lang not in self.translations:
            lang = self.default_lang
        
        try:
            keys = key.split('.')
            value = self.translations[lang]
            
            for k in keys:
                value = value[k]
            
            return value
        except (KeyError, TypeError, AttributeError):
            return None
    
    def get_style_name(self, lang: str, style_key: str) -> str:
        """Получает локализованное название стиля"""
        return self.get(lang, f"styles.{style_key}.name", style_key)
    
    def get_style_description(self, lang: str, style_key: str) -> str:
        """Получает локализованное описание стиля"""
        return self.get(lang, f"styles.{style_key}.description", "")
    
    
    
    def get_language_display_name(self, lang_code: str) -> str:
        """Получает отображаемое имя языка"""
        if lang_code in self.available_languages:
            info = self.available_languages[lang_code]
            return f"{info['flag']} {info['native']} ({info['name']})"
        return lang_code
    
    def get_language_options(self) -> Dict[str, str]:
        """Возвращает словарь опций для selectbox: отображаемое имя -> код языка"""
        return {
            self.get_language_display_name(code): code
            for code in self.available_languages.keys()
        }
    
    @st.cache_resource
    def get_cached_instance():
        """Кэшированный экземпляр менеджера переводов для Streamlit"""
        return TranslationManager()

_translator = None

def get_translator() -> TranslationManager:
    """Получает экземпляр менеджера переводов"""
    global _translator
    if _translator is None:
        _translator = TranslationManager()
    return _translator