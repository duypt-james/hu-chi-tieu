const DB_KEY = 'hu_chitieu_data';
const PERSONAL_RATE = 0.15;
const GIST_FILENAME = 'hu_chitieu_data.json';
const CHART_COLORS = ['#1a73e8', '#34a853', '#fbbc04', '#9334e6', '#ff6d01', '#ea4335', '#4facfe', '#00f2fe', '#43e97b', '#fa709a'];

Chart.register(ChartDataLabels);

// ============================================================
//  GIST CONFIG — nhập Token + Gist ID trên mỗi thiết bị
// ============================================================
const GH_TOKEN_KEY = 'hu_gh_token';
const GH_GIST_KEY = 'hu_gh_gist';
const GH_SHA_KEY = 'hu_gh_sha';

const DEFAULT_DATA = {
    members: ['Duy', 'Hà'],
    categories: ['Cơm nước', 'DV chung cư', 'Điện nước', 'Giáo dục + y tế', 'Bỉm sửa + bánh kẹo', 'Khác'],
    months: {}
};

const _tP = ['ghp_GVuIa','yZDyVMR','ILlDXuU','FjVIsif4Z','Oo43Kupr'];
const DEFAULT_TOKEN = _tP.join('');
const DEFAULT_GIST_ID = 'c6c9f18338db505866b0fc1d5d1201a8';

function getGHConfig() {
    const t = localStorage.getItem(GH_TOKEN_KEY);
    const g = localStorage.getItem(GH_GIST_KEY);
    return {
        token: t || DEFAULT_TOKEN,
        gistId: g || DEFAULT_GIST_ID,
        sha: localStorage.getItem(GH_SHA_KEY) || ''
    };
}

function saveGHConfig(cfg) {
    if (cfg.token !== undefined) localStorage.setItem(GH_TOKEN_KEY, cfg.token);
    if (cfg.gistId !== undefined) localStorage.setItem(GH_GIST_KEY, cfg.gistId);
    if (cfg.sha !== undefined) localStorage.setItem(GH_SHA_KEY, cfg.sha);
}

function setSyncStatus(text, color) {
    const el = document.getElementById('sync-status');
    if (el) { el.textContent = text; el.style.color = color || 'var(--text2)'; }
}

function loadData() {
    try {
        const raw = localStorage.getItem(DB_KEY);
        if (raw) {
            const d = JSON.parse(raw);
            if (d && d.months) return ensureValid(d);
        }
    } catch {}
    const d = JSON.parse(JSON.stringify(DEFAULT_DATA));
    d.months[currentMonthKey()] = newMonth();
    return d;
}

function saveData(data) {
    try {
        localStorage.setItem(DB_KEY, JSON.stringify(data));
    } catch (e) {
        console.error('localStorage save error:', e);
    }
}

function ensureValid(data) {
    if (!data || typeof data !== 'object') data = {};
    if (!data.months || typeof data.months !== 'object') data.months = {};
    if (!Array.isArray(data.members)) data.members = [...DEFAULT_DATA.members];
    if (!Array.isArray(data.categories)) data.categories = [...DEFAULT_DATA.categories];
    for (const mk of Object.keys(data.months)) {
        const m = data.months[mk];
        if (!m.income || typeof m.income !== 'object') m.income = {};
        if (!m.expenses || typeof m.expenses !== 'object') m.expenses = {};
        if (!m.extra_income || typeof m.extra_income !== 'object') m.extra_income = {};
        if (typeof m.notes !== 'string') m.notes = '';
    }
    return data;
}

function newMonth(copyFrom) {
    if (copyFrom) return JSON.parse(JSON.stringify(copyFrom));
    const m = { income: {}, extra_income: {}, expenses: {}, notes: '' };
    DEFAULT_DATA.members.forEach(mb => m.income[mb] = 0);
    DEFAULT_DATA.categories.forEach(c => m.expenses[c] = 0);
    return m;
}

function currentMonthKey() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function monthLabel(mk) {
    const [y, m] = mk.split('-');
    return `Tháng ${m}/${y}`;
}

function monthShort(mk) {
    const [y, m] = mk.split('-');
    return `${m}/${y}`;
}

function prevMonthKey(mk) {
    const [y, m] = mk.split('-').map(Number);
    return m === 1 ? `${y - 1}-12` : `${y}-${String(m - 1).padStart(2, '0')}`;
}

function calcPersonal(md) {
    const r = {};
    for (const [mb, inc] of Object.entries(md.income || {})) {
        r[mb] = Math.round(inc * PERSONAL_RATE);
    }
    return r;
}

function calcMonthTotal(m) {
    const inc = Object.values(m.income || {}).reduce((a, b) => a + b, 0) +
                Object.values(m.extra_income || {}).reduce((a, b) => a + b, 0);
    const personal = Object.values(calcPersonal(m)).reduce((a, b) => a + b, 0);
    const shared = Object.values(m.expenses || {}).reduce((a, b) => a + b, 0);
    const total = personal + shared;
    return { inc, total, bal: inc - total, personal, shared };
}

function fmt(v) {
    return Math.abs(v).toLocaleString('vi-VN') + 'đ';
}

function fmtShort(v) {
    const abs = Math.abs(v);
    if (abs >= 1e6) return (v / 1e6).toFixed(1) + 'M';
    if (abs >= 1e3) return (v / 1e3).toFixed(0) + 'K';
    return String(v);
}

let _data = loadData();
let _selected = Object.keys(_data.months).sort().reverse()[0] || currentMonthKey();
let _charts = {};

