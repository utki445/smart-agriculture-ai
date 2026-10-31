# ============================================================ PART C2
# Swap in the redrawn / re-plotted figures and resize each to the width it
# occupies on the page (A4 with 25.4 mm margins gives a 6.27 in text column).
# Figure 4 is left untouched: it is an accurate flowchart already well above
# 300 dpi at its printed size.
NEW_FIGS = {                      # figure number -> (file, printed width in)
    1: ("fig1_architecture.png", 6.10),
    2: ("fig2_circuit.png", 6.10),
    3: ("fig3_prototype.png", 5.00),
    5: ("fig5_control_law.png", 5.70),
    6: ("fig6_accuracy.png", 6.10),
    7: ("fig7_distribution.png", 6.10),
    8: ("fig8_f1_vs_photos.png", 3.90),
    9: ("fig9_confusion.png", 6.10),
    10: ("fig10_simulation.png", 6.10),
}
EMU = 914400

blips = body.findall(".//" + qn("a:blip"))
note("C2 found %d images in the document" % len(blips))
for idx, blip in enumerate(blips, start=1):
    if idx not in NEW_FIGS:
        continue
    fname, width_in = NEW_FIGS[idx]
    path = os.path.join(FIGDIR, fname)
    data = open(path, "rb").read()
    rid = blip.get(qn("r:embed"))
    part = doc.part.related_parts[rid]
    part._blob = data
    with Image.open(path) as im:
        pw, ph = im.size
    cx = int(round(width_in * EMU))
    cy = int(round(width_in * ph / pw * EMU))
    drawing = blip
    while drawing is not None and drawing.tag != qn("w:drawing"):
        drawing = drawing.getparent()
    for e in drawing.iter():
        if e.tag in (qn("wp:extent"), qn("a:ext")):
            e.set("cx", str(cx))
            e.set("cy", str(cy))
    note("  Fig %-2d <- %-26s %dx%d px, printed %.2f in wide (%d dpi)"
         % (idx, fname, pw, ph, width_in, round(pw / width_in)))


