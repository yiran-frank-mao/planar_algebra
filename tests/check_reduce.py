"""Check the reduced form of the package against Python.

For random planar tangles (words of layers made of id, ev, coev and input
discs) the test builds several isotopic variants of each word -- by sliding
generators past each other, inserting zigzags, closed loops and layers of
identities -- and lets the package reduce all of them.  It checks that

  * all variants of a word have the same normal form (\\PAlastnormalform),
    and the number of removed loops (\\PAlastloops) grows by one for every
    inserted loop;
  * the normal form connects the boundary points and the legs of the discs
    exactly as the input word does, and has no closed loops;
  * the normal form is reduced: reducing it again gives it back, and every
    layer has a generator other than id.

Words for which the package stops its search at `max states' (it warns) only
get the checks that do not need a canonical normal form.

The \\PA path (which also draws the diagram) is compared with \\PAdefine.

Run from the repository root:  python3 tests/check_reduce.py [seed] [count]
"""
import os
import random
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ARITY = {"id": (1, 1), "ev": (2, 0), "coev": (0, 2)}
DISCS = [(1, 1), (2, 2), (0, 2), (2, 0), (1, 3), (3, 1), (0, 4), (2, 1),
         (1, 0), (0, 1), (3, 3), (0, 0)]


def arity(item):
    return ARITY[item[0]] if item[0] in ARITY else (item[1], item[2])


def layer_in(layer):
    return sum(arity(g)[0] for g in layer)


def layer_out(layer):
    return sum(arity(g)[1] for g in layer)


def ids(k):
    return [("id",)] * k


# ---------------------------------------------------------------------------
# Invariants: which endpoints the strings connect, and the closed loops.
#
# A closed string that goes around an input disc cannot be shrunk to a point,
# so only the loops that enclose no disc count as loops; the others ("rings")
# are part of the connectivity data, together with the discs they enclose.
# To tell them apart, the word is drawn with straight segments: on the seam
# below layer y the strands are at x = 0, 1, ..., and a disc of the layer is
# at height y + 0.5.  A disc is inside a closed string iff a horizontal ray
# from it crosses the string an odd number of times.
# ---------------------------------------------------------------------------
def connectivity(word, inputs):
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    closed = []
    segments = []   # (node, (x0, y0), (x1, y1))
    centres = []    # (label, x, y)
    fresh = [0]

    def node():
        fresh[0] += 1
        return ("n", fresh[0])

    seam = [("T", i + 1) for i in range(inputs)]
    for x in seam:
        find(x)
    for y, layer in enumerate(word):
        new, i = [], 0
        for g in layer:
            a, b = arity(g)
            ins = seam[i:i + a]
            j = len(new)
            if g[0] == "id":
                segments.append((ins[0], (i, y), (j, y + 1)))
                new.extend(ins)
            elif g[0] == "ev":
                m = i + 0.5
                segments.append((ins[0], (i, y), (m, y + 0.4)))
                segments.append((ins[1], (i + 1, y), (m, y + 0.4)))
                if find(ins[0]) == find(ins[1]):
                    closed.append(ins[0])
                else:
                    union(ins[0], ins[1])
            elif g[0] == "coev":
                c = node()
                find(c)
                m = j + 0.5
                segments.append((c, (j, y + 1), (m, y + 0.6)))
                segments.append((c, (j + 1, y + 1), (m, y + 0.6)))
                new.extend([c, c])
            else:
                top = (i + (a - 1) / 2.0) if a else i - 0.5
                bot = (j + (b - 1) / 2.0) if b else j - 0.5
                centres.append((g[3], (top + bot) / 2.0, y + 0.5))
                for t, x in enumerate(ins):
                    union(x, (g[3], "in", t + 1))
                for t in range(b):
                    z = (g[3], "out", t + 1)
                    find(z)
                    new.append(z)
            i += a
        if i != len(seam):
            raise ValueError("layer %s does not fit %d strands" % (layer, len(seam)))
        seam = new
    for j, x in enumerate(seam):
        union(x, ("B", j + 1))
    classes = {}
    for x in list(parent):
        if x[0] != "n":
            classes.setdefault(find(x), []).append(x)
    pairs = sorted(tuple(sorted(map(repr, v))) for v in classes.values())

    def crossings(root, cx, cy):
        count = 0
        for n, (x0, y0), (x1, y1) in segments:
            if find(n) != root or (y0 > cy) == (y1 > cy):
                continue
            if x0 + (cy - y0) * (x1 - x0) / (y1 - y0) > cx:
                count += 1
        return count

    loops, rings = 0, []
    for x in closed:
        inside = sorted(label for label, cx, cy in centres
                        if crossings(find(x), cx, cy) % 2)
        if inside:
            rings.append(("ring",) + tuple(inside))
        else:
            loops += 1
    return pairs + sorted(rings), loops