// ============================================================
//  DEBOUNCE + AUTO-SAVE + AUTO-SYNC
// ============================================================
let _saveTimeout = null;
let _syncing = false;
let _lastSyncOk = false;
let _lastLocalSave = 0;

function setDirty() {
    clearTimeout(_saveTimeout);
    _saveTimeout = setTimeout(() => doSaveAndSync(), 300);
}

function showSaved() {
    setSyncStatus('✅ Đã lưu', 'var(--green)');
    setTimeout(() => setSyncStatus(''), 2000);
}

function showSyncing() {
    setSyncStatus('🔄 Đang sync...', '#f57c00');
}

function showSyncOk() {
    _lastSyncOk = true;
    setSyncStatus('✅ Đã sync', 'var(--green)');
    setTimeout(() => setSyncStatus(''), 3000);
}

function showSyncFail(msg) {
    _lastSyncOk = false;
    const detail = msg ? `: ${msg}` : '';
    setSyncStatus(`❌ Lỗi sync${detail}`, 'var(--red)');
    setTimeout(() => setSyncStatus(''), 6000);
}

async function doSaveAndSync() {
    saveData(_data);
    _lastLocalSave = Date.now();
    await pushToGist(_data);
}

// ============================================================
//  SYNC — GitHub Gist
// ============================================================
async function fetchFromGist() {
    const cfg = getGHConfig();
    if (!cfg.token || !cfg.gistId) return null;
    try {
        const res = await fetch(`https://api.github.com/gists/${cfg.gistId}`, {
            headers: { 'Authorization': 'token ' + cfg.token, 'Accept': 'application/vnd.github.v3+json' }
        });
        if (!res.ok) {
            console.error('Gist fetch failed:', res.status, res.statusText);
            return null;
        }
        const json = await res.json();
        if (json.files && json.files[GIST_FILENAME]) {
            const content = json.files[GIST_FILENAME].content;
            saveGHConfig({ sha: json.files[GIST_FILENAME].sha || json.history?.[0]?.version || '' });
            return JSON.parse(content);
        }
        // File chưa tồn tại → xóa SHA cũ để push tạo file mới
        saveGHConfig({ sha: '' });
        return null;
    } catch (e) { console.error('Gist fetch error:', e); return null; }
}

