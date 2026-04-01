/**
 * AU Voting System — Shared Frontend Library
 * Include once per page: <script src="/assets/js/app.js"></script>
 */

'use strict';

const API_BASE = 'https://voting-system2-production.up.railway.app/api';

// ── API Client ────────────────────────────────────────────────────────────────
const API = {
    async _call(endpoint, options = {}) {
        const token = localStorage.getItem('au_token');
        const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
        if (token) headers['Authorization'] = `Token ${token}`;

        const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            const msg = data.error || data.detail
                || Object.values(data).flat().join(' | ')
                || 'Request failed';
            throw { status: res.status, message: msg, data };
        }
        return data;
    },
    get:    (url)         => API._call(url),
    post:   (url, body)   => API._call(url, { method: 'POST',   body: JSON.stringify(body) }),
    patch:  (url, body)   => API._call(url, { method: 'PATCH',  body: JSON.stringify(body) }),
    delete: (url)         => API._call(url, { method: 'DELETE' }),
};

// ── Auth ──────────────────────────────────────────────────────────────────────
const Auth = {
    getSession() {
        try { return JSON.parse(localStorage.getItem('au_session')); } catch { return null; }
    },
    setSession(user, token) {
        localStorage.setItem('au_session', JSON.stringify(user));
        localStorage.setItem('au_token', token);
    },
    clear() {
        localStorage.removeItem('au_session');
        localStorage.removeItem('au_token');
    },
    requireStudent() {
        const s = this.getSession();
        if (!s || s.role !== 'student') { window.location.href = '/student/login.html'; return null; }
        return s;
    },
    requireAdmin() {
        const s = this.getSession();
        if (!s || !['uni_admin', 'faculty_admin'].includes(s.role)) {
            window.location.href = '/admin/login.html'; return null;
        }
        return s;
    },
    async logout() {
        try { await API.post('/auth/logout/'); } catch {}
        this.clear();
        const isAdmin = window.location.pathname.includes('/admin/');
        window.location.href = isAdmin ? '/admin/login.html' : '/student/login.html';
    },
};

// ── Toast ─────────────────────────────────────────────────────────────────────
const Toast = {
    container: null,
    init() {
        if (this.container) return;
        this.container = document.createElement('div');
        this.container.id = 'toast-root';
        this.container.style.cssText =
            'position:fixed;top:1.25rem;right:1.25rem;z-index:9999;display:flex;flex-direction:column;gap:.5rem;pointer-events:none;';
        document.body.appendChild(this.container);
    },
    show(message, type = 'info', duration = 3500) {
        this.init();
        const map = {
            success: { bg: '#16a34a', icon: 'check_circle' },
            error:   { bg: '#dc2626', icon: 'error' },
            warning: { bg: '#d97706', icon: 'warning' },
            info:    { bg: '#003DA5', icon: 'info' },
        };
        const { bg, icon } = map[type] || map.info;
        const el = document.createElement('div');
        el.style.cssText = `background:${bg};color:#fff;padding:.75rem 1.25rem;border-radius:.75rem;
            display:flex;align-items:center;gap:.625rem;font-size:.875rem;font-weight:500;
            box-shadow:0 10px 40px rgba(0,0,0,.2);pointer-events:auto;max-width:26rem;
            animation:toastIn .25s ease;`;
        el.innerHTML = `<span class="material-symbols-outlined" style="font-size:1.125rem">${icon}</span>${message}`;
        this.container.appendChild(el);
        setTimeout(() => { el.style.animation = 'toastOut .25s ease forwards'; setTimeout(() => el.remove(), 250); }, duration);
    },
};

// ── Dark Mode ─────────────────────────────────────────────────────────────────
const DarkMode = {
    init() {
        const saved = localStorage.getItem('au_dark');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (saved === 'true' || (!saved && prefersDark)) {
            document.documentElement.classList.add('dark');
        }
    },
    toggle() {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('au_dark', isDark);
    },
};

