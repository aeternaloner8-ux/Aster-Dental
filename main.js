const header = document.querySelector("#header");
const menuButton = document.querySelector("#menuButton");
const mobileNav = document.querySelector("#mobileNav");

const syncHeader = () => {
  header?.classList.toggle("scrolled", window.scrollY > 20);
};

syncHeader();
window.addEventListener("scroll", syncHeader, { passive: true });

menuButton?.addEventListener("click", () => {
  const isOpen = mobileNav.classList.toggle("open");
  menuButton.setAttribute("aria-expanded", String(isOpen));
});

mobileNav?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    mobileNav.classList.remove("open");
    menuButton?.setAttribute("aria-expanded", "false");
  });
});

const revealItems = document.querySelectorAll(".reveal");

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("visible"));
}

document.querySelector("#contactForm")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const note = document.querySelector("#formNote");
  if (note) {
    note.textContent = "Заявка подготовлена. Подключите реальный обработчик формы перед публикацией.";
  }
  event.currentTarget.reset();
});
