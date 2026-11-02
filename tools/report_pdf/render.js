// Lay out the report HTML in macOS WebKit, paginate it with paginate.js and write every page as vector PDF.
// Usage: osascript -l JavaScript render.js <report.html> <paginate.js> <out.pdf> [preview_dir]
// Title, author and subject of the PDF come from the HTML's <title> and <meta name="author|subject">.
ObjC.import('Cocoa');
ObjC.import('WebKit');
ObjC.import('Quartz');

const readText = p => ObjC.unwrap($.NSString.stringWithContentsOfFileEncodingError($(p), 4, null));

function run(argv) {
  const [htmlPath, jsPath, pdfPath, previewDir] = argv;
  const W = 595, P = 842;
  const app = $.NSApplication.sharedApplication;
  app.setActivationPolicy(2); // no Dock icon, no menu bar
  const rect = $.NSMakeRect(0, 0, W, P);
  const win = $.NSWindow.alloc.initWithContentRectStyleMaskBackingDefer(rect, 0, 2, false); // never shown
  const wv = $.WebView.alloc.initWithFrameFrameNameGroupName(rect, $(), $());
  win.setContentView(wv);
  wv.mainFrame.frameView.setAllowsScrolling(false); // no scroll bar, so the layout is exactly 595 px wide
  wv.mainFrame.loadRequest($.NSURLRequest.requestWithURL($.NSURL.fileURLWithPath($(htmlPath))));

  const pump = s => $.NSRunLoop.currentRunLoop.runUntilDate($.NSDate.dateWithTimeIntervalSinceNow(s));
  const js = c => ObjC.unwrap(wv.stringByEvaluatingJavaScriptFromString($(c)));
  const view = wv.mainFrame.frameView.documentView; // flipped: y grows downwards, like the page
  const t0 = Date.now();
  const laidOut = "document.readyState === 'complete' && Array.prototype.every.call(document.images, function (i) { " +
                  "var r = i.getBoundingClientRect(); return i.complete && i.naturalWidth > 0 && r.width > 0 && " +
                  "Math.abs(r.height - r.width * i.naturalHeight / i.naturalWidth) < 1.5; }) ? 'yes' : 'no'";
  const startsOk = "JSON.stringify(Array.prototype.map.call(document.querySelectorAll('section.part > h1, section.toc > h1'), " +
                   "function (h) { return Math.round(h.getBoundingClientRect().top + window.pageYOffset) % 842; }))";

  // Load, let fonts and images settle (one throw-away drawing of the whole document), paginate, and check that
  // every part still starts at the top of a page. A layout that moved afterwards is reloaded and paginated again.
  let result = null, attempts = 0;
  while (result === null) {
    if (++attempts > 3) throw new Error('layout kept moving after pagination');
    if (attempts > 1) wv.mainFrame.reload;
    pump(0.2);
    while (js(laidOut) !== 'yes') {
      if (Date.now() - t0 > 120000) throw new Error('report did not load within 120 s');
      pump(0.1);
    }
    wv.setFrame($.NSMakeRect(0, 0, W, 60000)); // a tall viewport, so caretRangeFromPoint reaches every line
    pump(0.3);
    view.dataWithPDFInsideRect(view.bounds); // warm-up drawing
    pump(0.5);
    const r = JSON.parse(js(readText(jsPath)));
    pump(0.8);
    const starts = JSON.parse(js(startsOk));
    if (starts.every(y => Math.abs(y - 64) <= 1)) result = r;
  }
  result.attempts = attempts;
  let doc = null;
  for (let k = 0; k < result.pages; k++) {
    const one = $.PDFDocument.alloc.initWithData(view.dataWithPDFInsideRect($.NSMakeRect(0, k * P, W, P)));
    if (doc === null) doc = one;
    else doc.insertPageAtIndex(one.pageAtIndex(0), doc.pageCount);
  }
  // links: drop whatever WebKit wrote per page, then add working ones (jumps inside the PDF, web links outside)
  let removed = 0;
  for (let k = 0; k < doc.pageCount; k++) {
    const page = doc.pageAtIndex(k), anns = page.annotations;
    for (let j = anns.count - 1; j >= 0; j--) {
      if (ObjC.unwrap(anns.objectAtIndex(j).type) === 'Link') { page.removeAnnotation(anns.objectAtIndex(j)); removed++; }
    }
  }
  const linkType = $.PDFAnnotationSubtypeLink || $('/Link');
  const noBorder = () => { const b = $.PDFBorder.alloc.init; b.setLineWidth(0); return b; };
  const destination = (page, y) => $.PDFDestination.alloc.initWithPageAtPoint(doc.pageAtIndex(page), $.NSMakePoint(0, Math.min(P, P - y + 14)));
  for (const l of result.links) {
    const ann = $.PDFAnnotation.alloc.initWithBoundsForTypeWithProperties($.NSMakeRect(l.x, P - l.y - l.h, l.w, l.h), linkType, $());
    if (l.url) ann.setURL($.NSURL.URLWithString($(l.url)));
    else ann.setDestination(destination(l.tpage, l.ty));
    ann.setBorder(noBorder());
    doc.pageAtIndex(l.page).addAnnotation(ann);
  }
  // bookmarks for the side bar of PDF viewers
  const root = $.PDFOutline.alloc.init;
  let part = null;
  for (const o of result.outline) {
    const item = $.PDFOutline.alloc.init;
    item.setLabel($(o.label));
    item.setDestination(destination(o.page, o.y));
    if (o.level === 1 || part === null) { root.insertChildAtIndex(item, root.numberOfChildren); part = item; }
    else part.insertChildAtIndex(item, part.numberOfChildren);
  }
  doc.setOutlineRoot(root);

  const meta = JSON.parse(js("JSON.stringify({ title: document.title, " +
    "author: (document.querySelector('meta[name=author]') || {}).content || '', " +
    "subject: (document.querySelector('meta[name=subject]') || {}).content || '' })"));
  const attrs = $.NSMutableDictionary.dictionary;
  attrs.setObjectForKey($(meta.title), $('Title'));
  attrs.setObjectForKey($(meta.author), $('Author'));
  attrs.setObjectForKey($(meta.subject), $('Subject'));
  doc.setDocumentAttributes(attrs);
  doc.writeToFile($(pdfPath));
  result.linksRemoved = removed;
  result.linksAdded = result.links.length;
  result.bookmarks = result.outline.length;
  delete result.links;
  delete result.outline;

  if (previewDir) {
    const shown = [1, 2, result.toc.part1, result.toc.refs].filter(Boolean);
    for (const p of shown) {
      const img = doc.pageAtIndex(p - 1).thumbnailOfSizeForBox($.NSMakeSize(1190, 1684), 0);
      $.NSBitmapImageRep.imageRepWithData(img.TIFFRepresentation)
        .representationUsingTypeProperties(4, $())
        .writeToFileAtomically($(previewDir + '/page' + p + '.png'), true);
    }
    result.previews = shown;
  }
  result.seconds = Math.round((Date.now() - t0) / 1000);
  return JSON.stringify(result);
}