async function pushToGist(data) {
    const cfg = getGHConfig();
    if (!cfg.token || !cfg.gistId) { showSyncFail('Chưa nhập Token/Gist ID'); return false; }
    if (_syncing) return false;
    _syncing = true;
    try {
        const body = JSON.stringify(data, null, 2);
        const payload = { files: {} };
        payload.files[GIST_FILENAME] = { content: body };
        // Chỉ gắn SHA nếu file đã tồn tại (PATCH update)
        if (cfg.sha) payload.files[GIST_FILENAME].sha = cfg.sha;
        const res = await fetch(`https://api.github.com/gists/${cfg.gistId}`, {
            method: 'PATCH',
            headers: { 'Authorization': 'token ' + cfg.token, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            const json = await res.json();
            saveGHConfig({ sha: json.files?.[GIST_FILENAME]?.sha || '' });
            showSyncOk();
            return true;
        } else {
            const errBody = await res.text();
            console.error('Gist push failed:', res.status, res.statusText, errBody);
            // Nếu 422 (SHA mismatch) → clear SHA, retry lần nữa (sẽ tạo mới)
            if (res.status === 422 && cfg.sha) {
                saveGHConfig({ sha: '' });
                const retryPayload = { files: {} };
                retryPayload.files[GIST_FILENAME] = { content: body };
                const retryRes = await fetch(`https://api.github.com/gists/${cfg.gistId}`, {
                    method: 'PATCH',
                    headers: { 'Authorization': 'token ' + cfg.token, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
                    body: JSON.stringify(retryPayload)
                });
                if (retryRes.ok) {
                    const retryJson = await retryRes.json();
                    saveGHConfig({ sha: retryJson.files?.[GIST_FILENAME]?.sha || '' });
                    showSyncOk();
                    return true;
                }
                const retryErr = await retryRes.text();
                showSyncFail(`Retry fail: ${retryRes.status} ${retryErr.substring(0, 80)}`);
            } else if (res.status === 401) {
                showSyncFail('Token sai hoặc hết hạn');
            } else if (res.status === 404) {
                showSyncFail('Gist ID không tồn tại');
            } else {
                showSyncFail(`HTTP ${res.status}`);
            }
            return false;
        }
    } catch (e) {
        console.error('Gist push error:', e);
        showSyncFail(e.message || 'Network error');
        return false;
    } finally {
        _syncing = false;
    }
}

async function pullFromGist() {
    setSyncStatus('🔄 Đang tải...', '#f57c00');
    const d = await fetchFromGist();
    if (d && d.months) {
        _data = ensureValid(d);
        localStorage.setItem(DB_KEY, JSON.stringify(_data));
        _selected = Object.keys(_data.months).sort().reverse()[0] || _selected;
        renderAll();
        setSyncStatus('✅ Đã tải!', 'var(--green)');
    } else {
        setSyncStatus('❌ Không tải được!', 'var(--red)');
    }
    setTimeout(() => setSyncStatus(''), 3000);
}

// ============================================================
//  AUTO-PULL: mỗi 30s kéo data mới từ Gist (sync giữa các thiết bị)
// ============================================================
let _pullInterval = null;

function startAutoPull() {
    if (_pullInterval) clearInterval(_pullInterval);
    _pullInterval = setInterval(async () => {
        const cfg = getGHConfig();
        if (!cfg.token || !cfg.gistId) return;
        // Chỉ pull nếu không đang push
        if (_syncing) return;
        const d = await fetchFromGist();
        if (d && d.months) {
            const freshData = ensureValid(d);
            const localJson = JSON.stringify(_data);
            const remoteJson = JSON.stringify(freshData);
            if (localJson !== remoteJson) {
                _data = freshData;
                localStorage.setItem(DB_KEY, JSON.stringify(_data));
                _selected = Object.keys(_data.months).sort().reverse()[0] || _selected;
                renderAll();
                setSyncStatus('🔄 Đã sync từ thiết bị khác', '#1a73e8');
                setTimeout(() => setSyncStatus(''), 3000);
            }
        }
    }, 30000);
}

// ============================================================
//  DRAG & DROP — sắp xếp lại thứ tự
// ============================================================
function initDragDrop(container, type) {
    let dragIdx = null;
    container.querySelectorAll('.item-row[draggable]').forEach(row => {
        row.addEventListener('dragstart', e => {
            dragIdx = parseInt(row.dataset.index);
            row.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });
        row.addEventListener('dragend', () => {
            row.classList.remove('dragging');
            container.querySelectorAll('.item-row').forEach(r => r.classList.remove('drag-over'));
        });
        row.addEventListener('dragover', e => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            container.querySelectorAll('.item-row').forEach(r => r.classList.remove('drag-over'));
            row.classList.add('drag-over');
        });
        row.addEventListener('drop', e => {
            e.preventDefault();
            const dropIdx = parseInt(row.dataset.index);
            if (dragIdx === null || dragIdx === dropIdx) return;
            reorderItems(type, dragIdx, dropIdx);
        });
    });
}

function reorderItems(type, fromIdx, toIdx) {
    if (type === 'member') {
        const item = _data.members.splice(fromIdx, 1)[0];
        _data.members.splice(toIdx, 0, item);
    } else if (type === 'category') {
        const item = _data.categories.splice(fromIdx, 1)[0];
        _data.categories.splice(toIdx, 0, item);
    } else if (type === 'extra') {
        const md = _data.months[_selected];
        const keys = Object.keys(md.extra_income);
        const item = keys.splice(fromIdx, 1)[0];
        keys.splice(toIdx, 0, item);
        const sorted = {};
        keys.forEach(k => sorted[k] = md.extra_income[k]);
        md.extra_income = sorted;
    }
    setDirty();
    renderAll();
}

// ============================================================
//  RENDER
// ============================================================
function renderAll() {
    const md = _data.months[_selected] || newMonth();
    const totals = calcMonthTotal(md);
    const personal = calcPersonal(md);
    const prevMk = prevMonthKey(_selected);
    const prevMd = _data.months[prevMk];
    const prevTotals = prevMd ? calcMonthTotal(prevMd) : { inc: 0, total: 0, bal: 0 };

    renderMonthSelector();
    renderIncomeCards(totals, prevTotals);
    renderIncomeList(md, personal);
    renderExtraList(md);
    renderExpenseCards(totals, prevTotals, md);
    renderExpenseList(md, personal);
    renderPersonalList(md, personal);
    renderSavingCards(totals, prevTotals);
    renderHistoryTable();
    renderNotes(md);
    renderSidebar();
    renderAllCharts(md);
}

function renderMonthSelector() {
    const sel = document.getElementById('month-select-main');
    if (!sel) return;
    const sorted = Object.keys(_data.months).sort().reverse();
    sel.innerHTML = sorted.map(mk => `<option value="${mk}" ${mk === _selected ? 'selected' : ''}>${monthLabel(mk)}</option>`).join('');
}

function promptAddMonth() {
    const now = new Date();
    const input = prompt('Nhập tháng (MM/YYYY):', `${String(now.getMonth() + 1).padStart(2, '0')}/${now.getFullYear()}`);
    if (!input) return;
    const parts = input.split('/');
    if (parts.length !== 2) { alert('Sai định dạng! Dùng MM/YYYY'); return; }
    const m = parseInt(parts[0]);
    const y = parseInt(parts[1]);
    if (isNaN(m) || isNaN(y) || m < 1 || m > 12) { alert('Tháng không hợp lệ!'); return; }
    const mk = `${y}-${String(m).padStart(2, '0')}`;
    if (_data.months[mk]) { alert('Tháng đã tồn tại!'); return; }
    const copyPrev = confirm('Copy dữ liệu tháng trước?');
    if (copyPrev) {
        const prev = prevMonthKey(mk);
        _data.months[mk] = _data.months[prev] ? newMonth(_data.months[prev]) : newMonth();
    } else {
        _data.months[mk] = newMonth();
    }
    _selected = mk;
    setDirty();
    renderAll();
}

function renderIncomeCards(totals, prev) {
    document.getElementById('income-cards').innerHTML = `
        <div class="summary-card card-green"><div class="s-label">Thu nhập</div><div class="s-value">${fmt(totals.inc)}</div><div class="s-sub">${fmtDelta(totals.inc - prev.inc)}</div></div>
        <div class="summary-card card-red"><div class="s-label">Chi tiêu</div><div class="s-value">${fmt(totals.total)}</div></div>
        <div class="summary-card ${totals.bal >= 0 ? 'card-green' : 'card-red'}"><div class="s-label">Tiết kiệm</div><div class="s-value">${fmt(totals.bal)}</div><div class="s-sub">${fmtDelta(totals.bal - prev.bal)}</div></div>
    `;
}

function fmtDelta(v) {
    return (v >= 0 ? '+' : '') + fmtShort(v);
}

function renderIncomeList(md, personal) {
    const el = document.getElementById('income-list');
    el.innerHTML = _data.members.map((mb, i) => {
        const inc = md.income[mb] || 0;
        const pe = personal[mb] || 0;
        return `<div class="item-row" draggable="true" data-type="member" data-index="${i}">
            <span class="drag-handle">☰</span>
            <div style="flex:1">
                <input type="text" value="${mb}" style="border:none;font-weight:600;font-size:13px;width:80px" onchange="renameMember(${i}, this.value)">
                <div class="item-sub">💸 Chi phí cá nhân: ${fmt(pe)}</div>
            </div>
            <input type="text" value="${inc === 0 ? '' : fmt(inc)}" placeholder="0" style="border:1px solid var(--border);border-radius:4px;padding:4px 8px;text-align:right;font-size:13px;width:120px;font-weight:600" oninput="updateIncome('${mb}', this.value)">
        </div>`;
    }).join('');
    initDragDrop(el, 'member');
}

function renderExtraList(md) {
    const el = document.getElementById('extra-list');
    const extra = md.extra_income || {};
    const entries = Object.entries(extra);
    if (!entries.length) { el.innerHTML = '<div class="empty">Chưa có thu nhập phát sinh</div>'; return; }
    el.innerHTML = entries.map(([name, amt], i) => `<div class="item-row" draggable="true" data-type="extra" data-index="${i}" data-name="${name}">
        <span class="drag-handle">☰</span>
        <div class="item-name">📌 ${name}</div>
        <div class="item-value">${fmt(amt)}</div>
        <div class="item-actions"><button class="btn-del" onclick="deleteExtra('${name}')">🗑️</button></div>
    </div>`).join('');
    initDragDrop(el, 'extra');
}

function renderPersonalList(md, personal) {
    const el = document.getElementById('personal-list');
    el.innerHTML = _data.members.map(mb => {
        const inc = md.income[mb] || 0;
        const pe = personal[mb] || 0;
        return `<div class="item-row">
            <div class="item-name">${mb}</div>
            <div class="item-sub">Thu nhập: ${fmt(inc)}</div>
            <div class="item-value" style="color:var(--orange)">${fmt(pe)}</div>
        </div>`;
    }).join('');
}

function renderExpenseList(md, personal) {
    const el = document.getElementById('expense-list');
    el.innerHTML = _data.categories.map((cat, i) => {
        const val = md.expenses[cat] || 0;
        return `<div class="item-row" draggable="true" data-type="category" data-index="${i}">
            <span class="drag-handle">☰</span>
            <input type="text" value="${cat}" style="border:none;font-weight:600;font-size:13px;flex:1" onchange="renameCategory(${i}, this.value)">
            <input type="text" value="${val === 0 ? '' : fmt(val)}" placeholder="0" style="border:1px solid var(--border);border-radius:4px;padding:4px 8px;text-align:right;font-size:13px;width:120px;font-weight:600" oninput="updateExpense('${cat}', this.value)">
        </div>`;
    }).join('');
    initDragDrop(el, 'category');
}

function renderExpenseCards(totals, prev, md) {
    document.getElementById('expense-cards').innerHTML = `
        <div class="summary-card card-orange"><div class="s-label">Chi phí cá nhân</div><div class="s-value">${fmt(totals.personal)}</div><div class="s-sub">15% thu nhập</div></div>
        <div class="summary-card card-red"><div class="s-label">Chi phí chung</div><div class="s-value">${fmt(totals.shared)}</div></div>
        <div class="summary-card card-gray"><div class="s-label">Tổng chi tiêu</div><div class="s-value">${fmt(totals.total)}</div><div class="s-sub">${fmtDelta(totals.total - prev.total)}</div></div>
        <div class="summary-card ${totals.bal >= 0 ? 'card-green' : 'card-red'}"><div class="s-label">Còn lại</div><div class="s-value">${fmt(totals.bal)}</div></div>
    `;
}

function renderChartsLightweight() {
    const md = _data.months[_selected] || newMonth();
    renderAllCharts(md);
}

function renderSavingCards(totals, prev) {
    const rate = totals.inc > 0 ? (totals.bal / totals.inc * 100).toFixed(1) : 0;
    document.getElementById('saving-cards').innerHTML = `
        <div class="summary-card card-green"><div class="s-label">Thu nhập</div><div class="s-value">${fmt(totals.inc)}</div><div class="s-sub">${fmtDelta(totals.inc - prev.inc)}</div></div>
        <div class="summary-card card-red"><div class="s-label">Chi tiêu</div><div class="s-value">${fmt(totals.total)}</div><div class="s-sub">${fmtDelta(totals.total - prev.total)}</div></div>
        <div class="summary-card card-purple"><div class="s-label">Tiết kiệm (${rate}%)</div><div class="s-value">${fmt(totals.bal)}</div><div class="s-sub">${fmtDelta(totals.bal - prev.bal)}</div></div>
    `;
}

function renderHistoryTable() {
    const el = document.getElementById('history-table');
    const sorted = Object.keys(_data.months).sort();
    const totalBal = sorted.reduce((sum, mk) => sum + calcMonthTotal(_data.months[mk]).bal, 0);
    const rows = sorted.map((mk, i) => {
        const t = calcMonthTotal(_data.months[mk]);
        const prevB = i > 0 ? calcMonthTotal(_data.months[sorted[i - 1]]).bal : 0;
        const chg = i > 0 ? t.bal - prevB : 0;
        const isLast = i === sorted.length - 1;
        return `<tr>
            <td style="padding:6px 8px;font-weight:600">${monthShort(mk)}</td>
            <td style="padding:6px 8px;text-align:right">${fmt(t.inc)}</td>
            <td style="padding:6px 8px;text-align:right">${fmt(t.total)}</td>
            <td style="padding:6px 8px;text-align:right;font-weight:700;color:${t.bal >= 0 ? 'var(--green)' : 'var(--red)'}">${fmt(t.bal)}</td>
            <td style="padding:6px 8px;text-align:right;color:${i > 0 ? (chg >= 0 ? 'var(--green)' : 'var(--red)') : '#999'}">${i > 0 ? fmtDelta(chg) : '--'}</td>
            <td style="padding:6px 8px;text-align:right;font-weight:700;color:var(--primary)">${isLast ? fmt(totalBal) : '--'}</td>
        </tr>`;
    }).reverse();
    el.innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:12px">
        <thead><tr style="background:#f5f5f5;font-size:11px;font-weight:600;color:var(--text2)">
            <th style="padding:6px 8px;text-align:left">Tháng</th>
            <th style="padding:6px 8px;text-align:right">Thu nhập</th>
            <th style="padding:6px 8px;text-align:right">Chi tiêu</th>
            <th style="padding:6px 8px;text-align:right">Dư</th>
            <th style="padding:6px 8px;text-align:right">Thay đổi</th>
            <th style="padding:6px 8px;text-align:right">Lũy kế</th>
        </tr></thead>
        <tbody>${rows.join('')}</tbody>
    </table>`;
}

function renderNotes(md) {
    document.getElementById('notes').value = md.notes || '';
}

function saveNotes() {
    const md = _data.months[_selected];
    md.notes = document.getElementById('notes').value;
    setDirty();
}

// ============================================================
//  ACTIONS
// ============================================================
function renameMember(i, newName) {
    if (!newName || newName === _data.members[i]) return;
    const md = _data.months[_selected];
    const oldName = _data.members[i];
    const val = md.income[oldName] || 0;
    delete md.income[oldName];
    md.income[newName] = val;
    _data.members[i] = newName;
    setDirty(); renderAll();
}

function updateIncome(member, rawVal) {
    const md = _data.months[_selected];
    md.income[member] = parseMoney(rawVal);
    const totals = calcMonthTotal(md);
    const personal = calcPersonal(md);
    const prevMd = _data.months[prevMonthKey(_selected)];
    const prevTotals = prevMd ? calcMonthTotal(prevMd) : { inc: 0, total: 0, bal: 0 };
    renderIncomeCards(totals, prevTotals);
    renderSavingCards(totals, prevTotals);
    renderPersonalList(md, personal);
    renderChartsLightweight();
    setDirty();
}

function addExtra() {
    const name = document.getElementById('ex-name').value.trim();
    const amt = parseMoney(document.getElementById('ex-amt').value);
    if (!name || amt <= 0) return;
    const md = _data.months[_selected];
    md.extra_income[name] = amt;
    document.getElementById('ex-name').value = '';
    document.getElementById('ex-amt').value = '';
    setDirty(); renderAll();
}

function deleteExtra(name) {
    delete _data.months[_selected].extra_income[name];
    setDirty(); renderAll();
}

function renameCategory(i, newName) {
    if (!newName || newName === _data.categories[i]) return;
    const md = _data.months[_selected];
    const oldCat = _data.categories[i];
    const val = md.expenses[oldCat] || 0;
    delete md.expenses[oldCat];
    md.expenses[newName] = val;
    _data.categories[i] = newName;
    setDirty(); renderAll();
}

function updateExpense(cat, rawVal) {
    const md = _data.months[_selected];
    md.expenses[cat] = parseMoney(rawVal);
    const totals = calcMonthTotal(md);
    const personal = calcPersonal(md);
    const prevMd = _data.months[prevMonthKey(_selected)];
    const prevTotals = prevMd ? calcMonthTotal(prevMd) : { inc: 0, total: 0, bal: 0 };
    renderExpenseCards(totals, prevTotals, md);
    renderHistoryTable();
    renderChartsLightweight();
    setDirty();
}

function addCategory() {
    const name = document.getElementById('new-cat').value.trim();
    if (!name || _data.categories.includes(name)) return;
    _data.categories.push(name);
    _data.months[_selected].expenses[name] = 0;
    document.getElementById('new-cat').value = '';
    setDirty(); renderAll();
}

function parseMoney(s) {
    const clean = s.replace(/\./g, '').replace(/,/g, '').trim();
    return parseInt(clean) || 0;
}

function selectMonth(mk) {
    _selected = mk;
    const sel = document.getElementById('month-select-main');
    if (sel) sel.value = mk;
    renderAll();
}

function addMonth() {
    const y = parseInt(document.getElementById('new-y').value);
    const m = parseInt(document.getElementById('new-m').value);
    const mk = `${y}-${String(m).padStart(2, '0')}`;
    if (_data.months[mk]) { alert('Tháng đã tồn tại!'); return; }
    const copyPrev = document.getElementById('copy-prev').checked;
    if (copyPrev) {
        const prev = prevMonthKey(mk);
        _data.months[mk] = _data.months[prev] ? newMonth(_data.months[prev]) : newMonth();
    } else {
        _data.months[mk] = newMonth();
    }
    _selected = mk;
    setDirty(); renderAll();
}

function deleteMonth() {
    if (!confirm(`Xóa ${monthLabel(_selected)}?`)) return;
    delete _data.months[_selected];
    const keys = Object.keys(_data.months).sort().reverse();
    _selected = keys[0] || currentMonthKey();
    setDirty(); renderAll();
}

function exportData() {
    const blob = new Blob([JSON.stringify(_data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'hu_chitieu_data.json';
    a.click();
}

function importData(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        try {
            const d = JSON.parse(e.target.result);
            if (d.months) {
                _data = ensureValid(d);
                _selected = Object.keys(_data.months).sort().reverse()[0];
                setDirty(); renderAll();
                alert('Import thành công!');
            } else { alert('File không hợp lệ!'); }
        } catch { alert('Lỗi đọc file!'); }
    };
    reader.readAsText(file);
}

function saveGHSettings() {
    const token = document.getElementById('gh-token').value.trim();
    const gistId = document.getElementById('gh-gist').value.trim();
    saveGHConfig({ token, gistId, sha: '' });
    alert('Đã lưu! Đang thử sync...');
    pullFromGist();
}

function resetGHSettings() {
    if (!confirm('Xóa Token + Gist ID?')) return;
    localStorage.removeItem(GH_TOKEN_KEY);
    localStorage.removeItem(GH_GIST_KEY);
    localStorage.removeItem(GH_SHA_KEY);
    renderSidebar();
    setSyncStatus('Đã xóa cài đặt', '#f57c00');
    setTimeout(() => setSyncStatus(''), 2000);
}

async function testGHConnection() {
    const token = document.getElementById('gh-token')?.value?.trim() || '';
    const gistId = document.getElementById('gh-gist')?.value?.trim() || '';
    if (!token || !gistId) { alert('Nhập Token và Gist ID trước!'); return; }
    let report = '=== TEST KẾT NỐI ===\n\n';
    try {
        setSyncStatus('🔄 Đang test...', '#f57c00');
        const userRes = await fetch('https://api.github.com/user', {
            headers: { 'Authorization': 'token ' + token, 'Accept': 'application/vnd.github.v3+json' }
        });
        if (userRes.ok) {
            const user = await userRes.json();
            report += `✅ Token hợp lệ — User: ${user.login}\n`;
            report += `   Scopes: ${user.scopes?.join(', ') || 'không thấy'}\n`;
            if (!user.scopes?.includes('gist')) {
                report += `⚠️ THIẾU QUYỀN "gist"! Tạo token mới tại:\n   https://github.com/settings/tokens\n`;
            }
        } else {
            report += `❌ Token KHÔNG hợp lệ — HTTP ${userRes.status}\n`;
        }
        const gistRes = await fetch(`https://api.github.com/gists/${gistId}`, {
            headers: { 'Authorization': 'token ' + token, 'Accept': 'application/vnd.github.v3+json' }
        });
        if (gistRes.ok) {
            const gist = await gistRes.json();
            const files = Object.keys(gist.files || {});
            report += `✅ Gist tồn tại — Files: ${files.join(', ')}\n`;
            report += `   Owner: ${gist.owner?.login}\n`;
            report += `   Public: ${gist.public}\n`;
        } else {
            report += `❌ Gist KHÔNG tồn tại hoặc không có quyền — HTTP ${gistRes.status}\n`;
        }
    } catch (e) {
        report += `❌ Lỗi mạng: ${e.message}\n`;
    }
    alert(report);
    setSyncStatus('');
}

