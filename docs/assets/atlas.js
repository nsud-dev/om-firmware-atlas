/* OM Firmware Atlas — small progressive enhancements for overrides/main.html. The site works without it. */
(function () {
  var root = document.documentElement;

  /* Theme toggle (initial theme is set inline in <head> before paint). */
  document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
    button.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('atlas-theme', next); } catch (e) {}
    });
  });

  /* Mobile menu. */
  var menuButton = document.querySelector('[data-menu-toggle]');
  var nav = document.getElementById('primary-nav');
  if (menuButton && nav) {
    menuButton.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      menuButton.setAttribute('aria-expanded', String(open));
    });
  }

  /* Wide tables scroll inside a rounded frame instead of stretching the page. */
  document.querySelectorAll('.prose table').forEach(function (table) {
    if (table.parentElement.classList.contains('table-wrap')) return;
    var wrap = document.createElement('div');
    wrap.className = 'table-wrap';
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
  });

  /* Copy buttons on code blocks, for commands and agent prompts. */
  if (navigator.clipboard) {
    document.querySelectorAll('.prose pre').forEach(function (pre) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-btn';
      button.textContent = 'Copy';
      button.addEventListener('click', function () {
        navigator.clipboard.writeText(pre.querySelector('code') ? pre.querySelector('code').innerText : pre.innerText).then(function () {
          button.textContent = 'Copied';
          setTimeout(function () { button.textContent = 'Copy'; }, 1600);
        });
      });
      pre.appendChild(button);
    });
  }

  /* Search dialog: "/" or Ctrl/Cmd+K opens it; the MkDocs search plugin fills the results. */
  var dialog = document.getElementById('search-dialog');
  var input = document.getElementById('mkdocs-search-query');
  function openSearch() {
    if (!dialog || dialog.open) return;
    if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
    if (input) { input.focus(); input.select(); }
  }
  document.querySelectorAll('[data-search-open]').forEach(function (b) { b.addEventListener('click', openSearch); });
  document.addEventListener('keydown', function (event) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName) || event.target.isContentEditable;
    if ((event.key === '/' && !typing) || (event.key.toLowerCase() === 'k' && (event.metaKey || event.ctrlKey))) {
      event.preventDefault();
      openSearch();
    }
  });
  if (dialog) {
    dialog.addEventListener('click', function (event) { if (event.target === dialog) dialog.close(); });
    /* Enter opens the first result rather than closing the dialog. */
    dialog.querySelector('form').addEventListener('submit', function (event) {
      if (event.submitter && event.submitter.classList.contains('search-close')) return;
      event.preventDefault();
      var first = dialog.querySelector('.search-results a');
      if (first) location.href = first.href;
    });
    if (/[?&]q=/.test(location.search)) openSearch();
  }

  /* Highlight the current section in the "On this page" list. */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.doc-toc a'));
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[decodeURIComponent(a.hash.slice(1))] = a; });
    var headings = Object.keys(byId).map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var visible = new Set();
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) visible.add(e.target); else visible.delete(e.target); });
      var current = headings.filter(function (h) { return visible.has(h); })[0];
      if (!current) {
        current = headings.filter(function (h) { return h.getBoundingClientRect().top < 120; }).pop();
      }
      tocLinks.forEach(function (a) { a.classList.remove('is-current'); });
      if (current && byId[current.id]) byId[current.id].classList.add('is-current');
    }, { rootMargin: '-72px 0px -60% 0px' });
    headings.forEach(function (h) { observer.observe(h); });
  }
})();
