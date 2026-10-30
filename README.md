# planaralgebra

A LaTeX package for drawing planar tangles and planar algebra diagrams with
TikZ, in the style of [plumber](https://github.com/yiran-frank-mao/plumber).
A tangle is described layer by layer: each `\PA{m,n}{items}` is one layer
going from `m` to `n` strands, and consecutive `\PA` commands are stacked
into one tangle.

```latex
\usepackage{planaralgebra}   % loads TikZ

\PAdefine{T}{\PA{2,4}{coev, id, id}\PA{4,2}{id, ev, S(1,1)}}

\[
  \PA[numbers]{4,4}{D(2,2), A(1,1), id}\PA{4,4}{id, id, B(2,2)}\PA{4,2}{id, id, ev}
  \circ_3 \PA{2,4}{coev, id, id}\PA{4,2}{id, ev, S(1,1)}
  = \PA[insert={3=T}]{4,4}{D(2,2), A(1,1), id}\PA{4,4}{id, id, B(2,2)}\PA{4,2}{id, id, ev}
\]
```

## Features

- Generators `id`, `ev` (cup, 2 → 0) and `coev` (cap, 0 → 2); any other item
  `label(a,b)` is an input disc with `a` strands on the input side and `b` on
  the output side. `item^k` repeats an item.
- Checkerboard shading (`sign=+`/`-`, `shading=false`, `shade=<colour>`),
  stars on every disc, an outer disc that is a `circle`, `ellipse`,
  `rectangle` or `none`, and round or rectangular input discs.
- `vertical` (default), `horizontal` and `reverse` orientations.
- `numbers` (numbers of the input discs) and `labels` (numbers of the
  boundary points).
- `reduce`: computes a normal form of the tangle. Closed loops become a
  coefficient `\delta^k` (`loop value`, `coefficient`), zig-zags are pulled
  straight, and discs are put in a canonical order. `\PAlastloops`,
  `\PAlastboxes` and `\PAlastnormalform` report the result.
- `\PAdefine{name}{...}` stores a tangle; `insert={i=name}` composes it into
  input disc `i`, and `expand` replaces every disc labelled with a defined
  name.
- `\PAgenerators` / `\PAgenerators*` draw a list of items side by side.
- Customisable TikZ styles (`pa string`, `pa shaded`, `pa box`, `pa outer`,
  `pa star`, ...) and layout keys (`strand sep`, `length`, `box size`, `margin`,
  `scale`, ...).
- Works with `\documentclass[tikz]{standalone}`: a formula in `\[...\]` or
  `\(...\)` becomes one cropped page.

See [`planaralgebra-doc.pdf`](planaralgebra-doc.pdf) for the manual and
[`examples/tangles.pdf`](examples/tangles.pdf) for more examples.

## Building and testing

```sh
make doc        # planaralgebra-doc.pdf
make examples   # examples/tangles.pdf
make test       # reduced-form and standalone tests (needs python3 and pdflatex)
```

`tests/check_reduce.py [seed] [count]` draws random tangles, builds isotopic
variants of each (sliding generators past each other, inserting zig-zags,
loops and identity layers) and checks that the package gives all of them the
same normal form, that the normal form has the same connectivity as the
input, and that reducing a normal form gives it back.

The package is written in expl3, needs a LaTeX kernel from 2020-10 or newer
and TikZ, and is distributed under the LaTeX Project Public License 1.3c.
