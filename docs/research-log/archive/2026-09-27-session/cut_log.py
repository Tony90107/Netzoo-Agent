"""Write the research log truncated just before `## Log <next>｜` (or whole if next is 'end')."""
import sys
main, dest, nxt = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(main, encoding="utf-8").read()
if nxt != "end":
    marker = f"\n## Log {nxt}｜"
    text = text[:text.index(marker) + 1]
open(dest, "w", encoding="utf-8").write(text)
