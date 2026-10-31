import sys, os
base = os.path.dirname(os.path.abspath(__file__))
g = {"__file__": os.path.join(base, "build_v2.py"), "__name__": "__main__"}
for f in ("build_v2.py", "part2.py", "part3.py"):
    exec(compile(open(os.path.join(base, f), encoding="utf-8").read(), f, "exec"), g)
