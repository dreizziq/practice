from pathlib import Path
import json
from project_content import CONCLUSION
ROOT=Path(__file__).resolve().parent.parent
CONFIG=json.loads((ROOT/'submission.json').read_text(encoding='utf-8'))
REPO=CONFIG['github_url'].rstrip('/')
DOCS=ROOT/'docs'
def save(path,text):
    (ROOT/path).write_text(text.strip()+'\n',encoding='utf-8')
trace=[('Вход и выход','notable_django/urls.py'),('CRUD и пагинация','api/resources.py'),('Разграничение доступа','api/permissions.py'),('Связи и ограничения БД','api/models.py'),('Интерфейс и CSRF','api/static/api/app.js'),('Тестовые аккаунты','api/management/commands/seed_demo.py'),('Резервное копирование','api/management/commands/backup_database.py'),('Восстановление и целостность','api/db_backup.py'),('16 автоматических тестов','api/tests.py'),('Проверка копии','docs/backup-verification.json')]
trace_text='| Функция | Исходный код и подтверждение |\n| --- | --- |\n'+'\n'.join(f'| {a} | [{b}]({REPO}/blob/main/{b}) |' for a,b in trace)
save('docs/TRACEABILITY.md','# Таблица соответствия\n\n'+trace_text)
save('README.md',f'''# Notable — заметки на Django

Учебное приложение с личными заметками, REST API и браузерным интерфейсом. Владелец работает со своими записями; аудитор читает все записи; суперпользователь управляет всеми заметками.

Основа: [Create a Django API in Under 20 Minutes](https://codeburst.io/create-a-django-api-in-under-20-minutes-2a082a60f6f3). [Каталог проектов](https://github.com/practical-tutorials/project-based-learning#python).

**GitHub:** [{REPO}]({REPO})

## Стек

Python, Django 5.2.17, TastyPie 0.15.1, SQLite, HTML, CSS, JavaScript. Настройки также поддерживают PostgreSQL; проверка копирования и восстановления выполнена для SQLite.

## Локальный запуск

Python 3.13 или 3.14. В PowerShell из корня проекта:

```powershell
powershell -ExecutionPolicy Bypass -File .\\start.ps1
```

Или вручную:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe manage.py migrate
.\\.venv\\Scripts\\python.exe manage.py seed_demo
.\\.venv\\Scripts\\python.exe manage.py runserver
```

Открыть http://127.0.0.1:8000/ . Вход: `student1`, `student2` или `auditor`; пароль новых локальных тестовых аккаунтов: `PracticeDemo2026!`. Остановка: Ctrl+C. Для собственных данных смените тестовые пароли. `seed_demo` не сбрасывает пароли существующих пользователей.

## API и права

Все запросы требуют сессии Django после входа. Изменяющие запросы дополнительно требуют заголовок `X-CSRFToken`. Интерфейс передаёт его автоматически.

| Метод | Маршрут | Результат |
| --- | --- | --- |
| GET | /api/note/ | Список доступных заметок с пагинацией, 200 |
| POST | /api/note/ | Создание собственной заметки, 201 |
| GET | /api/note/{{id}}/ | Одна доступная заметка, 200 |
| PUT | /api/note/{{id}}/ | Изменение, 204 |
| DELETE | /api/note/{{id}}/ | Удаление, 204 |

POST и PUT: `Content-Type: application/json`, тело `{{"title":"Заметка","body":"Текст"}}`. Заголовок и текст обязательны; заголовок до 200 символов. Чужая запись скрыта от обычного пользователя. Аудитору запрещены изменения. Поле владельца назначает сервер. Массовое удаление отключено.

[Аккаунты и сценарии проверки](docs/ACCESS.md). [Запросы Postman](Notable.postman_collection.json).

## База данных и резервные копии

Заметка связана обязательным внешним ключом с пользователем. Непустые значения проверяются формой и ограничениями БД. Удаление владельца с заметками запрещено.

```powershell
.\\.venv\\Scripts\\python.exe manage.py backup_database --output backups/copy.sqlite3
.\\.venv\\Scripts\\python.exe manage.py restore_database backups/copy.sqlite3 --output backups/restored.sqlite3
```

Команды создают новые файлы и отказываются перезаписывать существующие. Восстановление проверяет SHA-256 и целостность базы. [Подробности](docs/DATABASE.md), [результат проверки](docs/backup-verification.json).

## Проверки

```powershell
.\\.venv\\Scripts\\python.exe manage.py check
.\\.venv\\Scripts\\python.exe manage.py test
```

Локально пройдены 16 тестов: CRUD, валидация, изоляция пользователей, роли, CSRF, копирование и восстановление. Внешняя оценка Code Climate A/B не подтверждена; конфигурация сервиса не является результатом анализа.

## Демонстрация и отчёты

![Создание и изменение заметки](docs/demo.gif)

- [Сценарий демонстрации](docs/DEMO.md).
- [Таблица соответствия](docs/TRACEABILITY.md).
- [Отчёт ПМ11](output/reports/Отчет_ПМ11_заполненный.docx) и [отчёт ПМ02](output/reports/Отчет_ПМ02_заполненный.docx).
- [PDF ПМ11](output/pdf/practice-report.pdf) и [PDF ПМ02](output/pdf/practice-report-pm02.pdf).
- [Проверка перед сдачей](docs/BEFORE_SUBMISSION.md).

Для пересборки Word-отчётов: установить `requirements-report.txt` и выполнить `python tools/fill_reports.py` (Windows, шрифт Times New Roman). Исходные шаблоны находятся в `docs/templates`. Скрипт `tools/build_submission.py` обновляет текстовые материалы. PDF экспортируются из Word.
''')
save('docs/DEMO.md','''# Демонстрация

GIF `docs/demo.gif` показывает локальное создание и изменение заметки после входа в тестовый аккаунт.

Для повторения:

1. Запустить проект и войти как `student1` с паролем `PracticeDemo2026!`.
2. Создать заметку «Подготовка к защите» с текстом «Проверить основные функции».
3. Изменить текст на «Готово: заметка создана и успешно изменена.» и сохранить.
4. Обновить страницу и убедиться, что текст сохранён.
5. Выйти и войти как `student2`: заметка первого пользователя недоступна.
6. Войти как `auditor`: все заметки доступны только для чтения.

Роли и восстановление базы дополнительно проверяются автоматическими тестами.
''')
save('docs/BEFORE_SUBMISSION.md','''# Проверка перед сдачей

- [ ] Загрузить обновлённые исходники и отчёты в GitHub; открыть ссылки из отчётов.
- [ ] Вписать ФИО, группу и прочие обязательные личные реквизиты в Word.
- [ ] Проверить объём ПМ02: строки дневника дают 108 часов, поэтому итог исправлен на 108. Если по учебному плану требуется 72, согласовать сам дневник.
- [ ] В характеристике ПМ11 поставить фактическую дату; ошибочная дата 19.12.2025 удалена.
- [ ] Подписи, оценки и характеристику заверяют соответствующие руководители.
- [ ] Выполнить локальный запуск и показать права пользователей, копирование и восстановление.
- [ ] Получить реальный результат анализа Code Climate A/B либо согласовать с преподавателем допустимое подтверждение качества.

Не присваивайте проекту оценку сервиса без фактического анализа. Тесты подтверждают поведение программы, но не заменяют внешнюю оценку.
''')
save('СНАЧАЛА_ПРОЧИТАЙ.md','''# Материалы для сдачи

1. Запустите `start.ps1` и проверьте вход `student1 / PracticeDemo2026!`.
2. Загрузите обновлённые файлы в свой репозиторий GitHub.
3. Используйте Word-отчёты из `output/reports` и PDF из `output/pdf`.
4. Заполните личные реквизиты, проверьте часы ПМ02 и фактическую дату характеристики ПМ11. Подписи и оценки заполняют руководители.
5. Проверьте [список перед сдачей](docs/BEFORE_SUBMISSION.md).

Инструкции и доказательства: [README](README.md), [роли](docs/ACCESS.md), [база данных](docs/DATABASE.md), [соответствие исходникам](docs/TRACEABILITY.md).
''')
save('docs/architecture.mmd','''flowchart LR
  B[Браузер] -->|Сессия и CSRF| A[Django и TastyPie]
  A --> P[Проверка владельца и роли]
  P --> O[Django ORM]
  O --> D[(SQLite)]
  D --> C[Копия и SHA-256]
  C --> R[Проверенное восстановление]
''')
save('docs/erd.mmd','''erDiagram
  AUTH_USER ||--o{ API_NOTE : owns
  AUTH_USER }o--o{ AUTH_GROUP : belongs
  AUTH_USER {
    int id PK
    string username
    string password_hash
  }
  API_NOTE {
    int id PK
    int owner_id FK
    string title
    text body
    datetime created_at
  }
''')
save('docs/REPORT.md','# Notable — материалы отчёта\n\nПроект связывает интерфейс, REST API и базу данных. Реализованы вход, роли, CRUD и проверяемые резервные копии.\n\nGitHub: '+REPO+'\n\n## Архитектура и данные\n\nСм. [описание БД](DATABASE.md), [архитектуру](architecture.mmd), [ERD](erd.mmd) и [права доступа](ACCESS.md).\n\n## Соответствие\n\n'+trace_text+'\n\n## Демонстрация\n\n![Демонстрация](demo.gif)\n\n## Проверки\n\nПройдены 16 тестов. Внешняя оценка Code Climate A/B не подтверждена.\n\n## Вывод\n\n'+'\n\n'.join(CONCLUSION))