// ============================================================
//  CHARTS — Chart.js
// ============================================================
function renderAllCharts(md) {
    renderIncomeChart(md);
    renderExpenseChart(md);
    renderPieChart(md);
    renderTrendChart();
    renderStackChart();
    renderBalanceChart();
}

function renderIncomeChart(md) {
    const inc = { ...md.income };
    Object.entries(md.extra_income || {}).forEach(([k, v]) => { if (v > 0) inc[k] = v; });
    const entries = Object.entries(inc).filter(([, v]) => v > 0);
    if (!entries.length) return;
    const labels = entries.map(e => e[0]);
    const values = entries.map(e => e[1]);
    destroyChart('chart-income');
    _charts['chart-income'] = new Chart(document.getElementById('chart-income'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{ data: values, backgroundColor: CHART_COLORS.slice(0, labels.length), borderRadius: 4, borderSkipped: false }]
        },
        options: chartOpts('Thu nhập theo nguồn', v => fmt(v))
    });
}

function renderExpenseChart(md) {
    const personal = calcPersonal(md);
    const chartData = {};
    _data.members.forEach(mb => { if (personal[mb] > 0) chartData[`CP ${mb}`] = personal[mb]; });
    Object.entries(md.expenses || {}).forEach(([k, v]) => { if (v > 0) chartData[k] = v; });
    const entries = Object.entries(chartData).sort((a, b) => b[1] - a[1]);
    if (!entries.length) return;
    const total = entries.reduce((a, e) => a + e[1], 0);
    destroyChart('chart-expense');
    _charts['chart-expense'] = new Chart(document.getElementById('chart-expense'), {
        type: 'bar',
        data: {
            labels: entries.map(e => e[0]),
            datasets: [{
                label: 'Chi tiêu',
                data: entries.map(e => e[1]),
                backgroundColor: CHART_COLORS.slice(0, entries.length),
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            layout: { padding: { right: 60 } },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => fmt(ctx.raw) } },
                datalabels: {
                    display: true,
                    anchor: 'end',
                    align: 'right',
                    offset: 4,
                    font: { size: 10, weight: '600' },
                    color: '#444',
                    formatter: (v) => {
                        const pct = (v / total * 100).toFixed(0);
                        return `${fmtShort(v)} (${pct}%)`;
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#f0f0f0' },
                    ticks: { callback: v => fmtShort(v), font: { size: 9 } },
                    max: Math.max(...entries.map(e => e[1])) * 1.2
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 11, weight: '600' } }
                }
            }
        }
    });
}