// ── Navigation ────────────────────────────────────────────────────────────────
const Nav = {
    _build(pages, currentId) {
        const wrap = document.createElement('nav');
        wrap.id = 'sidebar-nav';
        wrap.className = 'sidebar-nav';
        wrap.innerHTML = pages.map(p => `
            <a href="${p.href}" class="nav-item${p.id === currentId ? ' nav-item--active' : ''}">
                <span class="material-symbols-outlined">${p.icon}</span>
                <span>${p.label}</span>
            </a>`).join('');
        return wrap;
    },
    student(currentId) {
        return this._build([
            { href: '/student/dashboard.html', icon: 'space_dashboard', label: 'Dashboard', id: 'dashboard' },
            { href: '/student/elections.html', icon: 'how_to_vote', label: 'Elections', id: 'elections' },
            { href: '/student/results.html', icon: 'bar_chart', label: 'Results', id: 'results' },
            { href: '/student/profile.html', icon: 'account_circle', label: 'My Profile', id: 'profile' },
        ], currentId);
    },
    admin(currentId) {
        return this._build([
            { href: '/admin/dashboard.html', icon: 'dashboard', label: 'Dashboard', id: 'dashboard' },
            { href: '/admin/elections.html', icon: 'how_to_vote', label: 'Elections', id: 'elections' },
            { href: '/admin/voters.html', icon: 'group', label: 'Voters', id: 'voters' },
            { href: '/admin/results.html', icon: 'bar_chart', label: 'Results', id: 'results' },
            { href: '/admin/announcements.html', icon: 'campaign', label: 'Announcements', id: 'announcements' },
        ], currentId);
    },
};

// ── Utilities ─────────────────────────────────────────────────────────────────
function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-NG', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

function formatDateShort(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-NG', { day: '2-digit', month: 'short', year: 'numeric' });
}

function elapsedLabel(isoEnd) {
    const diff = new Date(isoEnd) - Date.now();
    if (diff <= 0) return 'Ended';
    const hrs = Math.floor(diff / 3_600_000);
    if (hrs < 24) return `${hrs}h remaining`;
    return `${Math.floor(hrs / 24)}d remaining`;
}

function statusBadge(status) {
    const map = {
        draft:     ['badge--draft',     'Draft'],
        active:    ['badge--active',    'Live'],
        completed: ['badge--completed', 'Completed'],
        cancelled: ['badge--cancelled', 'Cancelled'],
    };
    const [cls, label] = map[status] || ['badge--draft', status];
    return `<span class="badge ${cls}">${label}</span>`;
}

// ── Global CSS animations (injected once) ─────────────────────────────────────
(function injectKeyframes() {
    const style = document.createElement('style');
    style.textContent = `
    @keyframes toastIn  { from { opacity:0; transform:translateX(2rem); } to { opacity:1; transform:translateX(0); } }
    @keyframes toastOut { from { opacity:1; transform:translateX(0); } to { opacity:0; transform:translateX(2rem); } }
    @keyframes fadeUp   { from { opacity:0; transform:translateY(1rem); } to { opacity:1; transform:translateY(0); } }
    @keyframes shimmer  { 0%,100%{opacity:.4} 50%{opacity:1} }
    .skeleton { animation: shimmer 1.5s ease infinite; background: var(--border); border-radius: .5rem; }
    `;
    document.head.appendChild(style);
})();

// Auto-init dark mode
DarkMode.init();

// ── Mobile Menu ───────────────────────────────────────────────────────────────
const MobileMenu = {
    init() {
        const header = document.querySelector('.app-header');
        const sidebar = document.querySelector('.app-sidebar');
        if (!header || !sidebar) return;
        
        // Add menu button to header
        if (!document.getElementById('mobile-menu-btn')) {
            const btn = document.createElement('button');
            btn.id = 'mobile-menu-btn';
            btn.className = 'icon-btn header-menu-btn';
            btn.innerHTML = '<span class="material-symbols-outlined">menu</span>';
            btn.title = "Toggle sidebar menu";
            btn.onclick = () => this.toggle();
            
            const brand = header.querySelector('.brand');
            if (brand) header.insertBefore(btn, brand);
        }
        
        // Add overlay to body
        if (!document.getElementById('sidebar-overlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'sidebar-overlay';
            overlay.className = 'sidebar-overlay';
            overlay.onclick = () => this.close();
            document.body.appendChild(overlay);
        }
    },
    toggle() {
        const sidebar = document.querySelector('.app-sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const icon = document.querySelector('#mobile-menu-btn span');
        if (!sidebar || !overlay) return;
        
        const isOpen = sidebar.classList.toggle('sidebar-open');
        overlay.classList.toggle('open');
        if (icon) icon.textContent = isOpen ? 'menu_open' : 'menu';
    },
    close() {
        const sidebar = document.querySelector('.app-sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const icon = document.querySelector('#mobile-menu-btn span');
        if (sidebar) sidebar.classList.remove('sidebar-open');
        if (overlay) overlay.classList.remove('open');
        if (icon) icon.textContent = 'menu';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    MobileMenu.init();
});
