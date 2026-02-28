document.addEventListener('DOMContentLoaded', function() {
  // On topic pages: honor localStorage language preference
  // The server renders with ?lang=it by default; redirect if user prefers EN
  const savedLang = localStorage.getItem('lang');
  if (savedLang && window.location.pathname.startsWith('/topic/')) {
    const url = new URL(window.location.href);
    const currentLang = url.searchParams.get('lang') || 'it';
    if (savedLang !== currentLang) {
      // Trigger HTMX swap instead of full reload to use cached content
      const slug = window.location.pathname.split('/topic/')[1];
      if (slug && typeof htmx !== 'undefined') {
        htmx.ajax('GET', `/topic/${slug}/content?lang=${savedLang}`, {
          target: '#explainer-content',
          swap: 'innerHTML'
        });
        // Update toggle button states
        document.querySelectorAll('.join-item').forEach(btn => {
          const isActive = btn.textContent.trim().toLowerCase() === savedLang;
          btn.classList.toggle('btn-primary', isActive);
          btn.classList.toggle('btn-ghost', !isActive);
        });
      }
    }
  }
});
