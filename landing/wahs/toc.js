// Marks the contents link for the section currently in view.
// The page reads fine without this script; it only adds the highlight.
const toc = document.querySelector('.doc-toc');

if (toc) {
  const links = [...toc.querySelectorAll('a[href^="#"]')];
  const linkById = new Map(links.map((link) => [link.getAttribute('href').slice(1), link]));

  // Where the browser tracks the visible section itself (:target-current in
  // CSS) it draws the highlight, and this script only mirrors the state to
  // aria-current for assistive technology. Elsewhere it draws the highlight too.
  const nativeHighlight = CSS.supports('scroll-target-group: auto');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const current = linkById.get(entry.target.id);
      links.forEach((link) => {
        if (!nativeHighlight) link.classList.toggle('target-current', link === current);
        if (link === current) link.setAttribute('aria-current', 'true');
        else link.removeAttribute('aria-current');
      });
    });
  }, { rootMargin: '-50% 0px -50% 0px', threshold: 0 });

  document.querySelectorAll('.doc-body section[id]').forEach((section) => {
    if (linkById.has(section.id)) observer.observe(section);
  });
}
