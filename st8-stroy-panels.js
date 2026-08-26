/**
 * ST8-STROY — панели Финансы и Фото
 * Подключить после основного скрипта PWA.
 * Зависимости: H(), fmt(), now(), S.get/set(), aiCall(), objects[]
 */

// ─── инъекция стилей ────────────────────────────────────────────────────────
(function injectStyles() {
  if (document.getElementById('st8-stroy-css')) return;
  const s = document.createElement('style');
  s.id = 'st8-stroy-css';
  s.textContent = `
:root{--accent:#F5C518;--bg:#0e0e0e;--surface:#161616;--surface2:#1f1f1f;--surface3:#272727;--border:rgba(255,255,255,.08);--text:#f0f0f0;--text-muted:rgba(240,240,240,.45);--radius:12px;}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.65rem;margin-bottom:1.25rem;}
@media(max-width:600px){.kpi-grid{grid-template-columns:repeat(2,1fr);}}
.kpi{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:.9rem 1rem;}
.kpi-val{font-size:1.35rem;font-weight:800;line-height:1.1;margin-bottom:.2rem;font-family:'Oswald',sans-serif;color:var(--accent);}
.kpi-lbl{font-size:.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.07em;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;margin-bottom:.75rem;}
.badge{display:inline-block;padding:.18rem .48rem;border-radius:5px;font-size:.66rem;font-weight:600;white-space:nowrap;}
.badge-green{background:rgba(34,197,94,.13);color:#86efac;}
.badge-yellow{background:rgba(234,179,8,.13);color:#fde047;}
.badge-red{background:rgba(239,68,68,.13);color:#fca5a5;}
.badge-accent{background:rgba(245,197,24,.13);color:var(--accent);}
.sec-hd{display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin-bottom:1.1rem;flex-wrap:wrap;}
.sec-hd h2{font-size:1.05rem;font-weight:700;}
.btn{padding:.6rem 1.2rem;border-radius:8px;font-size:.82rem;font-weight:600;cursor:pointer;border:none;transition:all .2s;display:inline-flex;align-items:center;gap:.35rem;}
.btn-accent{background:var(--accent);color:#0a0a0a;}
.btn-accent:hover{filter:brightness(1.1);}
.btn-ghost{background:var(--surface2);color:var(--text);border:1px solid var(--border);}
.btn-ghost:hover{background:var(--surface3);}
.btn-danger{background:rgba(239,68,68,.12);color:#fca5a5;border:1px solid rgba(239,68,68,.25);}
.mc-item{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:.5rem;overflow:hidden;}
.mc-row{display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;cursor:pointer;user-select:none;}
.mc-row:hover{background:var(--surface3);}
.mc-lbl{flex:1;font-size:.85rem;font-weight:600;}
.mc-body{padding:0 1rem 1rem;display:none;}
.mc-body.open{display:block;}
.fin-stage-row{display:grid;grid-template-columns:1fr 100px 100px 80px;gap:.5rem;align-items:center;padding:.45rem 0;border-bottom:1px solid var(--border);font-size:.8rem;}
.fin-stage-row:last-child{border-bottom:none;}
.fin-stage-lbl{color:var(--text-muted);}
.fin-inp{background:var(--surface3);border:1px solid var(--border);border-radius:6px;padding:.35rem .55rem;color:var(--text);font-size:.8rem;width:100%;outline:none;text-align:right;}
.fin-inp:focus{border-color:var(--accent);}
.prog-bar{height:5px;background:var(--surface3);border-radius:3px;overflow:hidden;margin:.5rem 0 .25rem;}
.prog-fill{height:100%;border-radius:3px;background:var(--accent);transition:width .4s;}
.gap-gap{gap:.5rem;}
.cash-warn{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);border-radius:10px;padding:.85rem 1rem;font-size:.82rem;color:#fca5a5;margin-bottom:.75rem;}
.cash-ok{background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.2);border-radius:10px;padding:.85rem 1rem;font-size:.82rem;color:#86efac;margin-bottom:.75rem;}
.ph-tabs{display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:1rem;}
.ph-tab{padding:.35rem .85rem;border-radius:20px;font-size:.75rem;font-weight:600;cursor:pointer;border:1.5px solid var(--border);color:var(--text-muted);background:transparent;transition:all .2s;}
.ph-tab.active{border-color:var(--accent);color:var(--accent);background:rgba(245,197,24,.07);}
.ph-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.65rem;}
@media(min-width:600px){.ph-grid{grid-template-columns:repeat(3,1fr);}}
.ph-card{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;position:relative;}
.ph-card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:var(--surface3);}
.ph-card-body{padding:.55rem .65rem;}
.ph-card-caption{font-size:.75rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ph-card-date{font-size:.65rem;color:var(--text-muted);margin-top:.1rem;}
.ph-del{position:absolute;top:.4rem;right:.4rem;background:rgba(0,0,0,.6);border:none;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:.65rem;color:#fca5a5;line-height:1;}
.ph-del:hover{background:rgba(239,68,68,.5);}
.ph-empty{text-align:center;padding:2.5rem 1rem;color:var(--text-muted);font-size:.82rem;}
.obj-sel{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:.55rem .75rem;color:var(--text);font-size:.85rem;outline:none;width:100%;}
.obj-sel:focus{border-color:var(--accent);}
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:flex-end;justify-content:center;z-index:1000;padding:0;}
.modal-bg.hidden{display:none;}
.modal{background:var(--surface);border-radius:20px 20px 0 0;width:100%;max-width:560px;padding:1.5rem;max-height:85vh;overflow-y:auto;}
.modal-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;}
.modal-hd h2{font-size:1rem;font-weight:700;}
.close-btn{background:var(--surface2);border:1px solid var(--border);border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:.85rem;color:var(--text);}
.field{display:flex;flex-direction:column;gap:.35rem;}
.field label{font-size:.68rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em;}
.field input,.field select,.field textarea{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:.55rem .75rem;color:var(--text);font-size:.85rem;outline:none;transition:border-color .2s;}
.field input:focus,.field select:focus,.field textarea:focus{border-color:var(--accent);}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:.65rem;}
@media(max-width:480px){.form-grid{grid-template-columns:1fr;}}
.mt-sm{margin-top:.5rem;}
.mt-md{margin-top:1rem;}
.text-muted{color:var(--text-muted);}
.cam-btn{background:var(--accent);color:#0a0a0a;border:none;border-radius:12px;padding:1rem 1.5rem;font-size:1rem;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:.5rem;justify-content:center;width:100%;margin-bottom:.75rem;}
.cam-btn:hover{filter:brightness(1.1);}
`;
  document.head.appendChild(s);
})();