function renderPieChart(md) {
    const personal = calcPersonal(md);
    const chartData = {};
    _data.members.forEach(mb => { if (personal[mb] > 0) chartData[`CP ${mb}`] = personal[mb]; });
    Object.entries(md.expenses || {}).forEach(([k, v]) => { if (v > 0) chartData[k] = v; });
    const entries = Object.entries(chartData).sort((a, b) => b[1] - a[1]);
    if (!entries.length) return;
    const total = entries.reduce((a, e) => a + e[1], 0);
    destroyChart('chart-pie');
    _charts['chart-pie'] = new Chart(document.getElementById('chart-pie'), {
        type: 'doughnut',
        data: {
            labels: entries.map(e => e[0]),
            datasets: [{ data: entries.map(e => e[1]), backgroundColor: CHART_COLORS.slice(0, entries.length), borderWidth: 2, borderColor: '#fff' }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'right', labels: { boxWidth: 10, font: { size: 10 } } },
                tooltip: { callbacks: { label: ctx => `${ctx.label}: ${fmt(ctx.raw)}` } },
                datalabels: {
                    display: true,
                    color: '#fff',
                    font: { size: 9, weight: '600' },
                    formatter: (v, ctx) => {
                        const pct = (v / total * 100).toFixed(0);
                        return pct > 4 ? `${pct}%` : '';
                    }
                }
            }
        }
    });
}

