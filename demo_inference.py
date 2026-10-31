"""Run the trained soil models on sample images and print the result.

A quick way to confirm the system works without flashing the ESP32 or
starting the dashboard:

    python demo_inference.py                  # uses clay.jpg and loam.jpg
    python demo_inference.py path/to/soil.jpg

Note the soil-type accuracies reported in the project report are measured
under source-disjoint cross-validation (44.6-46.8 %), not from single-image
demonstrations like this one. See training/source_disjoint_eval.py.
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.soil_predictor import SoilPredictor
from app.soil_condition_predictor import SoilConditionPredictor

BAR = "=" * 62
RULE = "-" * 62


def show(images):
    print(BAR)
    print("SMART AGRICULTURE AI - INFERENCE DEMONSTRATION")
    print(BAR)
    print("run at %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

    soil = SoilPredictor()
    cond = SoilConditionPredictor()

    for img in images:
        if not os.path.exists(img):
            print("%s  -- not found, skipped" % img)
            continue
        print(RULE)
        print("INPUT IMAGE : %s" % img)
        print(RULE)

        r = soil.predict_detailed(img)
        print("Soil type      : %s" % r.get("predicted_class"))
        print("Confidence     : %.1f %%" % (100 * r.get("confidence", 0.0)))
        probs = r.get("all_probabilities") or {}
        if probs:
            print("Class scores   :")
            for k, v in sorted(probs.items(), key=lambda x: -x[1]):
                print("    %-12s %6.2f %%  %s" % (k, 100 * v, "#" * int(round(40 * v))))

        c = cond.predict(img)
        print("Soil condition : %s" % c.get("condition"))
        print("Confidence     : %.1f %%" % (100 * c.get("confidence", 0.0)))
        cprobs = c.get("all_probabilities") or {}
        if cprobs:
            print("Class scores   :")
            for k, v in sorted(cprobs.items(), key=lambda x: -x[1]):
                print("    %-12s %6.2f %%  %s" % (k, 100 * v, "#" * int(round(40 * v))))
        advice = c.get("advice")
        if isinstance(advice, dict):
            print("Assessment     : %s" % advice.get("label", "-"))
            print("Description    : %s" % advice.get("description", "-"))
            print("Irrigation     : %s" % advice.get("irrigation_hint", "-"))
        elif advice:
            print("Advice         : %s" % advice)
        print()

    print(RULE)
    print("Note: the deployed classifier appends three normalised sensor values")
    print("to the image features, then trims the vector back to the length the")
    print("saved scaler was fitted on (1,382). Every prediction above is")
    print("therefore image-only, which is what the report evaluates.")
    print(RULE)


if __name__ == "__main__":
    args = sys.argv[1:] or ["clay.jpg", "loam.jpg"]
    show(args)
