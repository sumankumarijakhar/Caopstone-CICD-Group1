async function getJSON(url, options = {}) {
  const res = await fetch(url, options);
  const txt = await res.text();
  try { return JSON.parse(txt); } catch { return { raw: txt }; }
}

const api = {
  health: () => getJSON('/api/health'),
  list:   () => getJSON('/api/items'),
  stats:  () => getJSON('/api/stats'),
  add:    (id, title) => getJSON('/api/items', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, title })
  }),
  del:    (id) => getJSON(`/api/items/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  update: (id, title) => getJSON(`/api/items/${encodeURIComponent(id)}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  }),
};

const el = (s) => document.querySelector(s);

async function refresh() {
  el('#itemsOut').textContent = '...';
  const [list, stats] = await Promise.all([api.list(), api.stats()]);
  el('#stats').textContent = `${stats.count ?? (list.items?.length || 0)} items`;

  const items = list.items || [];
  const rows = items.map(it => `
    <tr>
      <td>${it.id}</td>
      <td>
        <input class="title-input" data-id="${it.id}" value="${(it.title ?? '').replace(/"/g,'&quot;')}">
      </td>
      <td class="actions">
        <button class="save" data-id="${it.id}">Save</button>
        <button class="del" data-id="${it.id}">Delete</button>
      </td>
    </tr>`).join('');

  el('#itemsOut').innerHTML = `<table class="grid">
    <thead><tr><th>ID</th><th>Title</th><th></th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

el('#btnHealth').addEventListener('click', async () => {
  el('#healthOut').textContent = '...';
  const data = await api.health();
  el('#healthOut').textContent = JSON.stringify(data, null, 2);
});

el('#btnRefresh').addEventListener('click', refresh);

el('#itemForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = el('#itemId').value.trim();
  const title = el('#itemTitle').value.trim();
  if (!id || !title) return alert('Please enter id and title');
  const r = await api.add(id, title);
  if (r.error) alert(r.error);
  await refresh();
  el('#itemTitle').value = '';
});

el('#itemsOut').addEventListener('click', async (e) => {
  const t = e.target;
  if (t.classList.contains('del')) {
    if (confirm('Delete this item?')) {
      await api.del(t.dataset.id);
      await refresh();
    }
  }
  if (t.classList.contains('save')) {
    const id = t.dataset.id;
    const input = el(`.title-input[data-id="${CSS.escape(id)}"]`);
    const title = input.value.trim();
    if (!title) return alert('Title required');
    const r = await api.update(id, title);
    if (r.error) alert(r.error);
    await refresh();
  }
});

// initial paint
refresh().catch(console.error);
