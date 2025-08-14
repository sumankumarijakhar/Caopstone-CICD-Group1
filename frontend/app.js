async function getJSON(url, options = {}) {
  const res = await fetch(url, options);
  const text = await res.text();
  try { return JSON.parse(text); } catch { return { raw: text }; }
}

document.getElementById('btnHealth').addEventListener('click', async () => {
  const out = document.getElementById('healthOut');
  out.textContent = '...';
  const data = await getJSON('/api/health');
  out.textContent = JSON.stringify(data, null, 2);
});

document.getElementById('btnRefresh').addEventListener('click', async () => {
  const out = document.getElementById('itemsOut');
  out.textContent = '...';
  const data = await getJSON('/api/items');
  out.textContent = JSON.stringify(data, null, 2);
});

document.getElementById('itemForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('itemId').value.trim();
  const title = document.getElementById('itemTitle').value.trim();
  if (!id || !title) return alert('Please enter id and title');
  const out = document.getElementById('itemsOut');
  out.textContent = 'Saving...';
  const data = await getJSON('/api/items', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, title })
  });
  out.textContent = JSON.stringify(data, null, 2);
});
