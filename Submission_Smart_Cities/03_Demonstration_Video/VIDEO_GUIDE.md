# Demonstration Video — Guide

**Limit: 10 minutes.** Place the finished file in this folder.
Suggested name: `Project_Demonstration_Smart_Cities.mp4`

---

## Suggested running order

This maps onto the report so an evaluator watching the video and reading the report sees
the same structure.

| Time | Segment | What to show |
|---|---|---|
| 0:00–0:40 | **Problem** | State it plainly: cities irrigate parks, medians and green roofs on timers; a timer cannot tell it rained yesterday. Over- and under-watering happen in the same green space. |
| 0:40–1:30 | **What was built** | The assembled node on camera. Name the parts: ESP32, capacitive probe, DHT11, BC547B driver, relay, pump. Say the cost — ₹970. |
| 1:30–2:30 | **Architecture** | Show the architecture diagram. Land the key point: the irrigation decision is taken on the ESP32 and the host *cannot* operate the relay. |
| 2:30–4:30 | **Live demo — the control loop** | Serial monitor open at 115200. Probe in air → moisture drops → relay clicks on, green LED blinks. Probe into wet soil/water → moisture rises → relay clicks off. **This is the core demo — don't rush it.** |
| 4:30–5:30 | **Dashboard** | Live gauges, sensor history, the 48-hour irrigation advisory with watering windows. |
| 5:30–6:30 | **Soil classification** | Upload a soil photo, show the classification and the crop/suitability output. Export the PDF report. |
| 6:30–8:00 | **Testing — including what fails** | Walk the 7 fault tests. Demonstrate **TC-07** live if you can: pull the pump supply while it runs and show the dashboard still reporting "irrigating". |
| 8:00–9:15 | **The unique outcome** | The evaluation finding: 91.9–94.0 % under conventional evaluation vs 44.6–46.8 % source-disjoint. Explain *why* — the classifier was recognising photographs, not soils. |
| 9:15–10:00 | **Outcome and next steps** | ₹970/node, works without a network, 17 % fewer relay actuations, 5/7 tests passed. ACS712 (₹145) as the fix for TC-07. |

---

## Points worth making on camera

These are the things that distinguish this project, so say them out loud rather than
leaving them on a slide:

1. **"The node never asks a server whether to irrigate."** Across a fleet, a network outage
   degrades visibility, not service.
2. **"We found a failure we cannot detect."** TC-07 — the pump dies and the system keeps
   reporting irrigation. Showing a flaw you found yourself reads as rigour, not weakness.
3. **"Our classifier looked 94 % accurate and wasn't."** Then explain the photograph-level
   split. This is the unique outcome.

---

## Practical notes

- **Record the serial monitor and dashboard with screen capture**, not a phone pointed at a
  monitor — text must be legible.
- **Check audio before the full take.** Bad audio sinks an otherwise good demo.
- If the hardware misbehaves on the day, the dashboard runs without the ESP32 attached
  (it replays `data/latest.json`) — but say so rather than implying it is live.
- **Do not quote the old 94 % accuracy figure** as if it were the result. The report states
  44.6–46.8 % source-disjoint; the video must agree with it.

## Before you call it done

- [ ] Under 10 minutes
- [ ] Audio audible throughout
- [ ] Serial output and dashboard text readable at playback resolution
- [ ] The live relay switch is clearly visible or audible
- [ ] Accuracy figures match the report
- [ ] File placed in this folder
