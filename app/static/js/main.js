/* ═══════════════════════════════════════════
   RIVERS STATE ICT DEPARTMENT — MAIN JS
   ═══════════════════════════════════════════ */

// ── Nav Scroll Effect ──────────────────────
window.addEventListener('scroll', () => {
  const nav = document.getElementById('mainNav');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 50);
});

// ── Mobile Menu ────────────────────────────
function toggleMobile() {
  const menu = document.getElementById('mobileMenu');
  const btn = document.getElementById('hamburger');
  if (!menu) return;
  const open = menu.classList.toggle('open');
  btn.classList.toggle('open', open);
  document.body.style.overflow = open ? 'hidden' : '';
}

// ── Search Overlay ─────────────────────────
function toggleSearch() {
  const overlay = document.getElementById('searchOverlay');
  const input = document.getElementById('searchInput');
  if (!overlay) return;
  const open = overlay.classList.toggle('open');
  if (open && input) setTimeout(() => input.focus(), 100);
  else if (input) { input.value = ''; clearSearchResults(); }
}

async function doSearch(query) {
  const container = document.getElementById('searchResults');
  if (!container) return;
  if (!query.trim()) { clearSearchResults(); return; }
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (!data.results.length) {
      container.innerHTML = '<div class="search-result-item">No results found for "<strong>' + query + '</strong>"</div>';
      return;
    }
    container.innerHTML = data.results.map(r =>
      `<a href="${r.url}" class="search-result-item">
        <span>${r.title}</span>
        <span class="tag">${r.type}</span>
      </a>`
    ).join('');
  } catch {}
}

function clearSearchResults() {
  const c = document.getElementById('searchResults');
  if (c) c.innerHTML = '';
}

// Close search on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    const overlay = document.getElementById('searchOverlay');
    if (overlay && overlay.classList.contains('open')) toggleSearch();
  }
});

// ── Toast Notification ─────────────────────
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast ${type === 'error' ? 'error' : ''} show`;
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// ── Newsletter Submit ──────────────────────
async function submitNewsletter(event) {
  event.preventDefault();
  const form = event.target;
  const email = form.querySelector('[name="email"]').value;
  if (!email) return;
  try {
    const res = await fetch('/api/newsletter', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    showToast(data.success ? '✓ ' + data.message : data.message, data.success ? 'success' : 'error');
    if (data.success) form.reset();
  } catch { showToast('Something went wrong. Please try again.', 'error'); }
}

// ── Contact Form Submit ────────────────────
async function submitContact(event) {
  event.preventDefault();
  const form = event.target;
  const btn = form.querySelector('[type="submit"]');
  const successEl = document.getElementById('contactSuccess');
  const data = Object.fromEntries(new FormData(form));
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
  try {
    const res = await fetch('/api/contact', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    const result = await res.json();
    if (result.success) {
      if (successEl) successEl.style.display = 'flex';
      form.reset();
      btn.innerHTML = '<i class="fas fa-check"></i> Message Sent!';
      btn.style.background = 'var(--green)';
    } else throw new Error();
  } catch {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Message';
    showToast('Failed to send message. Please try again.', 'error');
  }
}

// ── Registration Multi-Step ────────────────
let regStep = 1;
const regData = {};

function nextRegStep() {
  const step = document.getElementById(`reg-step-${regStep}`);
  if (!validateStep(regStep)) return;
  collectStepData(regStep);
  step.classList.remove('active');
  regStep++;
  const next = document.getElementById(`reg-step-${regStep}`);
  if (next) {
    next.classList.add('active');
    updateStepIndicator();
    if (regStep === 3) buildSummary();
  }
}

function prevRegStep() {
  const step = document.getElementById(`reg-step-${regStep}`);
  step.classList.remove('active');
  regStep--;
  const prev = document.getElementById(`reg-step-${regStep}`);
  if (prev) { prev.classList.add('active'); updateStepIndicator(); }
}

function validateStep(step) {
  const container = document.getElementById(`reg-step-${step}`);
  const required = container.querySelectorAll('[required]');
  let valid = true;
  required.forEach(el => {
    if (!el.value.trim()) {
      el.style.borderColor = '#ef4444';
      el.addEventListener('input', () => el.style.borderColor = '', { once: true });
      valid = false;
    }
  });
  if (!valid) showToast('Please fill in all required fields.', 'error');
  return valid;
}

function collectStepData(step) {
  const container = document.getElementById(`reg-step-${step}`);
  container.querySelectorAll('[name]').forEach(el => { regData[el.name] = el.value; });
}

function updateStepIndicator() {
  document.querySelectorAll('.step-dot').forEach((dot, i) => {
    dot.classList.remove('active', 'done');
    if (i + 1 < regStep) dot.classList.add('done');
    else if (i + 1 === regStep) dot.classList.add('active');
  });
}

function buildSummary() {
  collectStepData(2);
  const el = document.getElementById('regSummary');
  if (!el) return;
  el.innerHTML = `
    <div class="summary-row"><span>Full Name</span><strong>${regData.first_name || ''} ${regData.last_name || ''}</strong></div>
    <div class="summary-row"><span>Email</span><strong>${regData.email || ''}</strong></div>
    <div class="summary-row"><span>Phone</span><strong>${regData.phone || ''}</strong></div>
    <div class="summary-row"><span>LGA</span><strong>${regData.lga || ''}</strong></div>
    <div class="summary-row"><span>Program</span><strong>${regData.program || ''}</strong></div>
    <div class="summary-row"><span>Schedule</span><strong>${regData.schedule || ''}</strong></div>
    <div class="summary-row"><span>Occupation</span><strong>${regData.occupation || ''}</strong></div>
  `;
}

async function submitRegistration(event) {
  event.preventDefault();
  const agreeEl = document.getElementById('regAgree');
  if (!agreeEl || !agreeEl.checked) { showToast('Please agree to the terms to continue.', 'error'); return; }
  const btn = event.target.querySelector('[type="submit"]');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
  collectStepData(3);
  try {
    const res = await fetch('/api/register', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(regData)
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('reg-step-3').classList.remove('active');
      const success = document.getElementById('regSuccess');
      if (success) {
        document.getElementById('refNum').textContent = data.reference;
        success.style.display = 'block';
      }
      document.querySelectorAll('.step-dot').forEach(d => d.classList.add('done'));
    } else throw new Error(data.message);
  } catch (err) {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Application';
    showToast(err.message || 'Submission failed. Try again.', 'error');
  }
}

// ── Scroll Reveal ──────────────────────────
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
});

// ── Counter Animation ──────────────────────
function animateCounter(el) {
  const target = parseFloat(el.dataset.target);
  const isInt = Number.isInteger(target);
  const duration = 1800;
  const start = performance.now();
  const update = (now) => {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    const value = target * ease;
    el.textContent = isInt ? Math.floor(value).toLocaleString() : value.toFixed(1);
    if (t < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-target]').forEach(el => counterObserver.observe(el));
});
