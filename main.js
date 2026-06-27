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

document.querySelectorAll('.faq-q').forEach((question) => {
  question.addEventListener('click', () => question.parentElement.classList.toggle('open'));
});

const form = document.getElementById('leadForm');
if (form) {
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    form.reset();
    const message = document.getElementById('formMsg');
    if (message) message.classList.add('show');
  });
}