// ═══════════════════════════════════════════════════════════════════════════
// PANEL 1 — ФИНАНСЫ
// Data key: 's_fin'  [{id, objectId, stage, plan, fact, date, note}]
// ═══════════════════════════════════════════════════════════════════════════

const FIN_STAGES = ['фундамент','каркас/стены','кровля','инженерка','отделка','благоустройство'];

function _finData() { return S.get('s_fin') || []; }
function _finSave(d) { S.set('s_fin', d); }

/** Get/create stage rows for one objectId */
function _stageRows(objectId) {
  const all = _finData();
  return FIN_STAGES.map(stage => {
    const row = all.find(r => r.objectId === objectId && r.stage === stage);
    return row || { id: `${objectId}_${stage}`, objectId, stage, plan: 0, fact: 0, date: now(), note: '' };
  });
}

/** Persist edited stage value */
function finEdit(objectId, stage, field, val) {
  const all = _finData();
  const idx = all.findIndex(r => r.objectId === objectId && r.stage === stage);
  const v = parseFloat(val) || 0;
  if (idx >= 0) { all[idx][field] = v; }
  else { all.push({ id: `${objectId}_${stage}`, objectId, stage, plan: 0, fact: 0, date: now(), note: '', [field]: v }); }
  _finSave(all);
  _refreshFinKpi();
}

function _refreshFinKpi() {
  const el = document.getElementById('fin-kpi');
  if (el) el.outerHTML = _buildFinKpi();
}

function _buildFinKpi() {
  const all = _finData();
  let totPlan = 0, totFact = 0;
  (objects || []).forEach(o => {
    _stageRows(o.id).forEach(r => { totPlan += r.plan; totFact += r.fact; });
  });
  const dev = totFact - totPlan;
  const pct = totPlan > 0 ? Math.round(totFact / totPlan * 100) : 0;
  const devCls = dev <= 0 ? 'badge-green' : 'badge-red';
  return `<div class="kpi-grid" id="fin-kpi">
    <div class="kpi"><div class="kpi-val">${fmt(totPlan)} ₽</div><div class="kpi-lbl">план итого</div></div>
    <div class="kpi"><div class="kpi-val">${fmt(totFact)} ₽</div><div class="kpi-lbl">факт итого</div></div>
    <div class="kpi"><div class="kpi-val" style="color:${dev<=0?'#86efac':'#fca5a5'}">${dev>=0?'+':''}${fmt(dev)} ₽</div><div class="kpi-lbl">отклонение</div></div>
    <div class="kpi"><div class="kpi-val">${pct}%</div><div class="kpi-lbl">исполнение</div></div>
  </div>`;
}

