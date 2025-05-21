from datetime import datetime

def now():
    """Возвращает текущую дату и время для использования в шаблонах Jinja2."""
    return datetime.now()

def setup_jinja2_extensions(templates):
    """Настраивает расширения и фильтры для Jinja2."""
    templates.env.globals['now'] = now 