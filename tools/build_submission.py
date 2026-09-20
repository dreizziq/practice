"""Rebuild the practice report and README from submission.json."""
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Ellipse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / 'submission.json').read_text(encoding='utf-8'))
DOCS = ROOT / 'docs'
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
ARTICLE = 'https://codeburst.io/create-a-django-api-in-under-20-minutes-2a082a60f6f3'
REPO = CONFIG['github_url'].rstrip('/')
SITE = CONFIG['deploy_url'].rstrip('/')
BRANCH = CONFIG.get('branch', 'main')


def field(name, label):
    return CONFIG.get(name) or f'[{label}]'


def code_url(path):
    return f'{REPO}/blob/{BRANCH}/{path}' if REPO else ''


def screen_url(path):
    return SITE + path if SITE else ''


def link_md(label, url):
    return f'[{label}]({url})' if url else f'{label} — ссылка после публикации'


TRACE = [
    ('Просмотр и страницы списка', 'api/static/api/app.js', '/#notes', 'GET /api/note/?limit=6'),
    ('Создание заметки', 'api/resources.py', '/#create', 'POST /api/note/'),
    ('Чтение одной заметки', 'api/resources.py', '/api/note/1/', 'GET /api/note/{id}/'),
    ('Изменение заметки', 'api/static/api/app.js', '/#create', 'PUT /api/note/{id}/'),
    ('Удаление с подтверждением', 'api/static/api/app.js', '/#notes', 'DELETE /api/note/{id}/'),
    ('Проверка обязательных полей', 'api/resources.py', '/#create', 'HTTP 400 при неверных данных'),
    ('Сохранение в базе данных', 'api/models.py', '/#notes', 'Данные остаются после обновления'),
    ('Адаптивная страница', 'api/static/api/styles.css', '/', 'Одна колонка на узком экране'),
]

CONCLUSION = [
    'В результате работы подготовлено приложение Notable для хранения заметок. В основе проекта лежит учебный пример создания Django API. Его функциональность сохранена: запись содержит заголовок, текст и время создания, а клиент может создавать, получать, изменять и удалять записи. Проект дополнен страницей для работы через браузер, автоматическими проверками и материалами для развёртывания. Благодаря этому основной сценарий можно продемонстрировать без установки Postman у проверяющего.',
    'Работа с проектом показывает, как распределяются обязанности между клиентской и серверной частями. Браузер собирает введённые данные и отправляет JSON. Маршрутизация Django передаёт запрос ресурсу TastyPie. Ресурс проверяет данные и выполняет действие над моделью, а ORM обращается к базе. Интерфейс получает результат и обновляет список. При такой организации одна и та же серверная логика используется и страницей заметок, и внешним HTTP-клиентом. Изменение оформления не требует изменения структуры таблицы.',
    'Одной из технических задач стала адаптация исходного учебного материала к установленной версии Django. Вместо старого механизма объявления маршрутов применён актуальный интерфейс django.urls. Структура проекта разделена на настройки, модель, ресурс, шаблон и статические файлы. Миграция хранится вместе с исходниками: после установки зависимостей другой разработчик может создать таблицу одной командой. Демонстрационные данные добавляются отдельно, причём повторный запуск команды не создаёт одинаковую начальную запись.',
    'Другой важной задачей была согласованная обработка ошибок. Ограничения HTML помогают посетителю заполнить форму, но сервер выполняет собственную проверку заголовка и текста. Невалидный запрос не должен менять уже сохранённую запись. Для этой ситуации добавлен отдельный тест. Ответы 201 и 204 обрабатываются без попытки разобрать отсутствующее тело JSON. Вывод текста заметок через textContent позволяет показывать пользовательский ввод как текст, а не исполнять его в качестве разметки.',
    'Проверка проекта включала полный цикл CRUD, запрос отсутствующей записи, ошибочный JSON, пустые поля, ограничение длины заголовка и разбиение списка на страницы. Восемь автоматических тестов завершились успешно. В браузере дополнительно проверены создание и изменение заметки; эти действия отражены в демонстрационном GIF. Автотесты полезны тем, что проверяют результат запроса и состояние базы, а не только внешний вид страницы. При этом локальная проверка не заменяет контроль доступности будущего публичного адреса.',
    'Подготовка к размещению потребовала учесть отличие локальной среды от хостинга. Для локального запуска используется SQLite, для Render предусмотрено подключение PostgreSQL через переменную окружения. Секрет приложения, разрешённые хосты и режим отладки вынесены в настройки среды. Статические файлы собираются отдельной командой. Эти решения делают процесс запуска воспроизводимым и позволяют хранить исходники отдельно от секретов и рабочих данных. Публикация и проверка на хостинге выполняются после настройки аккаунта владельца.',
    'Дальнейшее развитие проекта может включать персональные аккаунты, разграничение доступа к заметкам, поиск, теги и восстановление удалённых записей. Сейчас приложение представляет собой общую учебную доску: все посетители работают с одними данными. Для использования в качестве личного блокнота сначала потребуется реализовать владельца записи и проверку прав на каждую операцию. Ещё одно направление развития — автоматические проверки интерфейса и анализ качества кода внешним сервисом. Реальный результат такого анализа необходимо подтверждать ссылкой на отчёт.',
]


