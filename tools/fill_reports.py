from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
import hashlib, json, sys, importlib.util
from lxml import etree as E
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/reports'
QA=ROOT/'tmp/word-qa'
OUT.mkdir(parents=True,exist_ok=True)
QA.mkdir(parents=True,exist_ok=True)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+NS['w']+'}'
ARTICLE='https://codeburst.io/create-a-django-api-in-under-20-minutes-2a082a60f6f3'
CATALOG='https://github.com/practical-tutorials/project-based-learning#python'
CONFIG=json.loads((ROOT/'submission.json').read_text(encoding='utf-8'))
REPO=CONFIG['github_url'].rstrip('/')

def make_diagrams():
    font=ImageFont.truetype('C:/Windows/Fonts/times.ttf',32)
    bold=ImageFont.truetype('C:/Windows/Fonts/timesbd.ttf',35)
    small=ImageFont.truetype('C:/Windows/Fonts/times.ttf',28)
    result=[]
    im=Image.new('RGB',(1500,280),'white'); d=ImageDraw.Draw(im)
    for x,title,sub in [(15,'Браузер','HTML / CSS / JavaScript'),(535,'Django + TastyPie','REST API / NoteResource'),(1055,'База данных','SQLite / PostgreSQL')]:
        d.rectangle((x,65,x+430,220),outline='black',width=3)
        d.text((x+215,110),title,font=bold,anchor='mm',fill='black')
        d.text((x+215,164),sub,font=small,anchor='mm',fill='black')
    for x,label in [(445,'JSON'),(965,'ORM')]:
        d.line((x,143,x+80,143),fill='black',width=3)
        d.polygon([(x+80,143),(x+64,135),(x+64,151)],fill='black')
        d.text((x+40,101),label,font=small,anchor='mm',fill='black')
    im.save(QA/'architecture.png');result.append(QA/'architecture.png')
    im=Image.new('RGB',(1200,440),'white');d=ImageDraw.Draw(im)
    d.rectangle((80,20,1120,420),outline='black',width=3)
    d.line((80,95,1120,95),fill='black',width=3)
    d.text((600,58),'api_note — заметки',font=bold,anchor='mm',fill='black')
    for y,t in [(130,'id: BIGINT — первичный ключ'),(205,'title: VARCHAR(200) — обязательный заголовок'),(280,'body: TEXT — обязательный текст'),(355,'created_at: DATETIME — время создания')]:
        d.text((110,y),t,font=font,fill='black')
    im=Image.new('RGB',(1500,600),'white');d=ImageDraw.Draw(im)
    for box in [(20,70,590,460),(830,70,1480,550)]: d.rectangle(box,outline='black',width=3)
    d.text((305,110),'auth_user',font=bold,anchor='mm',fill='black')
    d.text((50,165),'id — PK\nusername — unique\npassword — хеш\nis_superuser — роль',font=font,fill='black',spacing=23)
    d.text((1155,110),'api_note',font=bold,anchor='mm',fill='black')
    d.text((860,165),'id — PK\nowner_id — FK → auth_user.id\ntitle — varchar(200)\nbody — text\ncreated_at — datetime',font=font,fill='black',spacing=23)
    d.line((590,290,830,290),fill='black',width=3)
    d.text((710,250),'1 → много',font=font,anchor='mm',fill='black')
    im.save(QA/'erd.png');result.append(QA/'erd.png')
    im=Image.new('RGB',(1500,450),'white');d=ImageDraw.Draw(im)
    d.ellipse((75,110,145,180),outline='black',width=4);d.line((110,180,110,310),fill='black',width=4)
    d.line((45,220,175,220),fill='black',width=4);d.line((110,310,50,380),fill='black',width=4);d.line((110,310,170,380),fill='black',width=4)
    d.text((110,415),'Посетитель',font=small,anchor='mm',fill='black')
    for y,label in [(55,'Создать заметку'),(160,'Прочитать заметки'),(265,'Изменить заметку'),(370,'Удалить заметку')]:
        d.line((185,230,420,y),fill='black',width=2)
        d.ellipse((420,y-42,1410,y+42),outline='black',width=3)
        d.text((915,y),label,font=font,anchor='mm',fill='black')
    im.save(QA/'usecase.png');result.append(QA/'usecase.png')
    return result

def text(p): return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def settext(p,value):
    for c in list(p):
        if c.tag!=W+'pPr': p.remove(c)
    r=E.SubElement(p,W+'r');rp=E.SubElement(r,W+'rPr')
    for name,attrs in [('rFonts',{'ascii':'Times New Roman','hAnsi':'Times New Roman','cs':'Times New Roman'}),('sz',{'val':'24'}),('szCs',{'val':'24'}),('color',{'val':'000000'})]:
        E.SubElement(rp,W+name,{W+k:v for k,v in attrs.items()})
    for i,line in enumerate(value.split('\n')):
        if i:E.SubElement(r,W+'br')
        t=E.SubElement(r,W+'t');t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=line

