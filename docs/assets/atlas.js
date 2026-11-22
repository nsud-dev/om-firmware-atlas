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
    function setMenu(open) {
      nav.classList.toggle('is-open', open);
      menuButton.setAttribute('aria-expanded', String(open));
      menuButton.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    }
    menuButton.addEventListener('click', function (event) {
      var opening = !nav.classList.contains('is-open');
      setMenu(opening);
      if (opening && event.detail === 0) nav.querySelector('a').focus();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) {
        setMenu(false);
        menuButton.focus();
      }
    });
    function dismissMenu(event) {
      if (!nav.contains(event.target) && !menuButton.contains(event.target)) setMenu(false);
    }
    document.addEventListener('pointerdown', dismissMenu);
    document.addEventListener('focusin', dismissMenu);
  }

  /* Punctuation and generation spellings vary. Convert whole generations before
     matching so a search for Mark II cannot return a Mark III through a prefix. */
  function cameraKey(name) {
    var numerals = { i: '1', ii: '2', iii: '3', iv: '4' };
    return name.toLowerCase().replace(/mark|mk/g, '').replace(/[^a-z0-9]/g, '')
      .replace(/(iv|iii|ii|i)$/, function (value) { return numerals[value]; });
  }

  document.querySelectorAll('.camera-finder').forEach(function (finder) {
    var field = finder.querySelector('input');
    var status = finder.querySelector('[role="status"]');
    var links = Array.from(finder.querySelectorAll('[data-names]'));
    function filter() {
      var query = cameraKey(field.value);
      var count = 0;
      links.forEach(function (link) {
        var matches = query && link.dataset.names.split('|').some(function (name) {
          return cameraKey(name).includes(query);
        });
        link.parentElement.hidden = !matches;
        if (matches) count++;
      });
      status.textContent = !query ? '' : count ? count + (count === 1 ? ' camera listed' : ' cameras listed')
        : 'No matching camera in the Atlas. Check the name and generation, or browse the camera directory.';
    }
    field.addEventListener('input', filter);
    field.addEventListener('keydown', function (event) {
      if (event.isComposing) return;
      var matches = links.filter(function (link) { return !link.parentElement.hidden; });
      if (event.key === 'Enter' && matches.length === 1) {
        event.preventDefault();
        matches[0].click();
      } else if (event.key === 'ArrowDown' && matches.length) {
        event.preventDefault();
        matches[0].focus();
      }
    });
    filter();
    finder.hidden = false;
  });

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
    var models = dialog.querySelector('.search-models');
    var modelCards = Array.from(models.querySelectorAll('article'));
    var searchResults = dialog.querySelector('.search-results');
    var resultKinds = {
      cameras: 'Camera', research: 'Camera research', projects: 'Project or tool',
      firmware: 'Firmware', reference: 'Reference', evidence: 'Test evidence',
      capabilities: 'Feature claim', sources: 'Source', community: 'Community'
    };

    function showModelMatches() {
      var query = cameraKey(input.value);
      modelCards.forEach(function (card) {
        card.hidden = !query || !card.dataset.model.split('|').some(function (name) {
          return cameraKey(name) === query;
        });
      });
      models.hidden = modelCards.every(function (card) { return card.hidden; });
    }

    // The search plugin emits page and section results separately. Keep useful sections and suppress duplicate titles.
    new MutationObserver(function () {
      var seen = new Set();
      searchResults.querySelectorAll('article').forEach(function (article) {
        var link = article.querySelector('h3 a');
        var path = new URL(link.href).pathname;
        var match = path.match(/\/views\/([^/]+)/);
        var kind = match ? resultKinds[match[1]] : /\/knowledge\//.test(path) ? 'Guide' : '';
        var key = path + '\n' + link.textContent.trim().toLowerCase();
        article.hidden = (match && match[1] === 'showcases') || seen.has(key);
        seen.add(key);
        if (kind && !article.querySelector('.search-kind')) {
          var label = document.createElement('span');
          label.className = 'search-kind';
          label.textContent = kind;
          article.prepend(label);
        }
      });
    }).observe(searchResults, { childList: true });

    input.addEventListener('input', showModelMatches);
    dialog.addEventListener('click', function (event) { if (event.target === dialog) dialog.close(); });
    dialog.querySelector('.search-close').addEventListener('click', function () { dialog.close(); });
    dialog.querySelector('form').addEventListener('submit', function (event) {
      event.preventDefault();
      var matches = models.querySelectorAll('article:not([hidden])');
      if (matches.length > 1) {
        matches[0].querySelector('a').focus();
        return;
      }
      var first = matches.length === 1 ? matches[0].querySelector('a') : searchResults.querySelector('article:not([hidden]) a');
      if (input.value.trim() && first) location.href = first.href;
    });
    var initialQuery = new URLSearchParams(location.search).get('q');
    if (initialQuery !== null) {
      input.value = initialQuery;
      showModelMatches();
      openSearch();
    }
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
