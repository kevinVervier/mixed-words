const CIRC = 282.74; // 2π × r=45

const state = {
  langue: 'fr',
  temps: 60,
  lettre: null,
  theme: null,
  answers: [],
  timer: null,
  timeLeft: 0,
};

const T = {
  fr: {
    subtitle: "Nommez le plus d'éléments possible sur un thème, à partir d'une lettre tirée au sort !",
    duration: 'Durée', language: 'Langue',
    play: 'Jouer !', done: 'Terminé', again: 'Rejouer',
    placeholder: 'Votre réponse…',
    drawing: 'Tirage en cours…',
    validating: 'Validation par Claude…',
    results: 'Résultats',
  },
  en: {
    subtitle: 'Name as many items as possible on a theme, starting from a random drawn letter!',
    duration: 'Duration', language: 'Language',
    play: 'Play!', done: 'Done', again: 'Play again',
    placeholder: 'Your answer…',
    drawing: 'Drawing…',
    validating: 'Validating with Claude…',
    results: 'Results',
  },
};

function t(key) { return T[state.langue][key] || T.fr[key]; }

// ── Screen helpers ────────────────────────────────────────
function show(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function loading(msg) {
  document.getElementById('loading-text').textContent = msg;
  show('screen-loading');
}

// ── Language / settings ───────────────────────────────────
function applyLanguage() {
  document.getElementById('subtitle').textContent = t('subtitle');
  document.getElementById('lbl-langue').textContent = t('language');
  document.getElementById('lbl-temps').textContent = t('duration');
  document.getElementById('btn-play').textContent = t('play');
  document.getElementById('btn-done').textContent = t('done');
  document.getElementById('btn-again').textContent = t('again');
  document.getElementById('word-input').placeholder = t('placeholder');
  document.documentElement.lang = state.langue;
}

function initToggles() {
  document.getElementById('langue-toggle').addEventListener('click', e => {
    const btn = e.target.closest('.toggle-btn');
    if (!btn) return;
    document.querySelectorAll('#langue-toggle .toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.langue = btn.dataset.value;
    applyLanguage();
  });

  document.getElementById('temps-toggle').addEventListener('click', e => {
    const btn = e.target.closest('.toggle-btn');
    if (!btn) return;
    document.querySelectorAll('#temps-toggle .toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.temps = +btn.dataset.value;
  });
}

// ── Timer ─────────────────────────────────────────────────
function startTimer(seconds) {
  state.timeLeft = seconds;
  renderTimer(seconds, seconds);
  clearInterval(state.timer);
  state.timer = setInterval(() => {
    state.timeLeft--;
    renderTimer(state.timeLeft, seconds);
    if (state.timeLeft <= 0) {
      clearInterval(state.timer);
      finishGame();
    }
  }, 1000);
}

function renderTimer(left, total) {
  document.getElementById('timer-text').textContent = left;
  const offset = CIRC * (1 - left / total);
  const arc = document.getElementById('timer-arc');
  arc.style.strokeDashoffset = offset;
  // White → yellow → red as time runs out
  const pct = left / total;
  arc.style.stroke = pct > .5 ? '#fff'
    : pct > .25 ? '#FFD93D'
    : '#FF6B6B';
}

// ── Game flow ─────────────────────────────────────────────
async function startGame() {
  loading(t('drawing'));
  try {
    const res = await fetch(`/api/draw?langue=${state.langue}`);
    if (!res.ok) throw new Error(await res.text());
    const { lettre, theme } = await res.json();

    state.lettre = lettre;
    state.theme = theme;
    state.answers = [];

    document.getElementById('letter-display').textContent = lettre;
    document.getElementById('theme-display').textContent = theme;
    document.getElementById('answers-list').innerHTML = '';
    document.getElementById('word-input').value = '';

    const timerArea = document.getElementById('timer-area');
    if (state.temps > 0) {
      timerArea.classList.remove('hidden');
      show('screen-playing');
      startTimer(state.temps);
    } else {
      timerArea.classList.add('hidden');
      show('screen-playing');
    }

    setTimeout(() => document.getElementById('word-input').focus(), 150);
  } catch (err) {
    alert('Erreur : ' + err.message);
    show('screen-idle');
  }
}

function addAnswer() {
  const input = document.getElementById('word-input');
  const word = input.value.trim().toUpperCase().replace(/[^A-Z]/g, '');
  if (!word || state.answers.includes(word)) { input.value = ''; return; }

  state.answers.push(word);
  const li = document.createElement('li');
  li.textContent = word;
  const list = document.getElementById('answers-list');
  list.appendChild(li);
  list.scrollTop = list.scrollHeight;
  input.value = '';
  input.focus();
}

async function finishGame() {
  clearInterval(state.timer);
  loading(t('validating'));
  try {
    const res = await fetch('/api/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        theme: state.theme,
        lettre: state.lettre,
        answers: state.answers,
        langue: state.langue,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    const { result } = await res.json();
    showResults(result);
  } catch (err) {
    alert('Erreur validation : ' + err.message);
    show('screen-idle');
  }
}

function showResults(text) {
  const header = `${t('results')} — ${state.theme.toUpperCase()} / ${state.lettre}`;
  document.getElementById('results-header').textContent = header;

  const lines = text.split('\n');
  const scoreIdx = lines.findLastIndex(l => /score\s*:/i.test(l));
  const bodyLines = scoreIdx >= 0 ? lines.slice(0, scoreIdx) : lines;
  const scoreLine = scoreIdx >= 0
    ? lines[scoreIdx].replace(/\*\*(.*?)\*\*/g, '$1').trim()
    : '';

  const html = bodyLines.map(line => {
    if (!line.trim()) return '';
    const escaped = line
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    const cls = /✅|VALIDE\b|VALID\b/.test(line) ? ' valid'
      : /❌|INVALIDE\b|INVALID\b/.test(line) ? ' invalid' : '';
    return `<div class="result-line${cls}">${escaped}</div>`;
  }).join('');

  const scoreHtml = scoreLine
    ? `<div class="score-line">${scoreLine}</div>` : '';

  document.getElementById('results-body').innerHTML = html + scoreHtml;
  show('screen-results');
}

// ── Bootstrap ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  applyLanguage();
  initToggles();

  document.getElementById('btn-play').addEventListener('click', startGame);
  document.getElementById('btn-again').addEventListener('click', () => show('screen-idle'));
  document.getElementById('btn-add').addEventListener('click', addAnswer);
  document.getElementById('btn-done').addEventListener('click', finishGame);
  document.getElementById('word-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); addAnswer(); }
  });
});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}