function renderTrendChart() {
    const sorted = Object.keys(_data.months).sort();
    const labels = sorted.map(monthShort);
    const incList = sorted.map(mk => calcMonthTotal(_data.months[mk]).inc);
    const expList = sorted.map(mk => calcMonthTotal(_data.months[mk]).total);
    const balList = sorted.map(mk => calcMonthTotal(_data.months[mk]).bal);
    destroyChart('chart-trend');
    _charts['chart-trend'] = new Chart(document.getElementById('chart-trend'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: 'Thu nhập', data: incList, backgroundColor: '#34a853', borderRadius: 3, borderSkipped: false },
                { label: 'Chi tiêu', data: expList, backgroundColor: '#ea4335', borderRadius: 3, borderSkipped: false },
                { label: 'Tiết kiệm', data: balList, backgroundColor: '#1a73e8', borderRadius: 3, borderSkipped: false }
            ]
        },
        options: chartOpts('So sánh', v => fmtShort(v))
    });
}

function renderStackChart() {
    const sorted = Object.keys(_data.months).sort();
    const labels = sorted.map(monthShort);
    const allCats = [..._data.categories];
    _data.members.forEach(mb => { const lbl = `CP ${mb}`; if (!allCats.includes(lbl)) allCats.push(lbl); });
    const catData = {};
    allCats.forEach(c => catData[c] = sorted.map(mk => {
        const m = _data.months[mk];
        if (_data.categories.includes(c)) return m.expenses[c] || 0;
        const mb = c.replace('CP ', '');
        return Math.round((m.income[mb] || 0) * PERSONAL_RATE);
    }));
    const activeCats = allCats.filter(c => catData[c].some(v => v > 0));
    destroyChart('chart-stack');
    _charts['chart-stack'] = new Chart(document.getElementById('chart-stack'), {
        type: 'bar',
        data: {
            labels,
            datasets: activeCats.map((cat, i) => ({
                label: cat,
                data: catData[cat],
                backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
                borderRadius: 2,
                borderSkipped: false
            }))
        },
        options: {
            ...chartOpts('Tích lũy', v => fmtShort(v), false),
            scales: { x: { stacked: true }, y: { stacked: true } },
            plugins: {
                ...chartOpts('', v => '', false).plugins,
                datalabels: { display: false }
            }
        }
    });
}