def make_gif():
    names = ['02-form.png', '03-created.png', '04-edit.png', '05-updated.png']
    labels = ['1. Заполнение формы', '2. Заметка создана', '3. Изменение текста', '4. Изменения сохранены']
    font_path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'arial.ttf'
    font = ImageFont.truetype(str(font_path), 24) if font_path.exists() else ImageFont.load_default()
    frames = []
    for name, label in zip(names, labels):
        source = PILImage.open(DOCS / 'demo' / name).convert('RGB')
        source.thumbnail((1120, 960))
        canvas = PILImage.new('RGB', (1120, 1020), '#f5f6f2')
        canvas.paste(source, ((1120 - source.width) // 2, 60))
        ImageDraw.Draw(canvas).text((26, 16), label, fill='#24342e', font=font)
        frames.append(canvas)
    frames[0].save(DOCS / 'demo.gif', save_all=True, append_images=frames[1:],
                   duration=[5500, 6500, 5500, 7000], loop=0, optimize=False)


def make_markdown():
    badge = ''
    if CONFIG.get('quality_badge_image_url') and CONFIG.get('quality_report_url'):
        badge = f"[![Качество кода]({CONFIG['quality_badge_image_url']})]({CONFIG['quality_report_url']})\n"
    quality = f"{CONFIG.get('quality_service') or 'Внешний сервис не подключён'}; результат: {CONFIG.get('quality_grade') or 'не подтверждён'}."
    trace = '\n'.join('| ' + ' | '.join([name, link_md(path, code_url(path)), link_md(screen, screen_url(screen)), result]) + ' |'
                      for name, path, screen, result in TRACE)
    readme = f'''# Notable — заметки на Django

{badge}
Учебное веб-приложение для создания, просмотра, редактирования и удаления заметок. Браузерный интерфейс работает с REST API на Django и TastyPie. Данные хранятся в базе; вход не требуется, заметки общие для всех посетителей.

Проект: [Create a Django API in Under 20 Minutes]({ARTICLE}).
Каталог: [{CONFIG['catalog_url']}]({CONFIG['catalog_url']}). Подтвердите, что этот каталог утверждён преподавателем.

**GitHub:** {REPO or '[ВСТАВИТЬ ССЫЛКУ ПОСЛЕ ЗАГРУЗКИ]'}  
**Деплой:** {SITE or '[ВСТАВИТЬ ПУБЛИЧНЫЙ URL ПОСЛЕ ДЕПЛОЯ]'}

## Стек

- Frontend: HTML, CSS, JavaScript, Django Templates.
- Backend: Python, Django 5.2.17, TastyPie 0.15.1.
- База: SQLite локально; PostgreSQL настроен для Render.
- Развёртывание: Gunicorn, WhiteNoise, Render Blueprint.
- Проверки: Django TestCase, GitHub Actions; локально 8 тестов прошли.

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

Страница: http://127.0.0.1:8000/ . API: http://127.0.0.1:8000/api/note/ . Остановка: Ctrl+C.

## API

| Метод | Маршрут | Результат |
| --- | --- | --- |
| GET | /api/note/ | Список с пагинацией, 200 |
| POST | /api/note/ | Создание, 201; Location содержит адрес записи |
| GET | /api/note/{{id}}/ | Одна запись, 200; отсутствующая — 404 |
| PUT | /api/note/{{id}}/ | Замена заголовка и текста, 204 |
| DELETE | /api/note/{{id}}/ | Удаление, 204 |

POST и PUT: заголовок `Content-Type: application/json`, тело `{{"title":"Заметка","body":"Текст"}}`. Завершающий `/` обязателен. Заголовок и текст обязательны; длина заголовка до 200 символов. Дата хранится в базе, но скрыта в API как в заключительном примере статьи. Массовое удаление отключено. Готовые запросы: [коллекция Postman](Notable.postman_collection.json).

## Демонстрация

![Создание и изменение заметки](docs/demo.gif)

GIF длится 24,5 секунды. Он собран из реальных последовательных снимков локального браузера: заполнение формы, создание записи, редактирование и сохранённый результат. Сценарий: [docs/DEMO.md](docs/DEMO.md).

## Качество кода

{quality}
Code Climate Quality заменён Qlty. Для требования A/B нужен реальный анализ и согласование замены сервиса с преподавателем. Конфигурация `.codeclimate.yml` не является оценкой. После подключения внесите URL бейджа в `submission.json` и пересоберите материалы.

```powershell
.\\.venv\\Scripts\\python.exe manage.py check
.\\.venv\\Scripts\\python.exe manage.py collectstatic --noinput
.\\.venv\\Scripts\\python.exe manage.py test
```

## Материалы практики

- [Отчёт PDF](output/pdf/practice-report.pdf) и [редактируемый текст](docs/REPORT.md).
- [Таблица соответствия](docs/TRACEABILITY.md).
- [Развёртывание и заполнение ссылок](docs/DEPLOY.md).
- [Чек-лист перед сдачей](docs/BEFORE_SUBMISSION.md).
- [Архитектура](docs/architecture.mmd), [ERD](docs/erd.mmd).

Административная панель отключена по умолчанию. Основным сценариям не нужны login/password. Если включаете служебную панель через `ENABLE_ADMIN=true`, создайте пользователя командой `createsuperuser`; не включайте её в сдачу без тестовых доступов.

Проект — открытая учебная доска, не персональное хранилище. Для публичного сервера задайте `DEBUG=false` и случайный `SECRET_KEY`; Render Blueprint уже предусматривает эти параметры. `.env.example` показывает переменные, но сам файл автоматически не загружается.
'''
    (ROOT / 'README.md').write_text(readme, encoding='utf-8')
    (DOCS / 'TRACEABILITY.md').write_text('# Таблица соответствия\n\nПосле публикации заполните `submission.json` и запустите генератор. Для `/api/note/1/` используйте существующий ID из списка.\n\n| Функция | Файл GitHub | Страница | Проверка |\n| --- | --- | --- | --- |\n' + trace + '\n', encoding='utf-8')
    (DOCS / 'DEMO.md').write_text('''# Демонстрация

Файл `demo.gif`, 24,5 секунды. Снимки сделаны в работающем локальном браузере, а не нарисованы.

1. Ввести заголовок «Подготовка к защите» и текст.
2. Нажать «Создать заметку» — появляется карточка и подтверждение.
3. Нажать «Изменить», ввести «Готово: заметка создана и успешно изменена.».
4. Сохранить — новый текст виден в списке.

Для проверки удаления после демонстрации нажать «Удалить», подтвердить действие и убедиться, что карточка исчезла. Удаление дополнительно покрыто автоматическим тестом CRUD.
''', encoding='utf-8')
    (DOCS / 'architecture.mmd').write_text('flowchart LR\n  U[Браузер HTML CSS JavaScript] -->|HTTP JSON| R[Django и TastyPie]\n  R -->|Django ORM| D[(SQLite локально или PostgreSQL на хостинге)]\n  R -->|JSON| U\n', encoding='utf-8')
    (DOCS / 'erd.mmd').write_text('erDiagram\n  NOTE {\n    bigint id PK\n    varchar title\n    text body\n    datetime created_at\n  }\n', encoding='utf-8')
    report = f'''# Отчёт по практике Разработка веб приложения Notable

Студент: {field('student', 'ФИО')}. Группа: {field('group', 'группа')}.
Учебное заведение: {field('institution', 'учебное заведение')}.
Руководитель: {field('supervisor', 'руководитель')}. Сроки: {field('practice_dates', 'сроки практики')}.

## 1 Выбранный проект

Create a Django API in Under 20 Minutes. Источник: {ARTICLE}
Каталог: {CONFIG['catalog_url']}
Реализован API заметок; добавлены браузерный интерфейс, валидация, пагинация, тесты и конфигурация деплоя.

## 2 Технический паспорт проекта

GitHub: {REPO or '[ЗАПОЛНИТЬ]'}. Деплой: {SITE or '[ЗАПОЛНИТЬ]'}.
Frontend: HTML/CSS/JavaScript. Backend: Python/Django/TastyPie. DB: SQLite локально; PostgreSQL в конфигурации Render.
Вход не нужен. Админка выключена. Демо: docs/demo.gif.

## 3 Архитектура

Браузер → HTTP/JSON → Django/TastyPie → ORM → база данных. Схемы: architecture.mmd и erd.mmd.
Таблица api_note: id PK, title varchar(200), body text, created_at datetime. Предметных связей с другими сущностями нет.
Use Case: создать заметку, прочитать список/запись, изменить, удалить с подтверждением.
API: GET/POST /api/note/; GET/PUT/DELETE /api/note/{{id}}/. Тело POST/PUT: {{"title":"Заметка","body":"Текст"}}.

## 4 Таблица соответствия

| Функция | Файл GitHub | Страница | Проверка |
| --- | --- | --- | --- |
{trace}

## 5 Демонстрация работы

docs/demo.gif, 24,5 секунды. Заполнение формы → создание → изменение → сохранённый результат. Демонстрация выполнена локально.

## 6 Качество кода

8 локальных тестов пройдены; Django check и проверка миграций без ошибок. CRUD, неверный JSON, обязательные поля, длина заголовка, отклонение неверного изменения, пагинация и запрет массового удаления проверены.
{quality} Код бейджа добавляется после реального анализа. Qlty должен быть согласован вместо Code Climate.

## 7 Вывод по практике

''' + '\n\n'.join(CONCLUSION)
    (DOCS / 'REPORT.md').write_text(report, encoding='utf-8')


def register_fonts():
    windows = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    pairs = [(windows / 'times.ttf', windows / 'timesbd.ttf'),
             (Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'))]
    for regular, bold in pairs:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont('Body', str(regular)))
            pdfmetrics.registerFont(TTFont('BodyBold', str(bold)))
            pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')
            return
    raise RuntimeError('Install Times New Roman or DejaVu Serif to render Cyrillic.')


def make_pdf():
    register_fonts()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TextRU', fontName='Body', fontSize=11.5, leading=16, spaceAfter=9))
    styles.add(ParagraphStyle(name='SmallRU', fontName='Body', fontSize=9.5, leading=12.5, spaceAfter=5))
    styles.add(ParagraphStyle(name='HeadingRU', fontName='BodyBold', fontSize=17, leading=22, spaceAfter=17))
    styles.add(ParagraphStyle(name='SubRU', fontName='BodyBold', fontSize=12, leading=16, spaceBefore=10, spaceAfter=8))
    styles.add(ParagraphStyle(name='CoverRU', fontName='BodyBold', fontSize=23, leading=30, alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name='CenterRU', parent=styles['TextRU'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='ConclusionRU', parent=styles['TextRU'], fontSize=11, leading=14, alignment=TA_JUSTIFY, spaceAfter=7))
    story = []
    def p(text, style='TextRU'):
        return Paragraph(text, styles[style])
    def add(text, style='TextRU'):
        story.append(p(text, style))
    def h(text):
        add(text, 'HeadingRU')
    def url(label, target):
        return f'<link href="{escape(target, {chr(34): "&quot;"})}" color="#234e70">{escape(label)}</link>' if target else escape(label) + ' [после публикации]'
    def table(rows, widths):
        data = [[p(str(cell), 'SmallRU') for cell in row] for row in rows]
        result = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
        result.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8edf0')),
            ('GRID', (0, 0), (-1, -1), .45, colors.HexColor('#d9d9d9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(result)
        story.append(Spacer(1, 10))

    add(escape(field('institution', 'Название учебного заведения')), 'CenterRU')
    story.append(Spacer(1, 90))
    add('Отчёт по практике', 'CoverRU')
    add('Разработка веб приложения Notable', 'CoverRU')
    add('REST API и браузерный интерфейс для заметок', 'CenterRU')
    story.append(Spacer(1, 70))
    for key, label in [('student','Студент'), ('group','Группа'), ('supervisor','Руководитель'), ('practice_dates','Сроки практики')]:
        add(f'{label}: {escape(field(key, label))}')
    story.append(Spacer(1, 100))
    add(f"{escape(field('city', 'Город'))} · {escape(CONFIG['year'])}", 'CenterRU')
    story.append(PageBreak())

    h('1 Выбранный проект')
    add('<b>Create a Django API in Under 20 Minutes</b> — учебный проект API заметок по статье Scott Domes. Приложение позволяет сохранять заголовок и текст, просматривать записи, изменять и удалять их.')
    add(url('Статья с выбранным проектом', ARTICLE) + '<br/>' + url('Проект в каталоге Python', CONFIG['catalog_url']))
    add('Сохранены Django, TastyPie, модель Note и маршруты /api/note/. Добавлены браузерный интерфейс, проверка данных, страницы списка, тесты, конфигурация Render и материалы для демонстрации.')
    h('2 Технический паспорт проекта')
    table([
        ['Параметр', 'Значение'],
        ['Название', 'Notable'],
        ['GitHub', url(REPO or 'Публичный репозиторий', REPO)],
        ['Деплой', url(SITE or 'Публичный сайт', SITE)],
        ['Frontend', 'HTML, CSS, JavaScript, Django Templates'],
        ['Backend', 'Python; Django 5.2.17; TastyPie 0.15.1'],
        ['База данных', 'SQLite при локальном запуске; PostgreSQL в конфигурации Render'],
        ['Развёртывание', 'Render Blueprint, Gunicorn, WhiteNoise'],
        ['Доступы', 'Login/password не требуются. Общая доска без регистрации. Админка отключена.'],
        ['Демонстрация', url('docs/demo.gif — 24,5 секунды', code_url('docs/demo.gif'))],
        ['Локальная проверка', 'Python 3.14.7; 8 тестов пройдены; Django check без ошибок'],
    ], [115, 366])
    story.append(PageBreak())

    h('3 Архитектура')
    add('Клиентская страница обращается к API по HTTP. Django маршрутизирует запрос, TastyPie преобразует его в операцию над Note, а ORM выполняет запрос к базе данных. Ответы API сериализуются в JSON.')
    d = Drawing(480, 115)
    for x, title, sub in [(0,'Браузер','HTML · CSS · JS'),(175,'Django и TastyPie','Ресурс Note'),(350,'База данных','SQLite / PostgreSQL')]:
        d.add(Rect(x, 34, 130, 65, fillColor=colors.HexColor('#f3f5f6'), strokeColor=colors.HexColor('#a8b6bf')))
        d.add(String(x+65, 72, title, fontName='BodyBold', fontSize=10.5, textAnchor='middle'))
        d.add(String(x+65, 52, sub, fontName='Body', fontSize=9.5, textAnchor='middle'))
    for x, label in [(130,'JSON'),(305,'ORM')]:
        d.add(Line(x, 65, x+42, 65, strokeColor=colors.black))
        d.add(Polygon([x+42,65,x+36,69,x+36,61], fillColor=colors.black))
        d.add(String(x+22, 81, label, fontName='Body', fontSize=9, textAnchor='middle'))
    story.append(d)
    add('ERD предметной области', 'SubRU')
    er = Drawing(480, 155)
    er.add(Rect(85, 12, 310, 135, fillColor=colors.white, strokeColor=colors.HexColor('#8b9ea9')))
    er.add(Rect(85, 117, 310, 30, fillColor=colors.HexColor('#e8edf0'), strokeColor=colors.HexColor('#8b9ea9')))
    er.add(String(240, 127, 'api_note', fontName='BodyBold', fontSize=12, textAnchor='middle'))
    for y, text in [(97,'id — bigint, первичный ключ'), (74,'title — varchar(200), обязательное'), (51,'body — text, обязательное'), (28,'created_at — datetime, автоматически')]:
        er.add(String(102,y,text,fontName='Body',fontSize=11))
    story.append(er)
    add('Предметная область содержит одну таблицу без внешних ключей. У заметки нет владельца: данные общие. Служебные таблицы Django для миграций, сессий и встроенной системы пользователей не являются дополнительными сущностями блокнота.')
    add('Обработка данных', 'SubRU')
    add('NoteForm проверяет обязательность title и body и максимальную длину заголовка. created_at устанавливается при сохранении и скрыт в API. Вывод заметок через textContent не превращает пользовательский текст в HTML. Разрешены только нужные методы: список GET/POST и запись GET/PUT/DELETE.')
    story.append(PageBreak())

    h('3 Архитектура и сценарии использования')
    table([
        ['Use Case', 'Действие и ожидаемый результат'],
        ['Создать', 'Посетитель вводит заголовок и текст. POST создаёт запись; карточка появляется в списке.'],
        ['Прочитать', 'Посетитель открывает список или URL записи. GET возвращает сохранённые данные.'],
        ['Изменить', 'Кнопка «Изменить» заполняет форму. PUT сохраняет новый текст; список обновляется.'],
        ['Удалить', 'Посетитель подтверждает удаление. DELETE удаляет запись; следующий GET возвращает 404.'],
    ], [100,381])
    add('Контракт API', 'SubRU')
    table([
        ['Метод и маршрут', 'Входные данные', 'Успех'],
        ['GET /api/note/', 'limit, offset — параметры страницы', '200, meta и objects'],
        ['POST /api/note/', 'JSON с title и body', '201, Location'],
        ['GET /api/note/{id}/', 'ID в адресе', '200, title, body, resource_uri'],
        ['PUT /api/note/{id}/', 'JSON с title и body', '204, пустое тело'],
        ['DELETE /api/note/{id}/', 'ID в адресе', '204, пустое тело'],
    ], [174,192,115])
    add('Пример создания', 'SubRU')
    add('POST /api/note/<br/>Content-Type: application/json<br/>{&quot;title&quot;: &quot;План&quot;, &quot;body&quot;: &quot;Подготовить демонстрацию&quot;}', 'SmallRU')
    add('Пример ответа на чтение', 'SubRU')
    add('{&quot;title&quot;: &quot;План&quot;, &quot;body&quot;: &quot;Подготовить демонстрацию&quot;, &quot;resource_uri&quot;: &quot;/api/note/1/&quot;}', 'SmallRU')
    add('ID 1 приведён как пример. Фактический адрес берётся из Location или resource_uri. При неверных данных возвращается 400, при отсутствии записи — 404, при запрещённом методе — 405. Конечный слеш обязателен. Коллекция Postman находится в корне репозитория.')
    story.append(PageBreak())

    h('4 Таблица соответствия реализации')
    add('Таблица связывает каждую пользовательскую функцию с исходниками и местом её проверки. Ссылки на исходники и страницы формируются из адресов, указанных в техническом паспорте.')
    rows = [['Функция', 'Исходники GitHub', 'Экран или маршрут']]
    for name, path, screen, result in TRACE:
        rows.append([name, url(path, code_url(path)), url(screen, screen_url(screen)) + '<br/>' + escape(result)])
    table(rows, [122,174,185])
    add('Для API одной записи используйте существующий ID из GET /api/note/. Если начальная заметка удалена, пример /api/note/1/ закономерно вернёт 404. Сценарий изменения начинается кнопкой на карточке; #create указывает на форму редактирования.')
    add('Поддерживающие файлы', 'SubRU')
    add(url('Миграция таблицы', code_url('api/migrations/0001_initial.py')) + '<br/>' + url('Автоматические тесты', code_url('api/tests.py')) + '<br/>' + url('Конфигурация развёртывания', code_url('render.yaml')))
    story.append(PageBreak())

    h('5 Демонстрация работы')
    add('Формат: GIF, 24,5 секунды. Показан основной сценарий: заполнение формы → создание заметки → изменение текста → сохранённый результат. Изображения получены из работающего локального приложения.')
    add(url('Открыть демонстрацию docs/demo.gif', code_url('docs/demo.gif')))
    screenshot = DOCS / 'demo' / '05-updated.png'
    im = PILImage.open(screenshot)
    width = 465
    story.append(Image(str(screenshot), width=width, height=width*im.height/im.width))
    add('Рисунок 1 — заметка после изменения текста', 'SmallRU')
    add('Для повторения открыть главную страницу, создать заметку «Подготовка к защите», изменить текст на «Готово: заметка создана и успешно изменена.» и сохранить. Карточка должна отобразить новый текст. После публикации сценарий повторяется в режиме инкогнито на публичном адресе.')
    story.append(PageBreak())

    h('6 Качество кода')
    add('Локальная проверка завершилась успешно: восемь тестов Django пройдены. Проверка конфигурации не выявила ошибок, новых незаписанных миграций нет. Автоматическая проверка в GitHub Actions настроена на push и pull request; её результат появится после загрузки репозитория.')
    table([
        ['Проверка', 'Подтверждённый результат'],
        ['CRUD и хранение данных', 'Создание 201; чтение 200; изменение и удаление 204; после удаления 404.'],
        ['Некорректный ввод', 'Отсутствующее поле, пустой текст, заголовок длиннее 200 символов и неправильный JSON отклоняются.'],
        ['Безопасность изменения', 'Ошибка валидации не меняет прежнее содержимое записи. Массовое удаление запрещено.'],
        ['Список и интерфейс', 'Пагинация выдаёт следующую страницу; главная страница содержит форму. Админка недоступна по умолчанию.'],
        ['Браузер', 'Создание и изменение записи проверены вручную; результат отражён в GIF.'],
    ], [128,353])
    add('Внешний анализ качества', 'SubRU')
    service = CONFIG.get('quality_service') or 'не подключён'
    grade = CONFIG.get('quality_grade') or 'не подтверждена'
    add(f'Сервис: {escape(service)}. Оценка: {escape(grade)}. ' + url('Отчёт сервиса', CONFIG.get('quality_report_url', '')))
    add('Требование гайда — бейдж Code Climate с оценкой A или B. В официальной документации Code Climate Quality новые пользователи направляются в Qlty. При использовании Qlty замена должна быть согласована с преподавателем. Успешные тесты и файл конфигурации не заменяют результат внешнего анализа.')
    add(url('Источник о переходе Code Climate Quality на Qlty', 'https://docs.codeclimate.com/docs/overview'), 'SmallRU')
    add('Согласование замены сервиса: ' + ('подтверждено владельцем проекта' if CONFIG.get('quality_accepted_by_teacher') else 'не отмечено в данных отчёта') + '.')
    story.append(PageBreak())

    h('7 Вывод по практике')
    for text in CONCLUSION:
        add(escape(text), 'ConclusionRU')

    def footer(canvas, doc):
        if doc.page > 1:
            canvas.setFont('Body', 9)
            canvas.setFillColor(colors.HexColor('#59636b'))
            canvas.drawString(20*mm, 12*mm, 'Notable · Отчёт по практике')
            canvas.drawRightString(190*mm, 12*mm, str(doc.page))
    document = SimpleDocTemplate(str(OUT / 'practice-report.pdf'), pagesize=(210*mm,297*mm),
                                 leftMargin=20*mm, rightMargin=20*mm, topMargin=19*mm, bottomMargin=20*mm,
                                 title='Отчёт по практике Разработка веб приложения Notable', author=CONFIG.get('student') or '')
    document.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == '__main__':
    make_gif()
    make_markdown()
    make_pdf()
    print('Updated README.md, docs/REPORT.md, docs/TRACEABILITY.md and output/pdf/practice-report.pdf')