function _buildFinObject(o) {
  const rows = _stageRows(o.id);
  const oPlan = rows.reduce((s, r) => s + r.plan, 0);
  const oFact = rows.reduce((s, r) => s + r.fact, 0);
  const oPct = oPlan > 0 ? Math.min(100, Math.round(oFact / oPlan * 100)) : 0;
  const oDevCls = oFact <= oPlan ? 'badge-green' : 'badge-red';

  const stageHtml = rows.map(r => {
    const dev = r.fact - r.plan;
    const devCls = dev <= 0 ? 'badge-green' : 'badge-red';
    const eid = `${o.id}_${r.stage}`;
    return `<div class="fin-stage-row">
      <span class="fin-stage-lbl">${r.stage}</span>
      <input class="fin-inp" type="number" value="${r.plan}" placeholder="план"
        onchange="finEdit('${o.id}','${H(r.stage)}','plan',this.value)" title="план">
      <input class="fin-inp" type="number" value="${r.fact}" placeholder="факт"
        onchange="finEdit('${o.id}','${H(r.stage)}','fact',this.value)" title="факт">
      <span class="badge ${devCls}" style="text-align:right">${dev>=0?'+':''}${fmt(dev)}</span>
    </div>`;
  }).join('');

  return `<div class="mc-item">
    <div class="mc-row" onclick="finToggle('fin-body-${o.id}')">
      <span class="mc-lbl">🏗 ${H(o.name)}</span>
      <span class="badge badge-accent">${oPct}%</span>
      <span class="badge ${oDevCls}">${oFact<=oPlan?'✓ в бюджете':'↑ перерасход'}</span>
      <span style="font-size:.8rem;color:var(--text-muted)">▾</span>
    </div>
    <div class="mc-body" id="fin-body-${o.id}">
      <div class="fin-stage-row" style="font-weight:700;font-size:.72rem;color:var(--text-muted)">
        <span>Этап</span><span style="text-align:right">план ₽</span><span style="text-align:right">факт ₽</span><span style="text-align:right">откл.</span>
      </div>
      ${stageHtml}
      <div class="prog-bar"><div class="prog-fill" style="width:${oPct}%"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--text-muted)">
        <span>план: ${fmt(oPlan)} ₽</span><span>факт: ${fmt(oFact)} ₽</span><span>${oPct}%</span>
      </div>
      <div style="margin-top:.75rem">
        <button class="btn btn-ghost" style="font-size:.75rem;padding:.4rem .85rem"
          onclick="finAddExpense('${o.id}')">+ Добавить расход</button>
      </div>
    </div>
  </div>`;
}

function finToggle(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('open');
}

function finAddExpense(objectId) {
  const obj = (objects || []).find(o => o.id === objectId);
  document.getElementById('fin-exp-oid').value = objectId;
  document.getElementById('fin-exp-obj-name').textContent = obj ? obj.name : objectId;
  document.getElementById('fin-exp-modal').classList.remove('hidden');
}

function finSaveExpense() {
  const objectId = document.getElementById('fin-exp-oid').value;
  const stage = document.getElementById('fin-exp-stage').value;
  const fact = parseFloat(document.getElementById('fin-exp-fact').value) || 0;
  const note = document.getElementById('fin-exp-note').value;
  const all = _finData();
  const idx = all.findIndex(r => r.objectId === objectId && r.stage === stage);
  if (idx >= 0) { all[idx].fact += fact; all[idx].note = note; }
  else { all.push({ id: `${objectId}_${stage}_${Date.now()}`, objectId, stage, plan: 0, fact, date: now(), note }); }
  _finSave(all);
  document.getElementById('fin-exp-modal').classList.add('hidden');
  // refresh panel
  const p = document.getElementById('panel-finances');
  if (p) p.innerHTML = panelFinances();
}