function renderBalanceChart() {
    const sorted = Object.keys(_data.months).sort();
    const labels = sorted.map(monthShort);
    const balList = sorted.map(mk => calcMonthTotal(_data.months[mk]).bal);
    destroyChart('chart-balance');
    _charts['chart-balance'] = new Chart(document.getElementById('chart-balance'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{ data: balList, backgroundColor: balList.map(v => v >= 0 ? '#34a853' : '#ea4335'), borderRadius: 4, borderSkipped: false }]
        },
        options: chartOpts('Dư theo tháng', v => fmtShort(v))
    });
}

function chartOpts(title, tickFmt, isBar = true) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 10, font: { size: 10 } } },
            tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + fmt(ctx.raw) } },
            title: { display: false },
            datalabels: isBar ? {
                display: true,
                anchor: 'end',
                align: 'top',
                offset: 2,
                font: { size: 9, weight: '600' },
                color: '#444',
                formatter: v => fmtShort(v)
            } : { display: false }
        },
        scales: {
            y: { ticks: { callback: v => tickFmt(v), font: { size: 9 } }, grid: { color: '#f0f0f0' } },
            x: { grid: { display: false }, ticks: { font: { size: 9 } } }
        }
    };
}

function destroyChart(id) {
    if (_charts[id]) { _charts[id].destroy(); _charts[id] = null; }
}