# ---------------------------------------------------------------------------
# Random words and isotopic variants
# ---------------------------------------------------------------------------
def random_word(rng, max_width=5, max_layers=5):
    labels = ("D%d" % k for k in range(1, 1000))
    n = rng.randint(0, 4)
    start = n
    word = []
    for _ in range(rng.randint(1, max_layers)):
        layer, left = [], n
        while left > 0 or (not layer and rng.random() < 0.6):
            r = rng.random()
            if r < 0.15:
                layer.append(("coev",))
            elif left >= 2 and r < 0.45:
                layer.append(("ev",))
                left -= 2
            elif r < 0.62:
                a, b = rng.choice(DISCS)
                if a <= left and len(layer) < 6:
                    layer.append(("box", a, b, next(labels)))
                    left -= a
                continue
            elif left >= 1:
                layer.append(("id",))
                left -= 1
            if left == 0 and rng.random() < 0.5:
                break
        while left > 0:
            layer.append(("id",))
            left -= 1
        out = layer_out(layer)
        if not layer or out > max_width:
            continue
        word.append(layer)
        n = out
    if not word:
        word = [ids(start)] if start else [[("coev",)]]
    return start, word


def split_layer(rng, word):
    """Slide the generators of a layer apart (interchange law)."""
    k = rng.randrange(len(word))
    layer = word[k]
    if len(layer) < 2:
        return word
    s = rng.randint(1, len(layer) - 1)
    p, q = layer[:s], layer[s:]
    if rng.random() < 0.5:
        new = [p + ids(layer_in(q)), ids(layer_out(p)) + q]
    else:
        new = [ids(layer_in(p)) + q, p + ids(layer_out(q))]
    return word[:k] + new + word[k + 1:]


def seam_width(start, word, k):
    return start if k == 0 else layer_out(word[k - 1])


def insert_zigzag(rng, start, word):
    k = rng.randint(0, len(word))
    n = seam_width(start, word, k)
    if n == 0:
        return word
    i = rng.randrange(n)
    if rng.random() < 0.5:
        new = [ids(i + 1) + [("coev",)] + ids(n - i - 1),
               ids(i) + [("ev",)] + ids(n - i)]
    else:
        new = [ids(i) + [("coev",)] + ids(n - i),
               ids(i + 1) + [("ev",)] + ids(n - i - 1)]
    return word[:k] + new + word[k:]


def insert_loop(rng, start, word):
    k = rng.randint(0, len(word))
    n = seam_width(start, word, k)
    i = rng.randint(0, n)
    new = [ids(i) + [("coev",)] + ids(n - i), ids(i) + [("ev",)] + ids(n - i)]
    return word[:k] + new + word[k:]


def insert_ids(rng, start, word):
    k = rng.randint(0, len(word))
    n = seam_width(start, word, k)
    if n == 0:
        return word
    return word[:k] + [ids(n)] + word[k:]


def variants(rng, start, word):
    """(word, number of inserted loops) for several isotopic variants."""
    out = [(word, 0)]
    for _ in range(4):
        w, loops = word, 0
        for _ in range(rng.randint(1, 4)):
            r = rng.random()
            if r < 0.4:
                w = split_layer(rng, w)
            elif r < 0.75:
                w = insert_zigzag(rng, start, w)
            elif r < 0.9:
                w = insert_loop(rng, start, w)
                loops += 1
            else:
                w = insert_ids(rng, start, w)
        out.append((w, loops))
    return out


# ---------------------------------------------------------------------------
# TeX input and normal forms
# ---------------------------------------------------------------------------
def tex_item(g):
    if g[0] == "box":
        return "%s(%d,%d)" % (g[3], g[1], g[2])
    return g[0]


def tex_word(start, word, options):
    parts, n = [], start
    for k, layer in enumerate(word):
        opts = "[%s]" % options if k == 0 and options else ""
        parts.append("\\PA%s{%d,%d}{%s}" % (opts, n, layer_out(layer),
                                            ", ".join(map(tex_item, layer))))
        n = layer_out(layer)
    return "".join(parts)


NF_LAYER = re.compile(r"\\PA\{(\d+),(\d+)\}\{([^{}]*)\}")


def parse_normal_form(text):
    layers = NF_LAYER.findall(text)
    if "".join("\\PA{%s,%s}{%s}" % l for l in layers) != text:
        raise ValueError("cannot parse normal form %r" % text)
    start = int(layers[0][0]) if layers else 0
    word = []
    for _, _, body in layers:
        layer = []
        for item in filter(None, (s.strip() for s in body.split(", "))):
            m = re.fullmatch(r"(\w+)\((\d+),(\d+)\)", item)
            if m:
                layer.append(("box", int(m.group(2)), int(m.group(3)),
                              m.group(1)))
                continue
            m = re.fullmatch(r"(id|ev|coev)(?:\^(\d+))?", item)
            if not m:
                raise ValueError("bad item %r in %r" % (item, text))
            layer.extend([(m.group(1),)] * int(m.group(2) or 1))
        word.append(layer)
    return start, word


