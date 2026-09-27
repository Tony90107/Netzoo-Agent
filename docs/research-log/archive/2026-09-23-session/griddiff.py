import json, sys
from collections import Counter
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
c = Counter(); ex = {}
for k in a:
    for view in a[k]:
        if a[k][view] != b[k][view]:
            sig = (view, str(a[k][view]), str(b[k][view]))
            c[sig] += 1; ex.setdefault(sig, k)
print("changed view-cells:", sum(c.values()), "outcomes changed:", sum(1 for k in a if a[k] != b[k]))
for sig, n in c.most_common(40): print(n, sig, "e.g.", ex[sig])