def pagebreak(p):
    pp=p.find(W+'pPr')
    if pp is None:pp=E.Element(W+'pPr');p.insert(0,pp)
    if pp.find(W+'pageBreakBefore') is None:E.SubElement(pp,W+'pageBreakBefore')

def strip_highlights(rt):
    for el in list(rt.xpath('//w:highlight | //w:rPr/w:shd',namespaces=NS)):
        el.getparent().remove(el)
    for el in list(rt.xpath('//w:shd',namespaces=NS)):
        fill=el.get(W+'fill','').upper()
        if fill not in ('','AUTO','FFFFFF','000000','E7E6E6','D9D9D9'):
            el.getparent().remove(el)
    for el in rt.xpath('//w:color',namespaces=NS):
        if el.get(W+'val','').upper() in ('FF0000','0000FF','00FFFF','FFFF00'):
            el.set(W+'val','000000')

def build(source,mod,diagrams):
    data={}
    with ZipFile(source) as z:
        infos=z.infolist()
        data={i.filename:z.read(i.filename) for i in infos}
    rt=E.fromstring(data['word/document.xml'])
    paras=rt.xpath('//w:p',namespaces=NS)
    first=395 if mod=='11' else 397
    before=[text(p) for p in paras[:first]]
    off=0 if mod=='11' else 2
    def p(i):return paras[i+off]
    def s(i,t):settext(p(i),t)
    s(396,'Название проекта: Notable — веб-приложение для заметок')
    s(397,'Ссылка на проект из каталога: '+CATALOG+'\nУчебный проект: '+ARTICLE)
    s(399,'Notable предназначен для хранения личных заметок. Пользователь входит в аккаунт и работает со своими записями. Аудитор имеет доступ к чтению всех заметок без права изменения; суперпользователь управляет всеми записями. Браузерный интерфейс обращается к REST API на Django и TastyPie.')
    features=['Вход, выход и сессионная авторизация с CSRF-защитой.','Связь пользователей и заметок, ограничения базы данных.','Разграничение доступа: владелец, аудитор, администратор.','CRUD заметок, форма и страницы списка.','Проверка обязательных полей и длины заголовка.','Резервная копия SQLite с контрольной суммой SHA-256.','Восстановление в отдельную базу и проверка целостности.','Шестнадцать автоматических тестов.','README, тестовые аккаунты и GIF-демонстрация.']
    s(401,'\n'.join(f'{i+1}. {v}' for i,v in enumerate(features)))
    s(404,'Notable');s(406,ARTICLE);s(408,REPO)
    s(412,'HTML, CSS, JavaScript, Django Templates')
    s(414,'Python, Django 5.2.17, TastyPie 0.15.1')
    s(416,'SQLite; настройки поддерживают подключение PostgreSQL')
    s(418,'Да; сессии Django')
    s(420,'student1 / PracticeDemo2026!\nstudent2 / PracticeDemo2026!\nauditor / PracticeDemo2026!\nСоздаются командой seed_demo в локальном режиме.')
    s(427,'Страница на HTML и CSS содержит форму и список заметок. JavaScript отправляет запросы к API через fetch. Django сопоставляет адрес запроса с ресурсом NoteResource. TastyPie выполняет операцию над моделью Note. Django ORM читает и изменяет записи в базе данных. Сервер возвращает JSON, после чего браузер обновляет список. Внешние API не используются.')
    s(432,'auth_user хранит пользователей и хеши паролей. api_note содержит заметки и обязательный внешний ключ owner_id на пользователя. Связь: один пользователь — много заметок. Удаление владельца с заметками запрещено. Роль аудитора задают auth_group и auth_user_groups. В БД действуют ограничения непустого заголовка и текста.')
    scenarios=[('Создать заметку','Ввести заголовок и текст; нажать «Создать заметку»; увидеть новую карточку.'),('Просмотреть заметки','Открыть главную страницу; прочитать карточки; при необходимости перейти на следующую страницу.'),('Изменить заметку','Нажать «Изменить»; исправить текст; сохранить; проверить обновлённую карточку.'),('Удалить заметку','Нажать «Удалить»; подтвердить действие; убедиться, что карточка исчезла.')]
    for i,(a,b) in enumerate(scenarios):s(439+2*i,a);s(440+2*i,b)
    api=[('GET','/api/note/','Список заметок','200; objects и meta'),('POST','/api/note/','Создание','{"title":"План","body":"Текст"}; 201'),('GET','/api/note/{id}/','Чтение записи','200; title, body, resource_uri'),('PUT','/api/note/{id}/','Изменение','{"title":"Новый","body":"Текст"}; 204'),('DELETE','/api/note/{id}/','Удаление','204; затем GET возвращает 404')]
    for i,row in enumerate(api):
        for j,value in enumerate(row):s(453+4*i+j,value)
    trace=[('Вход и выход','notable_django/urls.py'),('CRUD и пагинация','api/resources.py'),('Разграничение доступа','api/permissions.py'),('Связи и ограничения БД','api/models.py'),('Интерфейс и CSRF-токен','api/static/api/app.js'),('Тестовые аккаунты','api/management/commands/seed_demo.py'),('Резервное копирование','api/management/commands/backup_database.py'),('Восстановление и целостность','api/db_backup.py'),('Проверка прав и восстановления','api/tests.py'),('Результаты проверки копии','docs/backup-verification.json')]
    for i in range(10):
        a,b=trace[i] if i<len(trace) else ('','')
        s(478+3*i,a);s(479+3*i,REPO+'/blob/main/'+b);s(480+3*i,'')
    s(512,'GIF');s(514,REPO+'/blob/main/docs/demo.gif')
    s(516,'Заполнение формы, создание заметки, изменение её текста и сохранённый результат.')
    s(518,'Файл docs/demo.gif в комплекте проекта; демонстрация выполнена локально.')
    s(521,'README содержит описание, стек и инструкцию локального запуска')
    s(522,'Да')
    s(524,'Нет');s(526,'');s(528,'')
    s(530,'1. Добавлены права доступа и CSRF-защита.\n2. Проверены копирование и восстановление SQLite.\n3. Успешно пройдены 16 тестов и Django check.')
    spec=importlib.util.spec_from_file_location('report_builder',ROOT/'tools/project_content.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    conclusion=list(m.CONCLUSION)
    if mod=='11':
        conclusion[0]='В рамках проекта по ПМ11 подготовлена реляционная база приложения Notable, средства управления доступом и резервного копирования. Определены сущности пользователя и заметки, внешний ключ и ограничения целостности. Реализованы роли владельца, аудитора и администратора. Подтверждены восстановление SQLite в отдельный файл и сохранность записей. Для взаимодействия с базой используется REST API и браузерный интерфейс.'
    else:
        conclusion[0]='В рамках проекта по ПМ02 подготовлено приложение Notable, объединяющее браузерный интерфейс, REST API и модуль хранения заметок. Определены границы компонентов и формат обмена данными. Клиентская часть отправляет HTTP-запросы, серверный ресурс обрабатывает их через модель Note, а база сохраняет результат. Для проверки взаимодействия подготовлены автоматические тесты и демонстрация основных действий.'
    anchor=p(533);s(533,conclusion[0])
    for paragraph in conclusion[1:]:
        new=deepcopy(anchor);settext(new,paragraph);anchor.addnext(new);anchor=new
    for paragraph in [p(533)]+list(p(533).itersiblings())[:len(conclusion)-1]:
        pp=paragraph.find(W+'pPr')
        if pp is None:pp=E.Element(W+'pPr');paragraph.insert(0,pp)
        spacing=pp.find(W+'spacing')
        if spacing is None:spacing=E.SubElement(pp,W+'spacing')
        spacing.set(W+'line','300');spacing.set(W+'lineRule','auto');spacing.set(W+'after','120')
    # Replace only report instructions, leaving every unrelated form unchanged.
    for i in [421,424,429,434,448,474,509,510,520,532]:
        el=p(i);el.getparent().remove(el)
    # Remove the unused passport row.
    row=p(409).getparent().getparent();row.getparent().remove(row)
    trace_table=p(475).getparent().getparent().getparent()
    tp=trace_table.find(W+'tblPr')
    layout=tp.find(W+'tblLayout')
    if layout is None:layout=E.SubElement(tp,W+'tblLayout')
    layout.set(W+'type','fixed')
    for row in trace_table.findall(W+'tr'):
        cells=row.findall(W+'tc')
        if len(cells)==3: row.remove(cells[-1])
    grid=trace_table.find(W+'tblGrid')
    if grid is not None and len(grid)==3:
        grid.remove(grid[-1]);grid[0].set(W+'w','2700');grid[1].set(W+'w','6600')
    for row in trace_table.findall(W+'tr'):
        for cell,width in zip(row.findall(W+'tc'),['2700','6600']):
            tcw=cell.find('./'+W+'tcPr/'+W+'tcW')
            if tcw is not None:tcw.set(W+'w',width)
    # Correct only verified template defects; preserve signatures and unknown data.
    if mod=='11':
        settext(paras[386],'ПМ11')
        settext(paras[372],'М.П. «___» __________ 20__ г.')
        before[386]='ПМ11';before[372]='М.П. «___» __________ 20__ г.'
    else:
        settext(paras[199],'108')
        before[199]='108'
    # Inline pictures use a separate temporary package; existing Word parts stay intact.
    rel=E.fromstring(data['word/_rels/document.xml.rels'])
    for j,(slot,img) in enumerate(zip([425,430,435],diagrams)):
        dummy=Document();run=dummy.add_paragraph().add_run();run.add_picture(str(img),width=Inches(6.2))
        drawing=deepcopy(run._r)
        rid=f'rIdNotableDiagram{j+1}'
        for blip in drawing.xpath('.//*[local-name()="blip"]'):blip.set('{'+NS['r']+'}embed',rid)
        for dp in drawing.xpath('.//*[local-name()="docPr"]'):dp.set('id',str(900+j));dp.set('descr',['Архитектура приложения','Модель данных Note','Сценарии использования'][j])
        target=p(slot);settext(target,'');target.remove(target[-1]);target.append(drawing)
        E.SubElement(rel,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',Id=rid,Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',Target=f'media/notable-{j}.png')
        data[f'word/media/notable-{j}.png']=img.read_bytes()
    # Make source references clickable while preserving their visible text.
    import re
    for j, run in enumerate(rt.xpath('//w:r[w:t]', namespaces=NS)):
        value=''.join(run.xpath('./w:t/text()',namespaces=NS))
        if re.fullmatch(r'https://\S+',value):
            rid=f'rIdNotableLink{j}'
            link=E.Element(W+'hyperlink');link.set('{'+NS['r']+'}id',rid)
            run.addprevious(link);link.append(run)
            if value.startswith(REPO+'/blob/main/'):
                run.find(W+'t').text=value.removeprefix(REPO+'/blob/main/')
            E.SubElement(rel,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',Id=rid,Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',Target=value,TargetMode='External')
    data['word/_rels/document.xml.rels']=E.tostring(rel,xml_declaration=True,encoding='UTF-8',standalone=True)
    types=E.fromstring(data['[Content_Types].xml'])
    if not any(e.get('Extension')=='png' for e in types):
        E.SubElement(types,'{http://schemas.openxmlformats.org/package/2006/content-types}Default',Extension='png',ContentType='image/png')
        data['[Content_Types].xml']=E.tostring(types,xml_declaration=True,encoding='UTF-8',standalone=True)
    for i in [402,422,433,473,508,531]:pagebreak(p(i))
    for para in rt.xpath('//w:p',namespaces=NS):
        if para in paras[first:] and text(para).startswith(('1. Выбран','2. Технический','3. Архитектура','3.1 ','3.2 ','3.3 ','3.4 ','4. Таблица','5. Демонстрация','6. Репозиторий','7. Вывод')):
            pp=para.find(W+'pPr')
            if pp is None:pp=E.Element(W+'pPr');para.insert(0,pp)
            E.SubElement(pp,W+'keepNext')
    # Keep report table rows whole and repeat headers; do not touch official tables.
    for tbl in rt.xpath('//w:tbl',namespaces=NS)[9:]:
        for row in tbl.findall(W+'tr'):
            pr=row.find(W+'trPr')
            if pr is None:pr=E.Element(W+'trPr');row.insert(0,pr)
            E.SubElement(pr,W+'cantSplit')
        if len(tbl.findall(W+'tr'))>0:
            pr=tbl.findall(W+'tr')[0].find(W+'trPr');E.SubElement(pr,W+'tblHeader')
    data['word/document.xml']=E.tostring(rt,xml_declaration=True,encoding='UTF-8',standalone=True)
    changes=[]
    for name,content in list(data.items()):
        if name.startswith('word/') and name.endswith('.xml'):
            tree=E.fromstring(content);old=E.tostring(tree);strip_highlights(tree)
            if E.tostring(tree)!=old:data[name]=E.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
    # Verify official content and dates were not filled or rewritten.
    after=E.fromstring(data['word/document.xml'])
    assert [text(x) for x in after.xpath('//w:p',namespaces=NS)[:first]]==before
    target=OUT/f'Отчет_ПМ{mod}_заполненный.docx'
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        known=set()
        for info in infos:z.writestr(info,data[info.filename]);known.add(info.filename)
        for name in data.keys()-known:z.writestr(name,data[name])
    with ZipFile(source) as a,ZipFile(target) as b:
        changes=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    (QA/f'changes-{mod}.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'changed_parts':changes,'official_text_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(str(target).encode('ascii','backslashreplace').decode())

images=make_diagrams()
for mod in ['11','02']:
    build(ROOT/'docs/templates'/f'pm{mod}.docx',mod,images)
