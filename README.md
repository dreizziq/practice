# Notable — заметки на Django


Учебное веб-приложение для создания, просмотра, редактирования и удаления заметок. Браузерный интерфейс работает с REST API на Django и TastyPie. Данные хранятся в базе; вход не требуется, заметки общие для всех посетителей.

Проект: [Create a Django API in Under 20 Minutes](https://codeburst.io/create-a-django-api-in-under-20-minutes-2a082a60f6f3).
Каталог: [https://github.com/practical-tutorials/project-based-learning#python](https://github.com/practical-tutorials/project-based-learning#python). Подтвердите, что этот каталог утверждён преподавателем.

**GitHub:** [ВСТАВИТЬ ССЫЛКУ ПОСЛЕ ЗАГРУЗКИ]  
**Деплой:** [ВСТАВИТЬ ПУБЛИЧНЫЙ URL ПОСЛЕ ДЕПЛОЯ]

## Стек

- Frontend: HTML, CSS, JavaScript, Django Templates.
- Backend: Python, Django 5.2.17, TastyPie 0.15.1.
- База: SQLite локально; PostgreSQL настроен для Render.
- Развёртывание: Gunicorn, WhiteNoise, Render Blueprint.
- Проверки: Django TestCase, GitHub Actions; локально 8 тестов прошли.

## Локальный запуск

Python 3.13 или 3.14. В PowerShell из корня проекта:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Или вручную:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

Страница: http://127.0.0.1:8000/ . API: http://127.0.0.1:8000/api/note/ . Остановка: Ctrl+C.

## API

| Метод | Маршрут | Результат |
| --- | --- | --- |
| GET | /api/note/ | Список с пагинацией, 200 |
| POST | /api/note/ | Создание, 201; Location содержит адрес записи |
| GET | /api/note/{id}/ | Одна запись, 200; отсутствующая — 404 |
| PUT | /api/note/{id}/ | Замена заголовка и текста, 204 |
| DELETE | /api/note/{id}/ | Удаление, 204 |

POST и PUT: заголовок `Content-Type: application/json`, тело `{"title":"Заметка","body":"Текст"}`. Завершающий `/` обязателен. Заголовок и текст обязательны; длина заголовка до 200 символов. Дата хранится в базе, но скрыта в API как в заключительном примере статьи. Массовое удаление отключено. Готовые запросы: [коллекция Postman](Notable.postman_collection.json).

## Демонстрация

![Создание и изменение заметки](docs/demo.gif)

GIF длится 24,5 секунды. Он собран из реальных последовательных снимков локального браузера: заполнение формы, создание записи, редактирование и сохранённый результат. Сценарий: [docs/DEMO.md](docs/DEMO.md).

## Качество кода

Внешний сервис не подключён; результат: не подтверждён.
Code Climate Quality заменён Qlty. Для требования A/B нужен реальный анализ и согласование замены сервиса с преподавателем. Конфигурация `.codeclimate.yml` не является оценкой. После подключения внесите URL бейджа в `submission.json` и пересоберите материалы.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py test
```

## Материалы практики

- [Отчёт PDF](output/pdf/practice-report.pdf) и [редактируемый текст](docs/REPORT.md).
- [Таблица соответствия](docs/TRACEABILITY.md).
- [Развёртывание и заполнение ссылок](docs/DEPLOY.md).
- [Чек-лист перед сдачей](docs/BEFORE_SUBMISSION.md).
- [Архитектура](docs/architecture.mmd), [ERD](docs/erd.mmd).

Административная панель отключена по умолчанию. Основным сценариям не нужны login/password. Если включаете служебную панель через `ENABLE_ADMIN=true`, создайте пользователя командой `createsuperuser`; не включайте её в сдачу без тестовых доступов.

Проект — открытая учебная доска, не персональное хранилище. Для публичного сервера задайте `DEBUG=false` и случайный `SECRET_KEY`; Render Blueprint уже предусматривает эти параметры. `.env.example` показывает переменные, но сам файл автоматически не загружается.
