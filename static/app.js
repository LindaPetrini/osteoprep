// Restore language preference on topic pages
document.addEventListener('DOMContentLoaded', function() {
  const lang = localStorage.getItem('lang') || 'it';
  // Topic page will read this on load via URL param set by server
  // This script is extended in Plan 02 when topic pages are built
});
