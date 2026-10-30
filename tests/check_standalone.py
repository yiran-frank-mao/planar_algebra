"""Compile diagrams in documents of class `standalone` and check the pages.

With the class option `tikz`, every TikZ picture becomes a page of its own,
which would break diagrams inside formulas.  Each case lists the expected
number of (cropped) pages and of package warnings.

Run from the repository root:  python3 tests/check_standalone.py
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

EQUATION = r"""\[
\PA{0,2}{coev}\PA{2,2}{x}\PA{2,0}{ev} \circ \PA{1,1}{id}
  = \PA[reduce]{0,2}{coev}\PA{2,0}{ev}
  = \PA[reduce, coefficient=false]{0,2}{coev}\PA{2,4}{id, coev, id}\PA{4,2}{id, ev, id}
\]"""

# (name, class options, body, pages, warnings); pages=None skips the count.
CASES = [
    ("display", "tikz, border=1pt", EQUATION, 1, 0),
    ("inline", "tikz, border=1pt",
     r"\( \PA{2,2}{x} = \PA[reduce, labels]{2,2}{x}\PA{2,2}{id^2} \)",
     1, 0),
    ("two-formulas", "tikz, border=1pt",
     r"\[ \PA{2,2}{x} \] \[ \PA[horizontal]{2,0}{ev} \]", 2, 0),
    ("top-level", "tikz, border=1pt",
     r"\PA{0,2}{coev}\PA{2,0}{ev} \PAgenerators[names]", 2, 0),
    ("mixed", "tikz, border=1pt",
     r"\begin{tikzpicture}\draw (0,0) -- (1,1);\end{tikzpicture}"
     + EQUATION + r"\PA[horizontal]{2,2}{x}", 3, 0),
    ("class-math", "tikz, math, border=1pt", EQUATION, 1, 0),
    ("multi", "multi=tikzpicture, border=1pt", EQUATION, 1, 0),
    ("preview", "tikz, preview, border=1pt", EQUATION, 1, 0),
    ("varwidth", "varwidth, border=1pt", EQUATION, 1, 0),
    ("dollar", "tikz, border=1pt", r"$\PA{2,2}{x}$", None, 1),
    ("equation", "tikz, border=1pt",
     r"\begin{equation*} \PA{2,2}{x} \end{equation*}", None, 1),
]

TEMPLATE = r"""\documentclass[%s]{standalone}
\usepackage{amsmath}
\usepackage{planaralgebra}
\AddToHook{shipout/before}{\typeout{PAGE \the\pdfpagewidth\space\the\pdfpageheight}}
\begin{document}
%s
\end{document}
"""


def to_pt(s):
    return float(s[:-2])


def main():
    failures = 0
    env = dict(os.environ, TEXINPUTS=ROOT + "//:")
    with tempfile.TemporaryDirectory() as tmp:
        for name, opts, body, pages, warnings in CASES:
            with open(os.path.join(tmp, name + ".tex"), "w") as fh:
                fh.write(TEMPLATE % (opts, body))
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", name + ".tex"],
                cwd=tmp, env=env, capture_output=True, text=True)
            with open(os.path.join(tmp, name + ".log"), errors="replace") as fh:
                log = fh.read()
            errors = re.findall(r"^! .*", log, re.M)
            got_warnings = log.count("Package planaralgebra Warning")
            sizes = [(to_pt(w), to_pt(h)) for w, h in
                     re.findall(r"^PAGE (\S+) (\S+)$", log, re.M)]
            problems = []
            if errors:
                problems.append("errors: %s" % errors[:3])
            if got_warnings != warnings:
                problems.append("%d warnings, expected %d"
                                % (got_warnings, warnings))
            if pages is not None:
                if len(sizes) != pages:
                    problems.append("%d pages, expected %d"
                                    % (len(sizes), pages))
                if any(w > 500 or h > 150 for w, h in sizes):
                    problems.append("page not cropped: %s" % sizes)
            status = "FAIL" if problems else "ok"
            print("%-13s [%s] %s %s" % (name, opts, status, "; ".join(problems)))
            failures += bool(problems)
    print("%d cases, %d failures" % (len(CASES), failures))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
