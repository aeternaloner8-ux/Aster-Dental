const hdr = document.getElementById('hdr');
addEventListener('scroll', () => {
  if (hdr) hdr.classList.toggle('scrolled', scrollY > 24);
}, { passive: true });

const io = new IntersectionObserver((entries) => {
  entries.forEach((entry, index) => {
    if (!entry.isIntersecting) return;
    entry.target.style.transitionDelay = `${Math.min(index, 4) * 55}ms`;
    entry.target.classList.add('in');
    io.unobserve(entry.target);
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

const menuBtn = document.getElementById('menuBtn');
const mnav = document.getElementById('mnav');
const mnavClose = document.getElementById('mnavClose');
function closeMenu() {
  if (mnav) mnav.classList.remove('open');
  document.body.style.overflow = '';
}
if (menuBtn && mnav) {
  menuBtn.addEventListener('click', () => {
    mnav.classList.add('open');
    document.body.style.overflow = 'hidden';
  });
}
if (mnavClose) mnavClose.addEventListener('click', closeMenu);
if (mnav) mnav.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));

document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener('click', (event) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

document.querySelectorAll('.faq-q').forEach((question) => {
  question.addEventListener('click', () => question.parentElement.classList.toggle('open'));
});

const videoTriggers = document.querySelectorAll('.video-trigger');
if (videoTriggers.length) {
  const modal = document.createElement('div');
  modal.className = 'video-modal';
  modal.innerHTML = `
    <div class="video-modal__panel" role="dialog" aria-modal="true" aria-label="Видео Aster Dental">
      <button class="video-modal__close" type="button" aria-label="Закрыть"></button>
      <span>Видео Aster Dental</span>
      <h3></h3>
      <p>Полную историю и похожие клинические случаи покажем на консультации, чтобы подобрать аккуратный план под ваш запрос.</p>
      <a class="ref-btn" href="contacts.html#appointment">Записаться на консультацию ↗</a>
    </div>
  `;
  document.body.appendChild(modal);
  const title = modal.querySelector('h3');
  const close = () => modal.classList.remove('open');
  modal.querySelector('.video-modal__close').addEventListener('click', close);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) close();
  });
  videoTriggers.forEach((button) => {
    button.addEventListener('click', () => {
      title.textContent = button.dataset.videoTitle || 'История пациента';
      modal.classList.add('open');
    });
  });
}

const form = document.getElementById('leadForm');
if (form) {
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    form.reset();
    const message = document.getElementById('formMsg');
    if (message) message.classList.add('show');
  });
}
