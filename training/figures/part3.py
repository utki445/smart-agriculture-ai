# ============================================================ PART C7
# Each algorithm goes into a 1x1 bordered table: title on the first line
# inside the box, steps in a monospace face, and no empty paragraph left
# above or below.
def box_algorithm(caption_prefix):
    ps = paras()
    start = None
    for i, p in enumerate(ps):
        if p.text.strip().startswith(caption_prefix):
            start = i
            break
    if start is None:
        note("  !! algorithm not found: %s" % caption_prefix)
        return
    title = ps[start].text.strip()
    lines = []
    end = start
    for j in range(start + 1, len(ps)):
        t = ps[j].text.rstrip()
        if not t.strip():
            end = j
            break
        # the steps are the indented / numbered lines that follow
        lines.append(t)
        end = j

    tbl = doc.add_table(rows=1, cols=1)
    tblel = tbl._tbl
    ps[start]._p.addprevious(tblel)

    # full single-line borders
    pr = tblel.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + edge)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "8")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        borders.append(e)
    for edge in ("insideH", "insideV"):
        e = OxmlElement("w:" + edge)
        e.set(qn("w:val"), "none")
        e.set(qn("w:sz"), "0")
        borders.append(e)
    pr.append(borders)
    w = OxmlElement("w:tblW")
    w.set(qn("w:w"), "5000")
    w.set(qn("w:type"), "pct")
    pr.append(w)

    cell = tbl.cell(0, 0)
    first = cell.paragraphs[0]
    r = first.add_run(title)
    r.font.name = "Consolas"
    r.font.size = Pt(9)
    r.bold = False
    first.alignment = WD_ALIGN_PARAGRAPH.LEFT
    first.paragraph_format.space_after = Pt(3)
    for ln in lines:
        cp = cell.add_paragraph()
        cr = cp.add_run(ln)
        cr.font.name = "Consolas"
        cr.font.size = Pt(8.5)
        cr.bold = False
        cp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        cp.paragraph_format.space_after = Pt(0)
        cp.paragraph_format.space_before = Pt(0)

    # remove the original caption, the step paragraphs and the blank line
    for j in range(start, end + 1):
        el = ps[j]._p
        if el.getparent() is not None:
            el.getparent().remove(el)
    # and any empty paragraph immediately before the new box
    prev = tblel.getprevious()
    if prev is not None and prev.tag == qn("w:p") and not Paragraph(prev, doc).text.strip():
        if not prev.findall(".//" + qn("a:blip")):
            prev.getparent().remove(prev)
    note("C7 boxed %s (%d step lines)" % (title.split(":")[0], len(lines)))


box_algorithm("Algorithm 1:")
box_algorithm("Algorithm 2:")


# ============================================================ PART C3
# Centre the heading styles (not each paragraph) and the table captions.
for sid in ("Title", "Heading1", "Heading2", "Heading3"):
    try:
        st = doc.styles.element.xpath('//w:style[@w:styleId="%s"]' % sid)[0]
    except IndexError:
        continue
    ppr = st.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr")
        st.append(ppr)
    jc = ppr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        ppr.append(jc)
    jc.set(qn("w:val"), "center")
note("C3 Title / Heading 1-3 styles set to centred")

# the paper title itself is a directly formatted paragraph
ps = paras()
ps[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

n = 0
for p in paras():
    if p.text.strip().startswith("Table ") and ":" in p.text[:12]:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        n += 1
note("C3 %d table captions centred (figure captions already were)" % n)


# ============================================================ PART C4
# Bold survives only in the paper title, the headings and table header rows.
def unbold(p):
    hit = False
    for r in p.runs:
        if r.bold:
            r.bold = False
            hit = True
        rpr = r._element.find(qn("w:rPr"))
        if rpr is not None:
            for b in rpr.findall(qn("w:b")) + rpr.findall(qn("w:bCs")):
                rpr.remove(b)
                hit = True
    return hit


n = 0
for p in paras():
    t = p.text.strip()
    if t.startswith("Table ") and ":" in t[:12]:
        n += unbold(p)
    elif t.startswith("Keywords:"):
        n += unbold(p)
note("C4 bold removed from %d captions / Keywords" % n)

# bold inside table bodies (header row keeps its bold)
cells = 0
for tbl in doc.tables:
    for ri, row in enumerate(tbl.rows):
        if ri == 0:
            continue
        for c in row.cells:
            for p in c.paragraphs:
                if unbold(p):
                    cells += 1
note("C4 bold removed from %d body-cell paragraphs" % cells)

# any residual bold in ordinary body paragraphs (headings use styles, so they
# are untouched by this pass only if they carry direct bold -- keep those)
HEAD_STYLES = {"Heading 1", "Heading 2", "Heading 3", "Title"}
n = 0
for p in paras():
    sname = p.style.name if p.style is not None else ""
    if sname in HEAD_STYLES:
        continue
    if p is paras()[0]:
        continue
    t = p.text.strip()
    if t.startswith("Figure ") or t.startswith("Table "):
        continue
    if any(r.bold for r in p.runs):
        # leave the title line alone; everything else loses its bold
        n += unbold(p)
note("C4 bold removed from %d further body paragraphs" % n)


# ============================================================ pagination
# Keep each algorithm box whole, and keep every caption with the thing it
# captions, so nothing is orphaned across a page break.
def set_keep_next(p, on=True):
    pf = p.paragraph_format
    pf.keep_with_next = on


n = 0
for tbl in doc.tables:
    cells = tbl._tbl.findall(".//" + qn("w:tc"))
    is_box = len(tbl.rows) == 1 and len(tbl.columns) == 1
    if is_box:
        for row in tbl.rows:
            trPr = row._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit")
            trPr.append(cs)
        n += 1
note("pagination: %d algorithm boxes set not to split across pages" % n)

n = 0
for p in paras():
    t = p.text.strip()
    if t.startswith("Table ") and ":" in t[:12]:
        set_keep_next(p)          # caption sits above its table
        n += 1
note("pagination: %d table captions kept with their table" % n)

# figure captions sit below the image, so the image paragraph keeps with them
n = 0
for p in paras():
    if p._p.findall(".//" + qn("a:blip")):
        set_keep_next(p)
        n += 1
note("pagination: %d figure images kept with their caption" % n)


# ============================================================ save
doc.save(DST)
note("saved %s" % DST)