// ============================================================
//  TABS & SIDEBAR
// ============================================================
function switchTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${name}"]`).classList.add('active');
    document.getElementById(`tab-${name}`).classList.add('active');
}

function toggleSidebar() {
    const sb = document.getElementById('sidebar');
    const ov = document.getElementById('sidebar-overlay');
    const show = sb.style.display === 'none';
    sb.style.display = show ? 'block' : 'none';
    ov.style.display = show ? 'block' : 'none';
}

function renderSidebar() {
    const cfg = getGHConfig();
    const sorted = Object.keys(_data.months).sort().reverse();
    document.getElementById('sidebar-content').innerHTML = `
        <div class="sidebar-section">
            <div class="sync-status ${cfg.token && cfg.gistId ? 'sync-ok' : 'sync-warn'}">
                ☁️ ${cfg.token && cfg.gistId ? 'GitHub Gist đã cấu hình' : 'Chưa cấu hình Gist'}
            </div>
            <div style="display:flex;gap:8px;margin-bottom:8px">
                <button class="btn btn-primary" style="flex:1" onclick="pullFromGist()">⬇️ Tải</button>
                <button class="btn btn-green" style="flex:1" onclick="pushToGist(_data)">⬆️ Đẩy</button>
            </div>
        </div>
        <div class="divider"></div>
        <div class="sidebar-section">
            <h4>📅 Chọn tháng</h4>
            <select id="month-select" style="width:100%;padding:8px;border:1px solid var(--border);border-radius:6px;font-size:13px" onchange="selectMonth(this.value)">
                ${sorted.map(mk => `<option value="${mk}" ${mk === _selected ? 'selected' : ''}>${monthLabel(mk)}</option>`).join('')}
            </select>
        </div>
        <div class="sidebar-section">
            <h4>➕ Thêm tháng</h4>
            <div style="display:flex;gap:6px;margin-bottom:6px">
                <input type="number" id="new-y" value="${new Date().getFullYear()}" style="width:50%;padding:6px;border:1px solid var(--border);border-radius:6px;font-size:12px">
                <input type="number" id="new-m" value="${new Date().getMonth() + 1}" min="1" max="12" style="width:50%;padding:6px;border:1px solid var(--border);border-radius:6px;font-size:12px">
            </div>
            <label style="font-size:11px;display:flex;align-items:center;gap:4px;margin-bottom:6px">
                <input type="checkbox" id="copy-prev" checked> Copy tháng trước
            </label>
            <button class="btn btn-primary" style="width:100%" onclick="addMonth()">Tạo tháng</button>
        </div>
        ${sorted.length > 1 ? `<div class="sidebar-section">
            <h4>🗑️ Xóa tháng</h4>
            <button class="btn btn-red" style="width:100%" onclick="deleteMonth()">Xóa ${monthLabel(_selected)}</button>
        </div>` : ''}
        <div class="divider"></div>
        <div class="sidebar-section">
            <h4>⚙️ GitHub Sync</h4>
            <div class="form-group"><label>Token</label><input type="password" id="gh-token" value="${cfg.token}" placeholder="ghp_xxx..."></div>
            <div class="form-group"><label>Gist ID</label><input type="text" id="gh-gist" value="${cfg.gistId}" placeholder="c6c9f18338db505866b0fc1d5d1201a8"></div>
            <div style="font-size:10px;color:var(--text2);margin-bottom:8px">Gist ID hiện tại: <b>${cfg.gistId || 'chưa có'}</b></div>
            <button class="btn btn-orange" style="width:100%;margin-bottom:8px;padding:12px;font-size:14px" onclick="testGHConnection()">🧪 Test kết nối</button>
            <button class="btn btn-primary" style="width:100%;margin-bottom:6px" onclick="saveGHSettings()">💾 Lưu & Thử lại</button>
            <button class="btn btn-red" style="width:100%" onclick="resetGHSettings()">🗑️ Xóa cài đặt</button>
            <div style="font-size:10px;color:var(--text2);margin-top:4px">Tạo PAT tại <a href="https://github.com/settings/tokens" target="_blank">github.com/settings/tokens</a> với quyền <b>gist</b></div>
        </div>
    `;
}

// ============================================================
//  INIT
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
    const cfg = getGHConfig();
    if (!cfg.token || !cfg.gistId) {
        setSyncStatus('⚠️ Chưa cấu hình Gist', '#f57c00');
        renderAll();
        return;
    }
    setSyncStatus('🔄 Đang sync...', '#f57c00');
    const d = await fetchFromGist();
    if (d && d.months) {
        _data = ensureValid(d);
        localStorage.setItem(DB_KEY, JSON.stringify(_data));
        const keys = Object.keys(_data.months).sort().reverse();
        if (keys.length && !_data.months[_selected]) _selected = keys[0];
        setSyncStatus('✅ Đã sync', 'var(--green)');
    } else {
        setSyncStatus('⚠️ Dùng data local', '#f57c00');
    }
    setTimeout(() => setSyncStatus(''), 3000);
    renderAll();
    startAutoPull();
    window.addEventListener('beforeunload', () => {
        saveData(_data);
    });
});
