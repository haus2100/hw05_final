## Yatube

Yatube - социальная сеть для публикации личных дневников. Это сайт, на котором можно создать свою страницу. Если на нее зайти, то можно посмотреть все записи автора. Пользователи могут заходить на чужие страницы, подписываться на авторов и комментировать их записи.

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/haus2100/hw05_final.git
```

```
cd hw05_final
```

Установите и активируйте виртуальное окружение (Windows):

```
python -m venv venv
```
```
source venv/Scripts/activate
```

Установить зависимости:

```
pip install -r requirements.txt
```

Применить миграции:

```
python manage.py makemigrations
```
```
python manage.py migrate
```

Создание суперпользователя:

```
python manage.py createsuperuser
```

Запуск приложения:

```
python manage.py runserver
```

### Технологии:
- Python 3
- Django 2
- Django Unittest
- SQLite
- Git