function panelFinances() {
  const all = _finData();
  const objs = objects || [];

  // cash gap
  let totPlan = 0, totFact = 0;
  objs.forEach(o => _stageRows(o.id).forEach(r => { totPlan += r.plan; totFact += r.fact; }));
  const gap = totFact - totPlan;
  const cashHtml = gap > 0
    ? `<div class="cash-warn">⚠️ Кассовый разрыв: перерасход ${fmt(gap)} ₽ — факт превышает план по проектам</div>`
    : `<div class="cash-ok">✓ Кассовый разрыв не обнаружен — факт в рамках плана</div>`;

  const objHtml = objs.length
    ? objs.map(_buildFinObject).join('')
    : '<div class="card text-muted" style="text-align:center;padding:2rem">Нет объектов</div>';

  return `
    <div class="sec-hd"><h2>💰 Финансы план/факт</h2></div>
    ${_buildFinKpi()}
    ${cashHtml}
    ${objHtml}
    <div class="modal-bg hidden" id="fin-exp-modal">
      <div class="modal">
        <div class="modal-hd">
          <h2>Добавить расход — <span id="fin-exp-obj-name"></span></h2>
          <button class="close-btn" onclick="document.getElementById('fin-exp-modal').classList.add('hidden')">✕</button>
        </div>
        <input type="hidden" id="fin-exp-oid">
        <div class="form-grid">
          <div class="field" style="grid-column:1/-1">
            <label>Этап</label>
            <select id="fin-exp-stage">${FIN_STAGES.map(s=>`<option value="${s}">${s}</option>`).join('')}</select>
          </div>
          <div class="field">
            <label>Сумма факт ₽</label>
            <input type="number" id="fin-exp-fact" placeholder="500000">
          </div>
          <div class="field">
            <label>Примечание</label>
            <input id="fin-exp-note" placeholder="субподряд, материалы…">
          </div>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:.5rem;margin-top:1rem">
          <button class="btn btn-ghost" onclick="document.getElementById('fin-exp-modal').classList.add('hidden')">Отмена</button>
          <button class="btn btn-accent" onclick="finSaveExpense()">💾 Сохранить</button>
        </div>
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════════════════════════
// PANEL 2 — ФОТО
// Data key: 's_photos'  [{id, objectId, stage, url, caption, date}]
// ═══════════════════════════════════════════════════════════════════════════

const PHOTO_STAGES = ['фундамент','каркас','кровля','инженерка','отделка','скрытые','готово'];

function _photoData() { return S.get('s_photos') || []; }
function _photoSave(d) { S.set('s_photos', d); }

// Active filters (module-level state)
let _phObjId = (objects && objects[0]) ? objects[0].id : null;
let _phStage = PHOTO_STAGES[0];

/** Upload to Supabase if configured, else base64 fallback */
async function uploadPhotoToSupabase(file, objectId, stage) {
  // If Supabase client (sb) is configured
  if (typeof sb !== 'undefined' && sb && sb.storage) {
    try {
      const ext = file.name.split('.').pop() || 'jpg';
      const path = `photos/${objectId}/${stage}/${Date.now()}.${ext}`;
      const { data, error } = await sb.storage.from('stroy-photos').upload(path, file, { upsert: true });
      if (!error && data) {
        const { data: urlData } = sb.storage.from('stroy-photos').getPublicUrl(path);
        return urlData?.publicUrl || null;
      }
    } catch (e) { /* fall through to base64 */ }
  }
  // Offline fallback — FileReader base64
  return new Promise(resolve => {
    const r = new FileReader();
    r.onload = e => resolve(e.target.result);
    r.onerror = () => resolve(null);
    r.readAsDataURL(file);
  });
}

async function phHandleFile(file) {
  if (!file) return;
  const url = await uploadPhotoToSupabase(file, _phObjId, _phStage);
  if (!url) { alert('Не удалось загрузить фото'); return; }
  phSaveRecord({ url, caption: file.name.replace(/\.[^.]+$/, ''), fromFile: true });
}

function phSaveRecord({ url, caption }) {
  if (!url) return;
  const all = _photoData();
  all.push({ id: `ph_${Date.now()}`, objectId: _phObjId, stage: _phStage, url: H(url), caption: caption || '', date: now().slice(0, 10) });
  _photoSave(all);
  document.getElementById('ph-add-modal').classList.add('hidden');
  _refreshPhGrid();
}

function phDelete(id) {
  if (!confirm('Удалить фото?')) return;
  _photoSave(_photoData().filter(p => p.id !== id));
  _refreshPhGrid();
}

function _refreshPhGrid() {
  const el = document.getElementById('ph-grid-wrap');
  if (el) el.innerHTML = _buildPhGrid();
}

function _buildPhGrid() {
  const photos = _photoData().filter(p => p.objectId === _phObjId && p.stage === _phStage);
  if (!photos.length) return `<div class="ph-empty">📷 Нет фото на этапе «${_phStage}»<br><span style="font-size:.72rem">Нажмите «Добавить фото»</span></div>`;
  return `<div class="ph-grid">${photos.map(p => `
    <div class="ph-card">
      <img src="${p.url}" alt="${H(p.caption)}" loading="lazy"
        onerror="this.style.background='var(--surface3)';this.style.minHeight='80px'">
      <button class="ph-del" onclick="phDelete('${p.id}')">✕</button>
      <div class="ph-card-body">
        <div style="margin-bottom:.3rem"><span class="badge badge-accent">${H(p.stage)}</span></div>
        <div class="ph-card-caption" title="${H(p.caption)}">${H(p.caption || '—')}</div>
        <div class="ph-card-date">${p.date || ''}</div>
      </div>
    </div>`).join('')}</div>`;
}

function phSelectObj(id) {
  _phObjId = id;
  _refreshPhGrid();
  // update tab counts
  document.querySelectorAll('.ph-tab-count').forEach(el => {
    const stage = el.dataset.stage;
    el.textContent = _photoData().filter(p => p.objectId === _phObjId && p.stage === stage).length || '';
  });
}

function phSelectStage(stage, btn) {
  _phStage = stage;
  document.querySelectorAll('.ph-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  _refreshPhGrid();
}

function panelPhotos() {
  const objs = objects || [];
  if (objs.length && !_phObjId) _phObjId = objs[0].id;

  const objSel = `<div class="field" style="margin-bottom:1rem">
    <label>Объект</label>
    <select class="obj-sel" onchange="phSelectObj(this.value)">
      ${objs.map(o => `<option value="${o.id}"${o.id===_phObjId?' selected':''}>${H(o.name)}</option>`).join('')}
    </select>
  </div>`;

  const tabs = `<div class="ph-tabs">
    ${PHOTO_STAGES.map((st, i) => {
      const cnt = _photoData().filter(p => p.objectId === _phObjId && p.stage === st).length;
      return `<button class="ph-tab${st===_phStage?' active':''}" onclick="phSelectStage('${st}',this)">
        ${st}${cnt ? ` <sup class="ph-tab-count" data-stage="${st}" style="color:var(--accent);font-size:.6rem">${cnt}</sup>` : `<sup class="ph-tab-count" data-stage="${st}" style="display:none"></sup>`}
      </button>`;
    }).join('')}
  </div>`;

  const addBtn = `<div style="margin-bottom:1rem">
    <button class="btn btn-accent" onclick="document.getElementById('ph-add-modal').classList.remove('hidden')">📷 Добавить фото</button>
  </div>`;

  const modal = `<div class="modal-bg hidden" id="ph-add-modal">
    <div class="modal">
      <div class="modal-hd">
        <h2>Добавить фото — ${_phStage}</h2>
        <button class="close-btn" onclick="document.getElementById('ph-add-modal').classList.add('hidden')">✕</button>
      </div>
      <label class="cam-btn">
        📸 Снять с камеры
        <input type="file" accept="image/*" capture="environment" style="display:none"
          onchange="phHandleFile(this.files[0])">
      </label>
      <label class="btn btn-ghost" style="width:100%;justify-content:center;margin-bottom:.75rem">
        🖼 Выбрать из галереи
        <input type="file" accept="image/*" style="display:none"
          onchange="phHandleFile(this.files[0])">
      </label>
      <div class="field" style="margin-bottom:.75rem">
        <label>Или вставить URL</label>
        <input id="ph-url-inp" placeholder="https://…" style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:.55rem .75rem;color:var(--text);font-size:.85rem;outline:none;width:100%">
      </div>
      <div class="field" style="margin-bottom:1rem">
        <label>Подпись</label>
        <input id="ph-caption-inp" placeholder="Армирование плиты, 2-й ряд…" style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:.55rem .75rem;color:var(--text);font-size:.85rem;outline:none;width:100%">
      </div>
      <div style="display:flex;justify-content:flex-end;gap:.5rem">
        <button class="btn btn-ghost" onclick="document.getElementById('ph-add-modal').classList.add('hidden')">Отмена</button>
        <button class="btn btn-accent" onclick="phSaveRecord({url:document.getElementById('ph-url-inp').value,caption:document.getElementById('ph-caption-inp').value})">💾 Сохранить</button>
      </div>
    </div>
  </div>`;

  return `
    <div class="sec-hd"><h2>📷 Фотодокументация</h2></div>
    ${objSel}
    ${tabs}
    ${addBtn}
    <div id="ph-grid-wrap">${_buildPhGrid()}</div>
    ${modal}`;
}
