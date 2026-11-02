// Split the report flow into A4 pages of 595 x 842 px (1 px = 1 pt): every section starts a new page,
// blocks never cross a page edge (code blocks and lists are split), headings stay with what follows.
// Then add page numbers (from page 2 on) and fill in the contents page. Returns JSON.
(function () {
  var P = 842, TOP = 64, BOTTOM = 72, H = P - TOP - BOTTOM;

  function box(el) {
    var r = el.getBoundingClientRect();
    return { top: r.top + window.pageYOffset, bottom: r.bottom + window.pageYOffset };
  }
  function pageOf(y) { return Math.floor(y / P); }
  function limitOf(page) { return page * P + TOP + H; }
  function atPageTop(y) { return Math.abs(y - (pageOf(y) * P + TOP)) < 1; }

  function pushToNextPage(el) {
    el.style.marginTop = '0';
    var top = box(el).top;
    var target = (pageOf(top) + 1) * P + TOP;
    if (top < pageOf(top) * P + TOP) target = pageOf(top) * P + TOP; // sits in the top margin: align to this page
    var s = document.createElement('div');
    s.className = 'spacer';
    s.style.height = (target - top) + 'px';
    el.parentNode.insertBefore(s, el);
    var off = box(el).top - target; // correct any rounding from margin collapsing
    if (Math.abs(off) > 0.5) s.style.height = (target - top - off) + 'px';
  }

  function splitPre(el, limit) {
    var lines = el.innerHTML.split('\n');
    var lh = parseFloat(getComputedStyle(el).lineHeight);
    var fit = Math.min(lines.length - 1, Math.floor((limit - box(el).top) / lh));
    while (fit >= 3) {
      el.innerHTML = lines.slice(0, fit).join('\n');
      if (box(el).bottom <= limit) {
        var rest = el.cloneNode(false);
        rest.innerHTML = lines.slice(fit).join('\n');
        el.parentNode.insertBefore(rest, el.nextSibling);
        return true;
      }
      fit--;
    }
    el.innerHTML = lines.join('\n');
    return false;
  }

  function splitList(el, limit) {
    var items = Array.prototype.slice.call(el.children), k = 0;
    while (k < items.length && box(items[k]).bottom <= limit) k++;
    if (k === 0 || k >= items.length) return false;
    var rest = el.cloneNode(false);
    if (el.tagName === 'OL') rest.setAttribute('start', String(k + 1));
    for (var j = k; j < items.length; j++) rest.appendChild(items[j]);
    el.parentNode.insertBefore(rest, el.nextSibling);
    return true;
  }

  // split a paragraph at the start of the first line that does not fit (at least 2 lines on each side)
  function splitPara(el, limit) {
    var lh = parseFloat(getComputedStyle(el).lineHeight), b = box(el);
    var fit = Math.floor((limit - b.top) / lh + 0.01), total = Math.round((b.bottom - b.top) / lh);
    if (fit < 2 || total - fit < 2) return false;
    var r = el.getBoundingClientRect();
    var caret = document.caretRangeFromPoint(r.left + 1, r.top + fit * lh + lh / 2);
    if (!caret || !el.contains(caret.startContainer)) return false;
    var tail = document.createRange();
    tail.setStart(caret.startContainer, caret.startOffset);
    tail.setEnd(el, el.childNodes.length);
    var rest = el.cloneNode(false);
    rest.appendChild(tail.extractContents());
    el.parentNode.insertBefore(rest, el.nextSibling);
    if (box(el).bottom > limit + 0.5 || !rest.textContent.trim()) { // undo if it did not work out
      while (rest.firstChild) el.appendChild(rest.firstChild);
      rest.parentNode.removeChild(rest);
      return false;
    }
    return true;
  }

  function keepsWithNext(el) {
    return /^(H1|H2|H3)$/.test(el.tagName) || el.classList.contains('tcap') || el.classList.contains('prompt');
  }
  function splittable(el) { return el.tagName === 'PRE' || el.tagName === 'UL' || el.tagName === 'OL'; }

  var sections = document.querySelectorAll('section');
  for (var s = 0; s < sections.length; s++) {
    var el = sections[s].firstElementChild;
    if (s > 0 && !atPageTop(box(el).top)) pushToNextPage(el);
    var guard = 0;
    while (el && guard++ < 5000) {
      if (el.classList.contains('spacer') || getComputedStyle(el).position === 'absolute') { el = el.nextElementSibling; continue; }
      var b = box(el), limit = limitOf(pageOf(b.top));
      if (b.top >= limit - 1) { pushToNextPage(el); continue; } // starts inside the bottom margin
      if (b.bottom <= limit) {
        var nx = el.nextElementSibling;
        if (keepsWithNext(el) && nx && !atPageTop(b.top)) {
          var nb = box(nx);
          var tooLow = splittable(nx) ? (limit - nb.top < 40) : (nb.bottom > limit && nb.bottom - nb.top <= H);
          if (tooLow) { pushToNextPage(el); continue; }
        }
        el = el.nextElementSibling;
        continue;
      }
      if (el.tagName === 'PRE' && splitPre(el, limit)) { el = el.nextElementSibling; continue; }
      if ((el.tagName === 'UL' || el.tagName === 'OL') && splitList(el, limit)) { el = el.nextElementSibling; continue; }
      if (el.tagName === 'P' && !el.classList.contains('tcap') && splitPara(el, limit)) { el = el.nextElementSibling; continue; }
      if (!atPageTop(b.top)) { pushToNextPage(el); continue; }
      el = el.nextElementSibling; // taller than a page: leave it
    }
  }

  var pages = pageOf(box(document.querySelector('section:last-of-type')).bottom - 1) + 1;
  document.body.style.height = (pages * P) + 'px';
  for (var p = 1; p < pages; p++) {
    var n = document.createElement('div');
    n.className = 'pnum';
    n.style.top = (p * P + P - 46) + 'px';
    n.textContent = String(p + 1);
    document.body.appendChild(n);
  }

  var toc = {};
  var links = document.querySelectorAll('.toc .entry a');
  for (var i = 0; i < links.length; i++) {
    var id = links[i].getAttribute('href').slice(1);
    var target = document.getElementById(id);
    var page = target ? pageOf(box(target).top) + 1 : null;
    toc[id] = page;
    links[i].parentNode.querySelector('.pg').textContent = page ? String(page) : '?';
  }
  // clickable areas for the PDF: a whole contents line, or the text of any other link
  function where(el) { var b = box(el), pg = pageOf(b.top); return { page: pg, y: b.top - pg * P }; }
  var linkList = [], anchors = document.querySelectorAll('a[href]');
  for (var a = 0; a < anchors.length; a++) {
    var href = anchors[a].getAttribute('href'), dest = null;
    if (href.charAt(0) === '#') {
      var t = document.getElementById(href.slice(1));
      if (!t) continue;
      dest = where(t);
    }
    var row = anchors[a].parentNode.classList.contains('entry') ? anchors[a].parentNode : null;
    var rects = row ? [row.getBoundingClientRect()] : anchors[a].getClientRects();
    for (var k = 0; k < rects.length; k++) {
      var top = rects[k].top + window.pageYOffset, pg = pageOf(top);
      linkList.push({ page: pg, x: rects[k].left, y: top - pg * P, w: rects[k].width, h: rects[k].height,
                      url: dest ? null : href, tpage: dest ? dest.page : null, ty: dest ? dest.y : null });
    }
  }

  // bookmarks: the contents page, then every part and section
  var outline = [{ level: 1, label: 'Contents', page: where(document.querySelector('.toc')).page, y: 0 }];
  var entries = document.querySelectorAll('.toc .entry.l1, .toc .entry.l2');
  for (var e = 0; e < entries.length; e++) {
    var link = entries[e].querySelector('a'), spot = where(document.getElementById(link.getAttribute('href').slice(1)));
    outline.push({ level: entries[e].classList.contains('l1') ? 1 : 2, label: link.textContent.replace(/\s+/g, ' ').trim(),
                   page: spot.page, y: spot.y });
  }

  return JSON.stringify({ pages: pages, toc: toc, links: linkList, outline: outline });
})()