# ============================================================ PART C1
# A 2-4 sentence summary directly after every table and figure.
TABLE_SUMMARIES = {
 1: "Table 1 places this study against the work it draws on. The baseline "
    "system [1] shares the sensing concept but keeps its decisions in the "
    "cloud, while the leakage studies [13], [14] supply the method rather than "
    "the domain. No row combines a soil-image classifier with a stated "
    "photograph-level split, which is the gap this paper measures.",
 2: "Table 2 lists the five GPIO assignments the firmware uses: GPIO 4 for the "
    "DHT11, GPIO 34 for the analogue moisture channel, GPIO 26 for the relay "
    "driver, and GPIO 13 and 14 for the status LEDs. GPIO 34 is input-only and "
    "carries ADC1_CH6, which is why the probe is read there. Every measurement "
    "and hardware test reported below was taken on this wiring.",
 3: "Table 3 shows that four purchased modules account for ₹470 of the "
    "₹970 total, the balance covering the pump, transistor, LEDs, "
    "resistors and consumables. At roughly US$11–12 the node costs about "
    "a quarter of the US$44 baseline [1]. The optional ACS712 current sensor "
    "at ₹145 would add about 15% to the total and is the cheapest route "
    "to detecting the fault discussed in §4.3.",
 4: "Table 4 sets out the three datasets. The soil-type set expands 16 source "
    "photographs into 4,194 samples and the condition set expands 14 into 294, "
    "so both are large in samples and very small in photographs — the "
    "condition under which the choice of split protocol matters most. The "
    "telemetry log contributes 8,171 records over 4.5 h and is used only for "
    "control-law and noise characterisation.",
 5: "Table 5 records seven fault-injection tests, each run once. Five behaved "
    "exactly as specified; the two that did not are both faults the firmware "
    "has no way to observe. TC-07, in which the pump stopped while the node "
    "went on reporting that irrigation was taking place, is the more "
    "consequential and is examined in §4.3.",
 6: "Table 6 is the central result of the paper. Holding out whole "
    "photographs drops soil-type accuracy from 91.9–94.0% to "
    "44.6–46.8%, a gap of 45.0–47.9 points, and soil-condition "
    "accuracy from 98.6–99.7% to 75.5–86.1%, a gap of "
    "13.6–23.1 points. The soil-type gap is well above the 5–30 "
    "points reported for medical images [13], and the exact test over "
    "photographs makes it certain for every backbone "
    "(p = 3.1 × 10⁻⁵) while leaving the condition gap "
    "significant for only two backbones of three.",
 7: "Table 7 is the reason the intervals in Table 6 are quoted over "
    "photographs rather than over samples. For the same predictions the two "
    "interval estimates differ by an order of magnitude in width, and the two "
    "significance tests disagree about the soil-condition gap. Reporting only "
    "the sample-level figures would have made a result that rests on four "
    "photographs look decisive.",
 8: "Table 8 shows source-disjoint F1 rising with the number of photographs "
    "behind a class: 0.70–0.74 for Clay with seven, 0.35–0.41 for "
    "Sand with five, below 0.06 for Loamy sand with two, and exactly zero for "
    "the two classes represented by a single photograph. A class with one "
    "photograph cannot be predicted at all once that photograph is held out, "
    "which is why the macro average stays near 0.23.",
 9: "Table 9 gives per-class soil-condition F1 for the three backbones. "
    "Cracked soil, whose pattern survives a change of image, is recognised "
    "most reliably at 0.859–0.982; compacted soil, which has three source "
    "images of which one is atypical, is recognised least reliably at "
    "0.562–0.724. The ordering of the four classes is the same for all "
    "three backbones, which is what makes the images rather than the "
    "architecture the likely explanation.",
 10: "Table 10 reports the simulated flag rates. With thresholds fixed from "
     "normal behaviour alone, the pulse-response test flags none of the "
     "healthy or offset-drifted probes and 2.2% of the gain-drifted ones, "
     "while flagging every fouled, dislodged, disconnected and submerged "
     "probe. The static clamp check catches only the disconnected probe, and "
     "would raise the same flag for genuinely air-dry soil.",
 11: "Table 11 summarises what the node can and cannot detect today. Only the "
     "DHT11 failure and the loss of the serial link are handled; probe faults "
     "and the stopped pump pass unnoticed. In simulation the proposed test "
     "would flag four of these conditions, and would correctly let calibration "
     "drift through, because a drifted probe still responds to water.",
 12: "Table 12 compares the node with the baseline system [1]. It costs about "
     "a quarter as much, keeps irrigating without a network and adds an image "
     "channel, at the price of no water-level sensor and a control loop that "
     "is still open. The machine-learning row is the honest one: soil "
     "condition is promising at 75.5–86.1%, but soil type at "
     "44.6–46.8% is not usable.",
 13: "Table 13 checks measured behaviour against what the firmware, the "
     "literature or the baseline predict. Telemetry interval, switching "
     "threshold, dry-air reading and relay-transition count all behave as "
     "designed. The two rows that depart from expectation are soil-type "
     "accuracy, where only the augmentation-level figure resembles published "
     "work, and the size of the leakage effect, which exceeds the "
     "5–30 points reported for medical imaging [13].",
}