def run_tex(cases):
    """cases: list of (tag, tex chain); returns {tag: (loops, nf)}."""
    lines = []
    for tag, chain in cases:
        if tag.startswith("pa:"):
            lines.append("\\setbox0\\hbox{%s}" % chain)
        else:
            lines.append("\\PAdefine[reduce]{tmp}{%s}" % chain)
        lines.append("\\typeout{RESULT %s|\\PAlastloops|\\PAlastnormalform|}"
                     % tag)
    doc = ("\\documentclass{article}\n\\usepackage{planaralgebra}\n"
           "\\begin{document}\n%s\n\\end{document}\n" % "\n".join(lines))
    env = dict(os.environ, TEXINPUTS=ROOT + "//:", max_print_line="100000")
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "t.tex"), "w") as fh:
            fh.write(doc)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "t.tex"],
                       cwd=tmp, env=env, capture_output=True, text=True)
        with open(os.path.join(tmp, "t.log"), errors="replace") as fh:
            log = fh.read()
    errors = re.findall(r"^! .*", log, re.M)
    results, capped = {}, False
    for line in log.splitlines():
        if "Warning: The normal form was chosen" in line:
            capped = True
        m = re.match(r"RESULT (\S+)\|(\d+)\|(.*?)\|", line)
        if m:
            results[m.group(1)] = (int(m.group(2)), m.group(3), capped)
            capped = False
    return results, errors


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    rng = random.Random(seed)
    words, cases = [], []
    for w in range(count):
        start, word = random_word(rng)
        vs = variants(rng, start, word)
        words.append((start, word, vs))
        for v, (vw, _) in enumerate(vs):
            cases.append(("w%d.%d" % (w, v), tex_word(start, vw, "")))
        cases.append(("pa:w%d" % w, tex_word(start, word, "reduce")))
    results, errors = run_tex(cases)
    failures = []
    if errors:
        failures.append("TeX errors: %s" % errors[:5])
    again, skipped = [], 0
    for w, (start, word, vs) in enumerate(words):
        pairs, loops = connectivity(word, start)
        tag = "w%d" % w
        got = [results.get("%s.%d" % (tag, v)) for v in range(len(vs))]
        if None in got:
            failures.append("%s: no result" % tag)
            continue
        # The search for the normal form stopped at `max states': it need not
        # be canonical, but it must still be a reduced form of the tangle.
        exact = not any(c for _, _, c in got)
        skipped += not exact
        base_loops, nf, _ = got[0]
        for v, ((vw, added), (l, f, _)) in enumerate(zip(vs, got)):
            if (exact and f != nf) or l != base_loops + added:
                failures.append(
                    "%s: variant %d gives %d; %s, expected %d; %s\n  %s\n  %s"
                    % (tag, v, l, f, base_loops + added, nf,
                       tex_word(start, word, ""), tex_word(start, vw, "")))
        pa = results.get("pa:" + tag)
        if pa is None or pa[:2] != (base_loops, nf):
            failures.append("%s: \\PA gives %s, \\PAdefine %s"
                            % (tag, pa, (base_loops, nf)))
        if base_loops != loops:
            failures.append("%s: %d loops, expected %d (%s)"
                            % (tag, base_loops, loops, tex_word(start, word, "")))
        try:
            nstart, nword = parse_normal_form(nf)
        except ValueError as err:
            failures.append("%s: %s" % (tag, err))
            continue
        if nword and nstart != start:
            failures.append("%s: normal form starts with %d strands" % (tag, nstart))
        try:
            npairs, nloops = connectivity(nword, start)
        except ValueError as err:
            failures.append("%s: normal form %s is not a tangle: %s (%s)"
                            % (tag, nf, err, tex_word(start, word, "")))
            continue
        if npairs != pairs or nloops:
            failures.append("%s: normal form %s changes the tangle (%s)"
                            % (tag, nf, tex_word(start, word, "")))
        for layer in nword:
            if len(nword) > 1 and all(g[0] == "id" for g in layer):
                failures.append("%s: layer of identities in %s" % (tag, nf))
        if nword and exact:
            again.append((tag, nf, tex_word(nstart, nword, "")))
    results2, errors2 = run_tex([("r" + t, chain) for t, _, chain in again])
    if errors2:
        failures.append("TeX errors: %s" % errors2[:5])
    for tag, nf, _ in again:
        r = results2.get("r" + tag)
        if r is None or (not r[2] and r[:2] != (0, nf)):
            failures.append("%s: reducing %s again gives %s" % (tag, nf, r))
    for f in failures:
        print(f)
    print("seed %d: %d words (%d with an incomplete search), %d variants, "
          "%d failures" % (seed, len(words), skipped, len(cases), len(failures)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
