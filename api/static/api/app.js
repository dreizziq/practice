'use strict';
const element = (id) => document.getElementById(id);
const form = element('note-form');
const readOnly = document.body.dataset.readOnly === 'true';
let editUrl = null;
let pageUrl = '/api/note/?limit=6';
let previousUrl = null;
let nextUrl = null;

function status(message, isError = false) {
  element('status').textContent = message;
  element('status').className = isError ? 'error' : '';
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options, headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value, ...options.headers}
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Ошибка ${response.status}. ${body.slice(0, 350)}`);
  }
  return response.status === 204 || response.status === 201 ? null : response.json();
}

function resetEditor() {
  editUrl = null;
  form.reset();
  element('form-title').textContent = 'Новая заметка';
  element('save').textContent = 'Создать заметку';
  element('cancel').hidden = true;
}

function editNote(note) {
  editUrl = note.resource_uri;
  element('title').value = note.title;
  element('body').value = note.body;
  element('form-title').textContent = 'Изменение заметки';
  element('save').textContent = 'Сохранить';
  element('cancel').hidden = false;
  element('title').focus();
  location.hash = 'create';
}

async function deleteNote(note, button) {
  if (!confirm(`Удалить заметку «${note.title}»?`)) return;
  button.disabled = true;
  try {
    await request(note.resource_uri, {method: 'DELETE'});
    if (editUrl === note.resource_uri) resetEditor();
    await loadNotes();
    status('Заметка удалена.');
  } catch (error) { status(error.message, true); }
  finally { button.disabled = false; }
}

async function loadNotes(url = pageUrl) {
  const data = await request(url);
  if (!data.objects.length && data.meta.previous) return loadNotes(data.meta.previous);
  pageUrl = url;
  previousUrl = data.meta.previous;
  nextUrl = data.meta.next;
  element('previous').disabled = !previousUrl;
  element('next').disabled = !nextUrl;
  element('count').textContent = `(${data.meta.total_count})`;
  const list = element('note-list');
  list.replaceChildren();
  if (!data.objects.length) {
    const empty = document.createElement('p');
    empty.className = 'empty';
    empty.textContent = 'Пока пусто. Создайте первую заметку в форме слева.';
    list.append(empty);
  }
  for (const note of data.objects) {
    const card = element('note-template').content.cloneNode(true);
    card.querySelector('h3').textContent = note.title;
    card.querySelector('.note-body').textContent = note.body;
    card.querySelector('.edit').onclick = () => editNote(note);
    card.querySelector('.delete').onclick = (event) => deleteNote(note, event.currentTarget);
    if (readOnly) card.querySelector('.actions').remove();
    list.append(card);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  element('save').disabled = true;
  const isEdit = Boolean(editUrl);
  try {
    await request(editUrl || '/api/note/', {
      method: isEdit ? 'PUT' : 'POST',
      body: JSON.stringify({title: element('title').value, body: element('body').value})
    });
    resetEditor();
    await loadNotes();
    status(isEdit ? 'Изменения сохранены.' : 'Заметка создана.');
  } catch (error) { status(error.message, true); }
  finally { element('save').disabled = false; }
});
element('cancel').onclick = resetEditor;
element('refresh').onclick = () => loadNotes().catch((error) => status(error.message, true));
element('previous').onclick = () => loadNotes(previousUrl).catch((error) => status(error.message, true));
element('next').onclick = () => loadNotes(nextUrl).catch((error) => status(error.message, true));
loadNotes().catch((error) => status(error.message, true));