FIGURE_SUMMARIES = {
 1: "Figure 1 shows the four layers and, more importantly, where the boundary "
    "between them falls. The ESP32 reads both sensors, applies the hysteresis "
    "rule and drives the relay by itself once a second; everything past the "
    "serial link logs, classifies and advises. Because no host process can "
    "actuate the relay, irrigation continues unchanged when the laptop or the "
    "network is unavailable.",
 2: "Figure 2 gives the wiring behind Table 2. Both sensors sit on the 3.3 V "
    "rail, GPIO 26 drives the relay through a BC547B and a 1 kΩ base "
    "resistor, and the two status LEDs are current-limited at 220 Ω. The "
    "pump runs from a separate 5 V supply that shares a ground with the ESP32, "
    "so the relay contact switches the pump circuit alone.",
 3: "Figure 3 shows the assembled node. The probe sits in a sealed container "
    "of soil that could be wetted and left to dry, which is how every hardware "
    "test and the whole telemetry log were produced. The arrangement is "
    "repeatable and convenient, but it is not a field deployment, a limitation "
    "returned to in §5.",
 4: "Figure 4 traces one pass of the implemented loop. Each iteration reads "
    "both sensors, applies Eq. (2), updates the LEDs, prints one JSON record "
    "and waits a second; a failed DHT11 read sends nulls and irrigation "
    "continues on moisture alone. The figure also shows what is absent: no "
    "path returns from the pump to the controller, which is the structural "
    "cause of TC-07.",
 5: "Figure 5 plots a measured 14-minute session, beginning at 78% moisture, "
    "with the pump state reconstructed under both rules. A single set point "
    "would have switched the relay six times against four for the implemented "
    "hysteresis rule. Every logged sample is marked, so the flat stretches are "
    "measured values rather than a line drawn across a gap in the log.",
 6: "Figure 6 shows the result of Table 6 together with its uncertainty. The "
    "augmentation-level bars stand above 91% for every backbone and both "
    "tasks, while the source-disjoint bars for soil type fall to the dotted "
    "majority-class line at 43.3%. The intervals, taken over photographs "
    "rather than samples, are wide enough for soil type that the accuracy on "
    "its own would mislead.",
 7: "Figure 7 explains why those intervals are so wide. The five "
    "augmentation-level folds agree to within about two points, whereas "
    "accuracy on individual held-out photographs covers almost the whole range "
    "from 0 to 100%. With EfficientNetV2-B0, 2 of the 16 soil-type "
    "photographs are never classified correctly and none is classified "
    "perfectly, giving a standard deviation of 35.9 points.",
 8: "Figure 8 plots source-disjoint F1 against the number of photographs "
    "behind each class, for all three backbones. The relationship is monotone "
    "and steep, and the two single-photograph classes sit at zero whichever "
    "backbone is used. The practical reading is that more source photographs, "
    "not a different network, is what would lift this curve.",
 9: "Figure 9 shows where the errors go. For soil type the Loam and Sandy "
    "Loam rows have an empty diagonal and spread across the other classes, and "
    "413 of the 1,320 Sand samples are read as Clay. For soil condition the "
    "only substantial error is the 22 of 63 compacted samples read as "
    "waterlogged, which is what lowers waterlogged precision to 0.708.",
 10: "Figure 10 shows the three things the simulation has to establish. Panel "
     "(a) is the response model the decision rules act on, panel (b) the flag "
     "rates of Table 10, and panel (c) the sensitivity sweep discussed below. "
     "Reading (a) together with (b), the fouled and dislodged traces are "
     "caught because they never rise after the pulse, and the free-water trace "
     "because it rises at once.",
}


# --- C1 also asks that, where a paragraph already states a table's numbers
# --- before the table, it be cut back to a lead-in so the summary is not a
# --- repetition. Three paragraphs need that.
LEADINS = {
    "Table 6 and Fig. 6 give the main result.":
        "Table 6 and Fig. 6 give the main result of this study.",
    "With thresholds set from normal behaviour alone":
        "The three thresholds were set from normal behaviour alone — "
        "π_min = 0.239 points per mL, τ_min = 3.6 s and "
        "g_max = 8.0 points per second — and then frozen. Table 10 and "
        "Fig. 10 give the outcome. The offset-drift result is the important "
        "one: a probe reading 20 points too high or too low passes, correctly, "
        "because it still responds to water.",
}
for prefix, repl in LEADINS.items():
    p = find_para(prefix)
    if p is None:
        note("  !! lead-in not found: %r" % prefix[:40])
        continue
    set_text(p, repl)
    note("C1 lead-in trimmed before %s" % prefix[:28])

# --- tables: the caption sits above the table, so insert after the table ---
added = 0
for ch in list(body.iterchildren()):
    if ch.tag != qn("w:tbl"):
        continue
    prev = ch.getprevious()
    while prev is not None and prev.tag != qn("w:p"):
        prev = prev.getprevious()
    cap = Paragraph(prev, doc).text.strip() if prev is not None else ""
    num = None
    if cap.startswith("Table "):
        try:
            num = int(cap.split()[1].rstrip(":"))
        except ValueError:
            num = None
    if num in TABLE_SUMMARIES:
        insert_after(ch, body_para(TABLE_SUMMARIES[num]))
        added += 1
    else:
        note("  !! no summary matched for table caption %r" % cap[:50])
note("C1 added %d table summaries" % added)

# --- figures: the caption sits below the image, so insert after the caption ---
added = 0
for p in paras():
    t = p.text.strip()
    if not t.startswith("Figure "):
        continue
    try:
        num = int(t.split()[1].rstrip(":"))
    except ValueError:
        continue
    if num in FIGURE_SUMMARIES:
        insert_after(p._p, body_para(FIGURE_SUMMARIES[num]))
        added += 1
note("C1 added %d figure summaries" % added)
