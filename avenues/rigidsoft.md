# Avenue: rigidsoft (2026-11-12 and 13, rounds 17, 19, 20, 21 and 22)

**Round 22: no certified gain. New spare-home orders and corner radii improved near misses, but none passed the take rule. Section 16 has the measurements.**

**Round 21: no certified gain, 0 n. The fault move now runs on a band that holds a row with an extra square (`rigidsoft_fault2.py`, control green). With the default fq settings every such start falls to a far jam 0.21 above the bar. The round set of fq at corner radius 0.2 or 0.3 takes these starts to within 1e-3 to 2e-3 of the bar on 297, 328, 332 and 409. Kick scans then take 1e-4 to 1.5e-3 off. The nearest end is 328 at 18.612630613, 5.6e-5 above the bar. Section 15 has the round.**

**Round 20: 1 n certified. 907 is in the take, 7.06e-05 of score under the round 18 file and 5.57e-05 under round 19. The band reader now sees the teeth of a band that a fault has moved, so a second band can move inside the first one. On 907 that band took 2 changes of sense out and the side 0.00168 down. Only a band with no extra square inside it that takes changes out paid. Chains of that rule from the held 907, 494, 365 and 328 found no second gain. Two bands at once and two builders of a block turned one way have red controls and found nothing. Section 14 has the round.**

**Round 19: 8 n certified, and 5 of them are in the take with 0.00053 of score. Two moves do it. In the fault move a band of rows of a soft block moves one diagonal track. The two squares left over become one more tilted square in the row before the band and in the row after it. The flip then sets a row that the fault has freed to the sense of its neighbours. They took 263, 297, 328, 332, 365, 409, 494 and 907 below the held side. Other lanes built lower layouts of 263, 332 and 409 from ours and hold those n. Section 13 has the round.**

**Round 17: no certified gain, 0 n. The idea as it was put is dead. 0 of 178 starts on the held rigid layouts and 0 of 221 fresh rigid blocks end below the held side. The round found what a soft block is: a stack of rows, turned both ways in bands, with a side that follows from the turn by one rule. The board's sides on 297, 332, 409 and 494 fit the same blocks with fewer bands. No move of this round takes a band out.**

The slice is every n where we hold a rigid 45° form and the board sits just under it. The idea was that the board's layouts there are our rigid blocks made soft. The rows are in [`results/rigidsoft-r17-2026-11-12.tsv`](../results/rigidsoft-r17-2026-11-12.tsv).

Words used here: the side is `L = m + f`, and `k = n − m²`. A *rigid block* is `a × b` squares at exactly 45° on one lattice. Its *threshold* is the smallest f at which the rule of [structure](structure.md) section 2 lets it fit. A *soft block* is the same squares turned a little off 45°. Its chains still run along the exact diagonal, and each square is slid against the one before. The *quench* is `fq quench`, with every square free. "Fq-soft" is the form the quench makes from a rigid block. "Deep" is the form of the held 261, which is 0.0056 below the fq-soft form of the same block.

## 1. The slice

Held file `gather/round15-2026-11-12a.csv`, board of 2026-11-09, n ≥ 100, board lower by 1e-4 to 3e-2 of side.

| held f | block | n | gap of score | n |
|---|---|---|---|---|
| 0.5208 | 17 × 17 | 7 | 0.00362 | 626, 677, 730, 785, 842, 901, 962 |
| 0.5355 | 5 × 5, one or two | 13 | 0.00678 | 401, 442, 485, 530, 577, 578, 627, 678, 731, 786, 843, 902, 963 |
| 0.6066 | 15 × 15 | 3 | 0.00109 | 489, 534, 581 |
| 0.6569 | 8 × 8, 15 × 8 | 3 | 0.00148 | 147, 329, 366 |
| 0.6924 | 13 × 13 | 3 | 0.00173 | 367, 407, 448 |
| 0.7042 | 14 × 13 | 1 | 0.00036 | 295 |
| 0.7071 | strip, 1 × 19 to 1 × 39 | 8 | 0.00399 | 262, 449, 492, 538, 585, 635, 686, 853 |
| 0.7279 | 18 × 18, 1 × 18 | 3 | 0.00128 | 202, 636, 741 |
| 0.7782 | 11 × 11 | 1 | 0.00007 | 298 |
| **all** | every tilted square at 45° | **42** | **0.0204** | |

Only 5 of the 42 have the board within 0.003 of side: 298, 407, 489, 538 and 578 (0.00039 of score). 536 is the sixth (two 8 × 8 blocks, one already loose, board 0.0003 under).

A second group is 132 n where several n share our f and the layout is not all at 45°. It is worth 0.0362 of score. 38 of them are within 0.003 of side (0.00238). They are sheared diagonal bands (0.5914 at 41.0°, 0.5838 at 39.65° and 42.2°, 0.5649 at 34.6°) and fq-soft blocks (0.7561 at 43.6°, 0.7332 at 43.8°, 0.7404 at 44.7°). The bands belong to the [band](band.md) lane. The fq-soft blocks are in sections 4 and 6.

## 2. Kill line (written before the first long run)

- **Control.** The held 261 is side 16.678779876: one soft block of 8 chains of 13 squares at 41.88°. Its rigid parent is the same block at exactly 45° at side 16.6925 (`structure_shear.py`, eps = 0, 261 squares by the exact fill). The tool gets the rigid parent and must end within 1e-6 of the held side. A quench of the parent with no operator is the negative control: it must stay above 16.69, or the control proves nothing about the operators.
- **Kill.** When the control is green, the same operators run on the rigid n of the slice, in the order of their gap to the board. The idea is dead if no start ends more than 1e-9 of side below the held side on the first 12 n.
- When the control is red, the tool cannot say anything about the slice, and the report says so.

## 3. The controls

**261: red, and the negative control failed too.** `rigidsoft.py` gave the rigid parent to the quench alone and with four shear operators. The shear angle has `tan = (√2/2)/13`, which is 3.11°. The operators use that angle and twice that angle, with both signs.

| start | side after the quench |
|---|---|
| rigid parent, no operator | 16.684379478 |
| the four shears at 3.11° | 16.684379478, four times |
| shears at 6.21° | 16.684379478 twice, 17.095 once, one failed |
| held 261 | 16.678779876 |

So the quench alone softens this rigid block by 0.0080 of side, and the operators add nothing: the quench pushes a sheared block back into the same basin. It stops 0.0056 above the held layout. The block ends at 43.9° (60 squares) and 46.1° (22), against 41.88° in the held layout.

More tries on the same control, all red:

| try | starts | result |
|---|---|---|
| every position of the rigid block in the box, exact fill, quench (`rigidsoft_scan.py`) | 8 | 16.684289549 to 16.684379486 |
| tight sheared block at 1°, 2° and ±3.118°, tolerant fill (0.03 to 0.15), quench | 664 placed, 131 reached 261 squares | 16.684379478 at 1° and 2°. At 3.118° the fill is 1 to 3 squares short, and the mirror shear ends at 16.81 |
| the same at 2.6°, 3.118° and 3.6° with a tolerance of 0.2 | 57 | the fill counts 4 to 9 squares too many, and the quench ends at 16.90 or above |
| the same at sides 0.014 to 0.05 above the held side, tolerance 0 and 0.03 | 2,048 | 3 to 15 squares short, nothing to quench |
| one slide per chain and one more square per chain end, a coordinate search on the exact-fill count (`deep`) | 65 positions, about 128 fills each | 2 to 14 squares short |
| kicks of 0.005 to 0.04 and a quench, from the fq-soft result | 128 | 16.684287734, 0.00009 lower |
| tight sheared block at ±3.118° at a side 0.0005 and 0.002 above the held side, where the fill sees the block pulled 1% to 4.5% toward its centre and the quench gets the true block | 528 placed, 111 reached 261 squares | 16.684379478 every time: the quench turns the block back from 3.118° to 1.1° |
| the same, with the uprights frozen for a first stage so that only the block moves | 39 placed, 17 reached 261 squares | the frozen stage ends at side 17.68 or above, and the result is the plain grid |
| one soft-box island from the fq-soft result | 30,350 children in 115 s | the box went down twice, to 16.683979, with no find. Stopped there for the next control |
| six stiffer or softer quench settings (`stiff3`, `stiff5`, `shrink`, `shrink1`, `round`, `soft` of `rigidsoft.py`) from the tight sheared block | 12 that reached 261 squares, 72 quenches | 16.684313573 at best |
| a block sheared along both diagonals (`rigidsoft_pin.py`, section 7) with the tolerant fill | 736 placed, 120 reached 261 squares | 16.684379478 every time |

**451: green.** The scan of section 4 placed the rigid 6 × 23 block (threshold 0.763456) at m = 21. All 4 positions quench to 21.756097561. The held 451 is 21.756097562. So the tool rebuilds a held soft layout from its rigid parent, to 1e-9.

What the two controls say together: the quench reaches the fq-soft form of a block and not the deep form. The held 261 is the only deep form we know.

## 4. What the quench does to a rigid block

`rigidsoft_scan.py plan` lists single blocks `a × b` (a, b ≤ 40) for every n with m = 12 to 31. A block is listed when its rule gain at its threshold is at least k and its threshold is at most 0.03 above our f. `run` places the block at up to 10 positions of the box, fills the uprights exactly, and quenches. The jobs ran in the order of threshold minus held f. 1,034 jobs ran, which is every threshold up to 0.012 above our f: 110 n, 221 pairs of n and block. 377 placements were one square short (the plan lets a block in one unit of m below the rule).

| block shape | pairs (n, block) | moved by the quench | softening (threshold minus quenched f) |
|---|---|---|---|
| square (5 × 5, 10 × 10, 11 × 11, 13 × 13, 15 × 15, 18 × 18) | 35 | 0 | 0 |
| strip one square wide | 83 | 4, all 1 × 30 falling to the plain strip value 0.7071 | 0 |
| rectangle | 103 | 33 | 0.0011 to 0.0080 |

The softening by rectangle:

| rectangle | softening |
|---|---|
| 8 × 13 | 0.0080 |
| 6 × 23 | 0.0074 |
| 3 × 22 | 0.0049 to 0.0064 |
| 6 × 25 | 0.0050 to 0.0055 |
| 3 × 29, 3 × 34, 3 × 36 | 0.0040 |
| 3 × 27 | 0.0024 |
| 6 × 30 | 0.0022 |
| 3 × 15 | 0.0021 |
| 3 × 39 | 0.0019 |
| 5 × 34 | 0.0016 |
| 6 × 18 | 0.0014 |
| 13 × 25, 10 × 22 | 0.0011 |

**No pair ends below the held side** (0 of 221, beyond the 2e-9 of the float-safe margin). The nearest:

| n | block | threshold | quenched f | held f | above held |
|---|---|---|---|---|---|
| 328 | 3 × 22 | 0.6213 | 0.614964 | 0.614369 | 0.00060 |
| 297, 332 | 6 × 18 | 0.7426 | 0.741250 | 0.740417 | 0.00083 |
| 907 | 3 × 39 | 0.6213 | 0.619430 | 0.618366 | 0.00106 |
| 230 | 8 × 13 | 0.6924 | 0.684379 | 0.682927 | 0.00145 |
| 494 | 6 × 25 | 0.7426 | 0.737646 | 0.736096 | 0.00155 |

Two facts for the idea:

- **A square block does not move.** Both extents are tight, and the quench returns the rule's threshold from every fresh arrangement of the uprights. A rectangle moves only as far as the slack of its short extent lets it turn.
- **The single-block class is used up, soft or rigid.** Where a softened rectangle lands at or below our side, the public files already hold that layout. 451 is one quench of the 6 × 23 block.

## 5. The idea on the held rigid layouts

`rigidsoft.py gen` wrote, for each n, the held layout as it is and with every block sheared or turned. The operators are the staircase angle along either axis, a shear of 1° along either axis and a rigid turn of 1°. Each has both signs per block. `run` quenched each start with the ALM from the same side and with the default flags, then the deep flags. A second set starts from the held n + 1 with one upright next to a block taken out.

| n | starts | back at the held side | ended above | ended below |
|---|---|---|---|---|
| 536 | 21 | 9 | 12 | 0 |
| 578 | 21 | 21 | 0 | 0 |
| 298 | 11 | 11 | 0 | 0 |
| 407 | 11 | 11 | 0 | 0 |
| 489 | 11 | 11 | 0 | 0 |
| 538 | 11 | 9 | 2 | 0 |
| 844 | 11 | 9 | 2 | 0 |
| 202 | 11 | 9 | 2 | 0 |
| 627 | 21 | 21 | 0 | 0 |
| 449 | 11 | 9 | 2 | 0 |
| 147 | 11 | 11 | 0 | 0 |
| **11 n** | **151** | **131** | **20** | **0** |

"Back" is within 5e-9 of the held side. The twelfth n, 903, was taken out of the queue for time: one of its starts takes 30 s. From the held n + 1 with one upright out, 27 starts ran on 536, 407, 627, 401 and 577. The best is the held side on 627, 401 and 577, and the side of n + 1 on 536 and 407. None is below.

**The kill line is met: 0 of 178 starts end below the held side.** The rigid layouts are closed against a shear, a turn and one free cell. With section 4 this is the answer for the idea as it was put: a rigid square block or strip has no soft version near it.

## 6. The near misses, with kicks and the soft-box island

The fresh fq-soft layouts of section 4 that ended within 0.0016 of the held side got a chain each. The chain is 4 minutes of kicks and quenches (`rigidsoft.py kick`), then one soft-box island (`methods_soft.py`, 12 minutes, `--dry 300`).

| n | block | one quench | after the kicks (quenches) | after the island (children, finds) | held | above held |
|---|---|---|---|---|---|---|
| 328 | 3 × 22 | 18.614964 | 18.614944 (35) | 18.614944 (128,334, 0) | 18.614369 | 0.00057 |
| 332 | 6 × 18 | 18.741250 | 18.740663 (120) | 18.740663 (118,339, 0) | 18.740417 | 0.00025 |
| 297 | 6 × 18 | 17.741250 | 17.740929 (120) | 17.740729 (135,843, 1) | 17.740417 | 0.00031 |
| 907 | 3 × 39 | 30.619430 | 30.618944 (17) | 30.618743 (70,509, 1) | 30.618366 | 0.00038 |
| 230 | 8 × 13 | 15.684379 | 15.684314 (120) | 15.684314 (189,587, 0) | 15.682927 | 0.00139 |
| 494 | 6 × 25 | 22.737646 | 22.737528 (18) | stopped after 62 s for the chains on the held layouts | 22.736096 | 0.00143 |

The kicks take a fresh fq-soft layout down by 0.00002 to 0.00059 of side. The island adds at most 0.0002. None reaches the held side: the held layouts of this class are these same layouts after more polish.

The same chain then ran on the held layouts of this class, 3 minutes of kicks and one island of up to 7 minutes each:

| n | block | held side | kicks: quenches, lower | island: children, finds |
|---|---|---|---|---|
| 230 | 8 × 13 | 15.682926830 | 87, 0 | 93,359, 0 |
| 263 | | 16.733166009 | 73, 0 | 102,148, 0 |
| 328 | 3 × 22 | 18.614368939 | 34, 0 | 89,299, 0 |
| 365 | 3 × 22 | 19.612856389 | 99, 0 | 87,601, 0 |
| 450 | | 21.733166009 | 39, 0 | 73,582, 0 |
| 451 | 6 × 23 | 21.756097562 | 42, 0 | 64,568, 0 |
| 494 | 6 × 25 | 22.736096176 | 16, 0 | 63,163, 0 |
| 539 | | 23.732037288 | 9, 0 | 62,102, 0 |
| 540 | 6 × 23 | 23.756097562 | 33, 0 | 57,500, 0 |
| 907 | 3 × 39 | 30.618366066 | 17, 0 | 36,429, 0 |

None of the 10 moved: 449 quenches and 729,731 island children, no lower side.

Pairs of blocks: `rigidsoft_scan.py plan --two` listed 16,319 placements of one block or two on 15 n of the slice. The n are 578, 627, 536, 844, 407, 489, 298, 538, 449, 451, 540, 263, 450, 297 and 332. 9,900 had the two blocks on top of each other and 6,399 were short of n. 20 reached n, all of them single blocks, and none ended below the held side.

## 7. What a soft block is

Measured on the held 230, 451 and 261 (`rigidsoft_topo.py`, and the lattice index of the tilted squares):

- **Every square is turned by the same angle.** The centres stay near the 45° lattice. A square touches its two neighbours along full sides and is slid against each of them. In 230 (104 squares at 43.6028°, where cos = 21/29 and sin = 20/29) the slide is 1/29 in two steps of three. In 261 (41.882°) it is about 1/13 in three steps of five. We call this block *doubly sheared*. `sblock` of the scan slides the squares along one diagonal only, so its fills ended short.
- **The staircases fix the form.** The quench never moves an upright to another row. So the rows of uprights around the block decide which soft form the quench reaches.

The uprights are four staircases, one in each corner of the box. The table gives the squares per row, from the wall corner outward. The *ends* face the short sides of the block and the *sides* face the long sides.

| layout | f | tilted | end 1 | end 2 | side 1 | side 2 |
|---|---|---|---|---|---|---|
| held 584, rigid 8 × 25 | 0.677670 | 200 | 6, 5, 4, 3, 2, 1 | 6, 5, 4, 3, 2, 1 | 18 down to 1 | 18 down to 1 |
| fq-soft 230, 8 × 13 | 0.684379 | 104 | 6, 5, 4, 3, 2, 1 | 5, 4, 3, 2, 1 | 9 down to 1 | 9 down to 1 |
| held 230, 8 × 13 | 0.682927 | 104 | 6, 5, 4, 2, 1 | 6, 5, 4, 2, 1 | 9 down to 1 | 9 down to 1 |
| held 261, 8 × 13 + 1 | 0.678780 | 105 | 7, 7, 6, 4, 3, 2, 1 | 6, 5, 4, 2, 1 | 9, 9, 9, 8 down to 1 | 9 down to 1 |

In the held 230 and 261 each end has a *kink*. Part of its teeth stand on one diagonal line, and the rest stand on the next line, one step back. The rigid layout has no kink. The fq-soft 230 has none either: its two ends hold 21 and 15 uprights, and the held 230 holds 18 at each end.

**Control A, green.** `rigidsoft_topo.py held` keeps the held uprights of 230. It puts a uniform doubly sheared 8 × 13 block (`rigidsoft_pin.pblock`, 1.397°) at the centre of the held block. The start side is 0.001 and 0.004 larger. The quench ends at 15.682926829 on 6 of 6 starts. The held side is 15.682926830. With the squares turned the other way it ends at 15.79.

**The same block with the general fill, red.** `rigidsoft_pin.py shear` gives the doubly sheared block to the tolerant fill. On 230, 48 placements reached 230 squares and ended at 15.684290 to 15.684379. On 261, 120 reached 261 squares and ended at 16.684379478. That fill builds the staircases of the fq-soft form, and the quench cannot change them.

### The deep form

The lattice index of the held 261 shows what its extra square is. The block has 8 chains. Five have 13 squares. The next one has 14. The last two have 13 and start one square later. So one long side of the block stands one square further along than the other, and the kinks of the two ends follow that step.

**Control B, green.** `rigidsoft_topo.py deep` writes the start from numbers only. They are the row counts of the table, the stepped block on the uniform lattice at 3.118°, and the place of its first square. That place is two numbers, fitted to the held layout. At a side 0.001 and 0.004 larger the quench ends at 16.678779875 on 4 of 4 starts. The held side is 16.678779876.

**Control C, green: the deep 261 from nothing.** `rigidsoft_step.py scan` takes only n, the block shape 8 × 13 and the rule below. It moves the stepped block over a grid of places. For each place it builds the four staircases on their wall lattices, each row from its wall to the block. A cell is taken when it clears the tilted squares shrunk by 0.2 to 0.3. It quenches each new set of row counts that has exactly n squares. Of the first 22 sets, two end at the held side: 16.678779875 and 16.678779878. This is the first tool of ours that builds the deep form, and the general filler was what failed before.

**The rule.** The turn δ of the deep form has `sin δ = (√2/2)/b`, and the side follows from `f = (√(2b² − 1) − B)/2`, with b the squares per chain and `B = ceil(b√2 − 2f)` as in the rigid rule. It gives 0.678779878 for b = 13, and the held 261 has 0.678779876. The reason: a chain of b squares lies between a tooth of one end and a tooth of the other end. The two teeth are one diagonal track apart. Both teeth are corners of wall-anchored squares, so that is possible only when **B is odd**. Up to b = 45 that leaves 21 values of b with f between 0.5 and 1. Ten of them:

| b | 6 | 10 | 13 | 17 | 20 | 23 | 27 | 30 | 34 | 37 |
|---|---|---|---|---|---|---|---|---|---|---|
| rigid threshold | 0.7426 | 0.5711 | 0.6924 | 0.5208 | 0.6421 | 0.7635 | 0.5919 | 0.7132 | 0.5416 | 0.6630 |
| deep f | 0.7131 | 0.5534 | 0.6788 | 0.5104 | 0.6333 | 0.7558 | 0.5853 | 0.7073 | 0.5364 | 0.6582 |

**It has almost no target.** The form needs slack across the block: `a√2 − 2f` must stay under the same whole number A as in the rigid rule. With that test and the rigid count, a deep block with a < b is below the held side on two n only, 451 and 230. On 451 the block is 6 × 23, with a deep f of 0.755768 against 0.756098, worth 1.55e-5 of score.

**The scan on the candidates.** A *set* is one set of row counts with exactly n squares. Each set gets two quenches.

| n | block | placements | sets quenched | best side | held side |
|---|---|---|---|---|---|
| 451 | 6 × 23, the step after 1, 2 or 3 chains | 1,222 | 93 | 21.756097561 | 21.756097562 |
| 451 | 6 × 23, the step after 2, 3 or 4 chains | 789 | 115 | 21.761971514 | 21.756097562 |
| 230 | 8 × 13 | 2,583 | 54 | 15.690123527 | 15.682926830 |
| 260 | 3 × 20 | 1,722 | 0 | none | 16.633520951 |
| 410 | 6 × 23 | 2,583 | 0 | none | 20.764282967 |

On 451 the stepped start ends at the held form and at nothing lower. On 230 it ends 0.0072 above. On 260 and 410 the box is one unit of m smaller than the rule asks, and no start has n squares. Two starts cut down from the deep 261, with one row of uprights and one chain out, have 230 squares and end at 15.7674 and 15.7708 (12 quenches).

A block with no slack across ends at the rigid threshold of its short extent. 290 (5 × 17, 532 placements, 48 sets) ends at 17.535533906, and the held side is 17.535533907. 406 (8 × 20, 9 sets) ends at 20.656854259 against 20.656854250. 205 (4 × 16, 1,722 placements) never reaches n squares.

**584, the rigid 8 × 25, where the board is 0.0010 under.**

| start | starts | result |
|---|---|---|
| fresh rigid block at 5 places, exact fill | 1 reached 584 squares | 24.677669530, the rigid side |
| kicks from the held layout | 114 quenches | 0 lower |
| block sheared along one diagonal, tolerant fill | 169 placed, 18 reached 584 squares | the rigid side every time |
| uniform doubly sheared block in the held uprights, 8 turns from 0.4° to 2.5°, both signs | 64 quenches | 24.67766953 every time |
| stepped block of 8 × 25 + 1 squares in four hand-made sets of kinked row counts | 214 quenches | 24.751 at best |
| step scan with one step | 10 sets | 24.791672917 at best |
| step scan with two steps | 3,528 placements | no start: the block with two more squares does not fit the box |

**The board's values are not deep forms.** We compared each board value just under one of our rigid values with `(√(2b² − j²) − B)/2` for j = 1 to 6. None matches to 3e-6, except one chance match at 416.

## 8. One upright moved to another row

`rigidsoft_hop.py` takes the last square of one staircase row and adds a square to the end of another row, then quenches with every square free. This is the idea of the lane in its smallest step: the staircases change by one square, and the quench does the rest.

**Control, green.** From the deep 261, the hop of one square from row 2 to row 3 of the bottom left staircase quenches to 16.682864700. From that layout 162 hops ran, and one ends at 16.678779875, the deep form again.

| n | hops in the list | hops quenched | best side | held side |
|---|---|---|---|---|
| 261 | 318 | 30 | 16.678779876 | 16.678779876 |
| 536 | 1,058 | 438 | 23.656854249 | 23.656854251 |
| 584 | 474 | 331 | 24.677669530 | 24.677669531 |


**No hop ends below the held side.** The best results are 1.1e-9 to 1.2e-9 under it. That is the rounding of the quench, and the take needs more. Most hops end 0.1 to 0.3 above: the quench cannot close the hole that the moved square leaves. No list was run to its end, because one hop costs 4 s on the loaded box.

**The lists of these runs were short.** The tool refused a target cell next to a quenched square. Such a square sits 1e-9 to 1e-7 off its cell, and the test asked for a full unit of room. The test now allows 0.03 (`FREE`). The full list of the held 584 has 2,076 hops and that of the held 536 has 1,308. So the hop is not closed on these n.

## 9. The block turned with no step

`rigidsoft_step.py scan --plain` places the block with no step, turned by a given angle, and builds the staircases as in control C. `turn_f` gives the side of the start. A chain of b squares turned by ε touches a tooth at each end, and the two teeth are one diagonal track apart. The two touch points are W apart across the chain, with `2b² + 2W² = (B + 2f)² + 1`. W = √(1/2) is the rigid block and W = 0 the deep form, so every f between the two has its turn.

**Control, red.** On 230 the scan placed the 8 × 13 block at 1.397° with both signs: 882 placements, 46 sets, and the best is 15.684379478, the fq-soft side. The builder gives the ends 6, 5, 4, 3, 2, 1 and 5, 4, 3, 2, 1. It never gives the kinked ends of the held 230. So this scan cannot say that a turned block has no lower form.

| n | block and turn | placements | sets quenched | at the held side | above | below |
|---|---|---|---|---|---|---|
| 448 | 13 × 13 at 1.84°, both signs | 793 | 45 | 8 | 37 | 0 |
| 407 | 13 × 13 at 0.17°, both signs | 716 | 43 | 6 | 37 | 0 |

Each run had 4 minutes, and only the first angle of its list ran.

## 10. The kink move

The row counts of section 7 say how the held 230 differs from the fq-soft 230. Three squares have gone from the last three rows of one end to the first three rows of the other end. `rigidsoft_hop.py run --moves kink` makes that move in one step. It takes the last square of K neighbouring rows of one staircase and adds a square to K neighbouring rows of the staircase in the opposite corner. A *run* is a set of neighbouring rows whose counts go down by one per row. The source rows are the last K of a run, and the target rows are the first K of a run (`--only lf`). `--ang` sets every tilted square to one angle first.

**Control, green.** The start is the fq-soft 230 at 15.684379478, built by the scan of section 9.

| block angle before the quench | K = 1 | K = 2 | K = 3 |
|---|---|---|---|
| as the quench left it | 15.793017628 | 16.000000000 | 16.000000000 |
| 43.603° | 15.685323739 | 15.770611574 | **15.682926829** |
| 44.3° | 15.685588411 | 15.762625449 | **15.682926829** |
| 45° | 15.793017628 | 15.746209223 | 16.000000000 |
| 45.7° | 15.793017628 | 15.939441228 | 15.928672769 |
| 46.397° | 15.793017628 | 16.000000000 | no layout |

The move with K = 3 and the block turned the right way ends at the held 230 (15.682926830). The move alone does not: the block has to be turned first, and the sign matters more than the size.

**The control ran with a short list.** It had 3 moves, because of the free-cell test of section 8. The fix adds moves and takes none away. Every run below used the fixed tool, with K up to 8.

**The move on a fresh fq-soft layout.** The scan of section 4 left fresh fq-soft layouts within 0.0034 of the held side. Their ends are equal, and their two long sides differ by one row. So the move runs between the side staircases. Each layout ran as the quench left it, and with the block set to angles from 43.6° to 46.4°. One block can leave several fresh forms with the same side, and the table counts them.

| n | block | parent side | forms | quenches | best side | held side |
|---|---|---|---|---|---|---|
| 297 | 6 × 18 | 17.741250 | 2 | 90 | 17.742762 | 17.740417 |
| 332 | 6 × 18 | 18.741250 | 3 | 42 | 18.742762 | 18.740417 |
| 494 | 6 × 25 | 22.739488 | 1 | 54 | 22.737542 | 22.736096 |

On 297 and 332 no move ends below its parent. On 494 the best moves take the parent down by 0.0019. That is just under the other fresh form of that block (22.737646) and 0.0014 above the held side. The best result on 494 then got the move a second time, for a part of its list.

| n | first parent | quenches | best side | held side |
|---|---|---|---|---|
| 494 | 22.739488 | 13 | 22.825663 | 22.736096 |

No move, first or second, ends below the held side. The kink pays at the ends of the block, where 230 has it. It does not pay along the long sides of these blocks.

**The move on the held layouts.** A move exists only where a wall row has a free cell. With the fixed tool, 69 held layouts have a block near 45° and an `lf` move with K of 2 or more. `work/kink-count.tsv` in the take dir lists every n. The queue ran the `lf` moves on 7 of them, with the block set to 44.3°, 45.7°, 43° and 47°. That made 227 quenches: 58 at the held side, 169 above, and none below. The layouts that end at the held side hold rigid square blocks, and the quench returns the rigid side.

**The move on the held soft layouts.** Five of those held layouts have a block that is already turned, as the fq-soft 230 has. They are the closest case to the control. The `lf` moves ran on them as they are and with the block set to angles on both sides of its own.

| n | block angle | quenches | at the held side | best side | held side |
|---|---|---|---|---|---|
| 199 | 44.218° | 288 | 1 | 14.614689853 | 14.614689854 |
| 228 | 41.690° | 57 | 0 | 15.612724047 | 15.604601476 |
| 328 | 44.178° | 52 | 0 | 18.653913484 | 18.614368939 |
| 365 | 43.993° | 152 | 0 | 19.652042439 | 19.612856389 |
| 494 | 44.203° | 172 | 0 | 22.821852698 | 22.736096176 |

None ends below the held side.

A second queue ran every kink move of the `lf` and `fl` kinds, with the block set to 44.5° and 45.5°. It ran on the held layouts where the board is just under.

| n | quenches | best side | held side |
|---|---|---|---|
| 297 | 44 | 17.833712732 | 17.740417288 |
| 536 | 5 | 23.817782733 | 23.656854251 |
| 584 | 52 | 24.717514421 | 24.677669531 |

None ends below the held side.

**Two more kinds, with no control.** `ff` and `ll` move squares between the two staircases on one wall, in the rows next to a tip of the block. They ran on the held 584 only: as it is, with the block at 44.5°, and part of the list at 45.5°.

| n | quenches | at the held side | best side | held side |
|---|---|---|---|---|
| 584 | 103 | 14 | 24.677669530 | 24.677669531 |

14 of the 103 quenches return the held side. The others end 0.039 or more above it.

**The first control of the lane, end to end.** The control of section 3 asks for the held 261 from a fresh rigid 8 × 13 block. It was red at 0.0056 above. The chain of this section gets closer. The scan places the rigid block, and the quench ends at the fq-soft 261, 16.684379478. The kink with K = 3 and the block at 43.603° or 44.3° ends at 16.682926829. That is the form of the held 230 one size up, with f = 28/41. The held 261 is the deep form, 16.678779876. It has 105 tilted squares and 156 uprights, and the kinked form has 104 and 157. A hop or a kink keeps both counts. 180 hops from the kinked form end at 16.682926829 at best. So this control stays red, now at 0.0041 above.

**One upright made into a tilted square.** `--moves grow` changes the two counts. It puts a new tilted square, at the angle of the block, at each free place one step from a tilted square. The upright nearest to that place goes. This is the step the chain above lacks.

**Control, red.** From the kinked 261 the move has 39 places. No quench ends below 16.682926829, the side of the kinked form. 14 layouts end within 0.006 of the held side. In 4 of them the new square stays tilted, and in the others the quench turns it back upright. A layout of the first kind has the counts of the deep form at the side of the kinked form. From one of those layouts, 23 kinks end at 16.682926829 at best. The deep form also has two chains one square further along, and no move here shifts a chain.

The move ran on two held layouts of that family too.

| n | places quenched | best side | held side |
|---|---|---|---|
| 230 | 36 | 15.682926829 | 15.682926830 |
| 451 | 36 | 21.756097561 | 21.756097562 |

None ends below the held side. The move has no green control, so these negatives are weak.

## 11. A soft block is bands of rows turned both ways

This section came in the last hour of the round. The rule, the bands and the long room are measured. The reading of the board's sides at the end is a model with no control yet.

**The side follows from the turn.** Section 9 gives the side of a block whose chains are turned by ε between two teeth. The same rule holds for every soft form we looked at, with b the squares across the tight extent of the block. The turn is measured on the layout, and the rule gives it from the side alone.

| layout | b | f | turn by the rule | turn measured |
|---|---|---|---|---|
| held 297 and 332, 6 × 18 | 6 | 0.740417 | 0.2598° | 0.2598° |
| fresh 297 | 6 | 0.741250 | 0.1612° | 0.1612° |
| held 494, 6 × 25 | 6 | 0.736096 | 0.7969° | 0.7969° |
| fresh 494, two forms | 6 | 0.739488 and 0.737646 | 0.3715° and 0.5989° | 0.3715° and 0.5989° |
| held 328, 3 × 22 | 3 | 0.614369 | 0.8215° | 0.8215° |
| held 365, 3 × 22 | 3 | 0.612856 | 1.0074° | 1.0074° |
| held 199 | 3 | 0.614690 | 0.7824° | 0.7824° |
| held 230 and 451 | 13 and 23 | 0.682927 and 0.756098 | 1.3972° | 1.3972° |

So a lower side on the same block means a deeper turn, and nothing else. The board's sides give these turns: 0.375° on 297, 0.547° on 332 and 409, 1.531° on 494, 2.78° on 328 and 2.88° on 365. On 451 the board's side is under the limit of the rule, so the board holds another block there.

**The block is a stack of rows.** `block_rows` gives the row of every tilted square. The 6 × 18 block of the held 297 is 18 rows of 6 squares, and the rows are not turned the same way. Rows 0 to 4 are turned by +0.26°, rows 6 to 9 by −0.26°, row 11 by +0.26° and rows 12 to 17 by −0.26°. Rows 5 and 10 stay near 45°. We call a run of rows with one sense a *band*. The held 332 and 409 hold the same block with the same bands.

| layout | rows | turn | changes of sense | sum of the changes of turn |
|---|---|---|---|---|
| held 297 | 18 | 0.260° | 3 | 1.56° |
| fresh 297, two forms | 18 | 0.161° | 3 | 1.52° and 1.55° |
| held 494 | 25 | 0.797° | 5 | 7.99° |
| fresh 494, two forms | 25 | 0.372° and 0.599° | 5 | 6.44° and 8.80° |
| held 328 | 22 | 0.822° | 5 | 8.22° |
| held 365 | 22 | 1.007° | 4 | 8.79° |

The fresh 297 and the held 297 have the same sum, 1.5°. The held form spends it on three clean changes. The fresh form spends it on many small ones, so its turn is smaller.

**What turns a row.** `facing` lists the staircase rows whose tooth meets each row of the block. A row is *pinched* when a tooth of each side staircase meets it. Its sense follows which of the two teeth is further along the block. On the held 297 the pinched rows are 1 and 4 (+), 6 and 9 (−), 11 (+), 13 and 16 (−). The other rows take the sense of a neighbour. That gives the bands above and their 3 changes of sense. Row 11 is a band of one row, pinched by row 4 of the top left staircase and row 8 of the bottom right one.

**The long room limits the turn.** Inside a band the rows of the held 297 are 1.0000 apart. At a change of sense they are 1.001 to 1.004 apart. The 18 rows take 0.0167 more than 18, and the room between the two end staircases is 0.0177. So each change of sense costs room along the block, and the room is spent.

**A model for the board's sides.** Take the room as 0.65 times the sum of the changes of turn, as the held 297 has it. With 2 changes of sense the turn is then 0.363° and f is 0.739559. The board holds 0.739456 on 297. With 1 change the turn is 0.604° and f is 0.737605. The board holds 0.738057 on 332 and 409. On 494 the same count gives 0.732729 with 3 changes and 0.729280 with 2, and the board holds 0.730791. So the board seems to hold our blocks with fewer bands. The fit is within 0.0005 of side and has no control.

**The moves that were tried on it.** A change of sense goes away when the band of one row loses its pinch. Four moves went at that.

- `--moves ungrow` makes a tilted corner square of the block into an upright in the wall row next to it. The held 297 differs from the fresh 297 by this step: 107 tilted squares and one more upright in the top row. `--turn F` multiplies every turn by F first.
- `--moves flip` sets 1 to 4 neighbouring rows to one sense.
- `--from` keeps the hops that take the last square of given staircase rows, here the two teeth that pinch row 11.
- `--moves home` takes the last square of a staircase row to a wall row with room for one more upright. It sets the uprights of that wall row at even steps.

| start | move | quenches | result |
|---|---|---|---|
| fresh 297 | reverse grow, as it is | 12 | 12 at the parent side 17.741250448, 0 lower |
| fresh 297 | reverse grow, turn × 1.3, 1.6 and 2.0 | 18 | 18 at the parent side, 0 lower |
| held 297 and 332 | reverse grow, as it is and turn × 1.45 and 2.1 | 18 | 18 at the held side, 0 lower |
| held 494 | reverse grow, one and two squares, turn × 1 to 1.92 | 26 | 26 at the held side, 0 lower |
| fresh 297 | flip of 1 to 4 rows | 123 | 116 at the parent side, 0 lower |
| held 199, 328, 332, 365, 494 | home | 193 | 8 at the held side, 0 lower |

Both controls are red. The reverse grow and the flip should take the fresh 297 to the held 297, and every quench returns the parent. The quench puts the turn back, because the pinched rows have not changed.

The home move has no control. It ran on 5 held layouts, 193 moves. 8 of them end at the held side and none ends below. The nearest other result is 0.000032 above the held side, on 328. On 328 the left wall has room, and the four nearest results got the move a second time: 118 moves, 18.614376892 at best. The held side is 18.614368939.

The single hop ran on the held soft layouts, where it had never run. Its control of section 8 is green on a soft layout.

| n | hops in the list | hops quenched | at the held side | best side | held side |
|---|---|---|---|---|---|
| 297 | 998 | 266 | 14 | 17.740417288 | 17.740417288 |
| 332 | 958 | 171 | 14 | 18.740417288 | 18.740417288 |
| 451 | 1,254 | 58 | 4 | 21.756097561 | 21.756097562 |
| 494 | 1,186 | 495 | 11 | 22.736096175 | 22.736096176 |

The 3 × 22 blocks of 365 and 328 read the same way. On 365 row 13 is a band of one row between two + bands. Row 6 of the top left staircase and row 9 of the bottom right one pinch it. The hops that take a tooth of such a row:

| n | teeth taken | hops | at the held side | next sides above | held side |
|---|---|---|---|---|---|
| 297 | TL 4 and BR 8, of row 11 | 60 | 2 | 17.740602, 17.740929, 17.741250 | 17.740417 |
| 332 | TL 5 and BR 8, of row 11 | 54 | 1 | 18.740486, 18.741280, 18.779956 | 18.740417 |
| 365 | TL 6, of row 13 | 15 | 0 | 19.675657, 19.755880, 19.778389 | 19.612856 |
| 328 | TL 5 and TL 6, of rows 13 and 11 | 41 | 0 | 18.615081, 18.680004, 18.773849 | 18.614369 |

No hop ends below the held side. The hops from the two teeth leave layouts just above it, 0.0001 to 0.0015. They are other sets of pinched rows, and the held one is the best of them. On 332 the nearest one is 0.00007 above the held side. Its row 9 has lost its pinch and has joined the band of row 11, so it still has 3 changes of sense. From that layout, 59 hops that take the teeth of rows 6 and 11 end at 18.740485975 at best. The held side is 18.740417288. The reason they stay above is room for the square that leaves the tooth. Three of the four wall rows of the held 297 are full of uprights, and the fourth holds a corner of the block. The square has no free cell, so the quench puts it back or pushes the block.

## 12. What the next round should run

This is the list of round 17. Round 19 ran it, and section 13 has the results and the new list.

1. **Take the lone band out of the 6 × 18 block.** Start on 332 and 409. The model of section 11 puts the board there at one change of sense, and ours has three. The step is known: row 11 must lose its pinch. The single hop cannot do it, because the square that leaves the tooth has no free cell. The home move gives it a cell in a wall row. On 332 that ends above the held side: 18.740929 from the top left tooth and 18.936471 from the bottom right one. So the next tool gives the square a home inside the block. The square joins the short last row of the block as a tilted square, in the step that takes the tooth. The control is the held 297 from the fresh 297. The prize is 0.00236 of side on 332 and on 409, 0.00096 on 297 and 0.0053 on 494.
2. **The same reading on the 3 × 22 blocks of 328 and 365.** The rule holds there, and the board's turn is 2.8° against our 0.8° and 1.0°. They hold 5 and 4 changes of sense. These two n are worth 0.00082 and 0.00073 of score, more than all the 6-wide n together. The home move came nearest on 328. Two steps end 0.000008 above the held side, and then every wall row is full. List the pinched rows with `facing` first.
3. **Search over which teeth stay.** For this class the staircases matter only through the rows they pinch. A search that retreats a few teeth, homes their squares and quenches is small: the held 297 has 7 pinched rows. `rigidsoft_topo.py` writes such a start from row counts.
4. **A move that shifts one chain.** The held 261 differs from the kinked 261 by one tilted square and by two chains that sit one square further along. No move here shifts a chain. The control is the held 261 from the kinked 261. The board's 451 is under the limit of the rule, so 451 and 540 are no longer targets of it.
5. **The full hop lists on 536 and 584.** They hold 1,308 and 2,076 hops. The run did 438 and 331 of the short lists. The block is rigid there, so set it to a small turn of both signs before the hop.
6. **Nothing more on single rigid blocks.** A square block or a strip has no soft version near it.

## 13. Round 19: the fault move

Round 19 took the steps of section 12 in order. The first step cannot be done as written, and another move in the same place works. `rigidsoft_band.py fault` moves a band of rows of the block one diagonal track. It certified lower layouts of 263, 297, 328, 332, 365, 409, 494 and 907. They are the first results of this lane below a held side.

**The model's control is red.** The model of section 11 says that the side follows from the set of teeth. It had no control, so its control came first: the side of a held layout from its teeth, to 1e-6. Two records fail it.

- The fresh 297 of section 11 has the same staircase rows as the held 297. Its side is 17.741250448, and the held side is 17.740417288. The two layouts differ in one corner site of the block. The held 297 has 107 tilted squares, and an upright of the top row stands in that site.
- `rigidsoft_band.py scan` builds the block with its end sites left out and one loose upright in a wall row. It quenches once per set of row counts. On 297 it ran 96 sets. The set of the held 297 ends at 17.741250448, and the best set ends at 17.741133740.

So the side does not follow from the teeth alone. The fq quench of a rigid block stops at a worse jam of the same row counts. A scan from fresh blocks is a weak negative, and every move of this round starts from a held layout.

**The move of section 12 has no site.** The 6 × 18 block of the held 297 has 108 sites. 107 hold a tilted square, and the last one holds the upright of the top row. Every lattice site of the four staircases is taken too. A tooth that goes back leaves one square with no site, so the short last row cannot take it.

**Where a square does fit.** The tips of the two side staircases alternate along the block, 0.7071 apart, and the rows are 1 apart. A tooth square fits as a seventh tilted square of the row it faces, in the notch that the tooth leaves. It then stands 0.086 + |p − 0.5| past the line of the row ends. p is the place of the tip along the row, from 0 to 1. So a row takes a seventh square only where one tip faces it near its middle.

**The fault move.** A band of rows, k1 to k2 − 1, moves one diagonal track toward one side staircase. A track is 0.7071 across the block. `TL6:12` moves rows 6 to 11 toward the top left staircase.

- Every tooth of that staircase that faces the band goes back one square.
- On the other side, one square fills each notch between two teeth that face the band.
- Two squares are left over. They become the seventh tilted square of row k1 − 1 and of row k2, at the end on the side of the move. Each of these two rows moves 0.15 the other way.

The count stays n. Inside the band the two staircases change places along the block, so every pinch in the band changes its sense. On the held 297, `TL6:12` turns the pinches 1+ 4+ 6− 9− 11+ 13− 16− into 1+ 4+ 6+ 9+ 11− 13− 16−. That is one change of sense, and the held layout has three. The quench then turns rows 0 to 8 by +0.375° and rows 9 to 17 by −0.375°. The held rows are turned by 0.26°.

**Its control is green.** The board holds 17.7394555120 on 297. The move `TL6:12` on the held 297 ends at 17.739455512. The control can fail: the first version of the move filled the wrong notches, left an overlap of 0.87, and ended at 17.97 and at 18.0.


**Results.** Every row starts from the held layout of that n. The quench is `fq` with `alm0`, at the side and 0.003 above it, then one pass with the deep flags.

| n | block | band | held side | new side | lower by | tilted squares | changes of sense | mean turn | score gain | state |
|---|---|---|---|---|---|---|---|---|---|---|
| 263 | 6 × 13 | `BR4:7, then flip r7-7p` | 16.733166009 | 16.728569535 | 0.004596 | 78 to 79 | 2 to 0 | 1.12° to 1.65° | 2.834e-04 | another lane holds a lower one |
| 297 | 6 × 18 | `TL6:12` | 17.740417288 | 17.739455513 | 0.000962 | 107 to 109 | 3 to 1 | 0.23° to 0.37° | 5.581e-05 | in the take |
| 332 | 6 × 18 | `TL6:12` | 18.740417288 | 18.739455559 | 0.000962 | 107 to 109 | 3 to 1 | 0.23° to 0.35° | 5.278e-05 | another lane holds a lower one |
| 409 | 6 × 18 | `TL6:12` | 20.740417289 | 20.739455559 | 0.000962 | 107 to 109 | 3 to 1 | 0.22° to 0.34° | 4.755e-05 | another lane holds a lower one |
| 328 | 3 × 22 | `BR8:14, then a kick scan` | 18.614368939 | 18.612574299 | 0.001795 | 66 to 68 | 5 to 3 | 0.67° to 0.88° | 9.909e-05 | in the take |
| 365 | 3 × 22 | `BR8:14, the kick of the midm lane, then flip r3-10m` | 19.612856389 | 19.608277774 | 0.004579 | 67 to 69 | 4 to 2 | 0.95° to 1.52° | 2.397e-04 | in the take |
| 494 | 6 × 25 | `TL6:12, BR18:21, then flip r19-21m` | 22.736096176 | 22.733430919 | 0.002665 | 150 to 153 | 5 to 1 | 0.67° to 1.11° | 1.199e-04 | in the take |
| 907 | 3 × 39 | `TL3:12` | 30.618366066 | 30.617919301 | 0.000447 | 116 to 118 | 9 to 7 | 0.28° to 0.33° | 1.483e-05 | in the take |

The squares left over add up to two tilted squares per moved band. On 365 the count of changes stays at 4 and the turn still grows, because the moved band is wider than the bands it replaces. 

Other lanes built lower layouts from some of these, and they hold those n. The border lane put a plain border on the new 297 and got the 332. The forensics lane put the held packing of 10 in the free corner of the new 297 and got the 409. The midm lane kicked the new 365 and got 19.608371, which is 0.0021 below it. The kick turned one row to the sense of its neighbours, and the next part does that step by itself. A kick scan of the midm lane's tool on our 328 found 18.612574298 in 57 tries, 0.0000005 lower, and nothing else.

Most bands give nothing. On 328 the whole list has 95 bands, and 8 end below the held side. On 365 it is 1 of 70, on 263 2 of 32, and on 494 1 of the 33 that ran. A band works when both leftover teeth stand near the middle of the row they face: 0.48 and 0.55 for `BR8:14` on 328, 0.47 and 0.53 for `TL6:12` on 297. The bands `TL6:11`, `TL7:11`, `TL7:12` and `TL10:12` on 297 have one tooth at 0.12 or 0.88 and end at 17.80 to 17.95.


**After a fault move the flip works.** In section 11 the flip of a row did nothing. The quench put the turn back, because the pinches had not changed. After a fault move some rows have lost their pinch, and such a row can stand against its neighbours. The midm lane's kick turned one row of the new 365, and the side went from 19.610440 to 19.608371. The senses of the rows went from `+++-------++-+++++++++` to `+++--------+++++++++++`. `rigidsoft_hop.py --moves flip` does that step with no kick. Its start `r10-10m` on our 365 ends at 19.608371152, the side of the midm layout. That is its control, and it is green. The starts `r10-10p` and `r10-11p` end at 19.610446 and 19.610449.

| n | start | flips quenched | lower than the start | best flip | start side | best side | lower by |
|---|---|---|---|---|---|---|---|
| 365 | new 365 of this lane (control) | 5 | 3 | `r10-10m` | 19.610439667 | 19.608371152 | 0.002069 |
| 263 | new 263 | 31 | 5 | `r6-7p` | 16.732995056 | 16.728569535 | 0.004426 |
| 494 | new 494 | 16 | 3 | `r19-21m` | 22.734443443 | 22.733430918 | 0.001013 |
| 494 | new 494 after its flip | 8 | 0 | `r0-3p` | 22.733430918 | 22.733463311 | -0.000032 |
| 297 | new 297 | 36 | 0 | `r0-0p` | 17.739455512 | 17.739455512 | 0.000000 |
| 328 | new 328 | 40 | 0 | `r11-15p` | 18.612574792 | 18.612574791 | 0.000000 |
| 907 | new 907 | 17 | 0 | `r24-26m` | 30.617920026 | 30.617923348 | -0.000003 |
| 365 | 365 of the midm lane | 32 | 1 | `r3-10m` | 19.608371153 | 19.608277773 | 0.000093 |
| 263 | new 263 after its flip, every turn × 1.35 first (control of the turn) | 6 | 2 | `r7-9p` | 16.728569535 | 16.724372709 | 0.004197 |
| 263 | new 263 after its flip | 23 | 11 | `r8-9m` | 16.728569535 | 16.728567868 | 0.000002 |
| 494 | new 494 after its flip, every turn × 1.3 first | 35 | 0 | `r20-22p` | 22.733430918 | 22.733430920 | -0.000000 |
| 365 | our 365 after its flip, every turn × 1.2 first | 29 | 0 | `r0-0p` | 19.608277773 | 19.608277773 | 0.000000 |
| 297 | new 297, every turn × 1.3 first | 17 | 0 | `r7-8p` | 17.739455512 | 17.739455512 | 0.000000 |
| 328 | new 328, every turn × 1.3 first | 37 | 0 | `r1-2p` | 18.612574792 | 18.612574792 | 0.000000 |
| 907 | new 907, every turn × 1.3 first | 27 | 0 | `r18-19m` | 30.617920026 | 30.617923345 | -0.000003 |
| 297 | held 297 | 7 | 0 | `r10-10p` | 17.740417288 | 17.740417288 | 0.000000 |
| 328 | held 328 | 24 | 0 | `r3-3p` | 18.614368939 | 18.614368938 | 0.000000 |
| 365 | held 365 | 12 | 0 | `r3-3p` | 19.612856389 | 19.612856388 | 0.000000 |
| 494 | held 494 | 7 | 0 | `r6-6p` | 22.736096176 | 22.736096175 | 0.000000 |

On the new 263 one row stood against its neighbours. The flip `r7-7p` sets it to their sense, and every row of the block then turns one way. The side is 16.728569535, which is 0.0046 below the held side. The midm lane then kicked that layout to 16.724372710: all 13 rows at 2.6°, where ours has 1.9° and three rows at 0.9°. On the new 494 the flip of rows 19 to 21 takes 0.0010 more. On the 365 of the midm lane the flip `r3-10m` takes 0.00009 more. On the held layouts the flip still does nothing: every start on the held 297, 328, 365 and 494 ends at the held side. So the fault move frees a row from its pinch, and the flip then takes the change of sense out.

**A larger turn first.** The option `--turn F` makes every turn of the block F times larger before the flip. Its control is green: on the flipped 263, `--turn 1.35` and the flip `r7-9p` end at 16.724372709, the side of the midm lane's kick. The rows of the table with a turn show the other runs. With `--turn 1.2` or `1.3` no start on the new 297, 328, 494 and 907 or on our 365 ends lower. The flip also ran on six other results of the fault move, three of 263 and three of 328. None ended under the lowest layout of its n. The best on 263 is 16.728567893, where the midm lane holds 16.724372710. The best on 328 is 18.612630613.

**One change of sense costs one unit of room.** The room along the 6 × 18 block is √2 · (side − 5) − 18. The turn comes from the rule of section 11. Their ratio counts what the layout spends.

| layout | side | turn | room | room / turn |
|---|---|---|---|---|
| fresh 297 | 17.741250448 | 0.161° | 0.018849 | 6.70 |
| held 297 | 17.740417288 | 0.260° | 0.017671 | 3.90 |
| new 297 | 17.739455512 | 0.375° | 0.016311 | 2.49 |
| the board's 332, less 1 | 17.738057207 | 0.547° | 0.014333 | 1.50 |

The held 297 has 3 changes of sense and the new one has 1. The ratio drops by 1.41, which is 2 less 0.59. The 0.59 is the cost of the change of sense that now lies at the edge of the moved band. The rest, 0.90, is the cost of the two end teeth. The contact list of the held 297 shows that chain. It runs from a tooth of the bottom left staircase through column 4 of the block to a tooth of the top right staircase. The board's 332 is one more unit down. So the board's 332 and 409 have no change of sense. From the held pinches, that needs rows 6 to 10 and rows 12 to 17 moved. Those are the band 6:11 and a band that runs to the end of the block.

**A band to the end of the block.** `rigidsoft_band.py end` moves every row from row k to one end of the block one track. It does so with and without a new tilted square beside the band. It then builds the four staircases again with `rigidsoft_step.staircases`, once per tolerance, and quenches a start that has exactly n squares. Its control is the start `asis`: the held tilted squares of 297 with the staircases built again. It ends at 17.740417288 with `alm0` 0.003 above the side, so the control is green. It can fail: `alm0` at the side ends at 17.841497883, and the default flags end at 17.741250448.

On the held 297, 30 moved starts have 297 squares. None ends below the held side, and the best is 0.00092 above. Every band to the far end of the block is 1 or 2 squares short at every tolerance, on 297 and on 332. So this builder finds no layout with no change of sense at these n. The 409 does not read: its free corner holds a packing of 10 squares.

On the held 328 the move ends below the held side twice in 28 starts, at 18.613797171 with rows 0 to 6 moved. The fault move ends lower, at 18.612574792. From the new 328 and the new 365 it finds nothing: 17 and 6 starts, and the best ones are the starts `asis`.

**Second steps.** `teeth` does not read the teeth that face a moved band. So a layout with one moved band offers few bands for a second move: 9 on 297, 332 and 409, and 19 on 328. One second step ends lower, `BR18:21` on the new 494. The others end above the first step.

**Blocks without bands give nothing.** `rigidsoft_bandlist.py` reads every n of a held file and lists the bands that the move accepts, with no quench. It takes the largest group of tilted squares that touch, so one tilted square that stands alone does not stop the reading (263, 540). On the round 17 file it reads a block with two side staircases on 46 n. A band with both leftover teeth near the middle of their rows exists on 66, 150, 263, 297, 328, 332, 365, 409, 451, 494, 540 and 907. The blocks that are 8 wide and the single lines have none: their tips stand 0.29 to 0.34 from the middle.

| n | block | bands quenched | result |
|---|---|---|---|
| 66 | 3 × 8 | 10 | 4 at the held side 8.656854250, 0 lower |
| 150 | 6 × 11 | 25 | 8 at the held side 12.778174594, 0 lower |
| 237 | 2 × 20 | 4 | best 15.967302, held 15.893806 |
| 451 | 6 × 23 | 13, the ones that fit | best 21.763380, held 21.756098 |
| 907 | 3 × 39 | 24, the ones that fit, the ones that fit | 1 lower: `TL3:12` ends at 30.617920026, held 30.618366066 |

The rigid blocks of 66 and 150 come back to the held side, and the deep form of 451 ends above it. The 540 has the form of 451 and did not run. The move pays only on a soft block that already has bands.

**The chain move (step 4 of section 12).** `rigidsoft_chain.py` is new. It takes the square at one end of a line of tilted squares and puts it one step past the other end. The upright nearest to that place goes to the place the square left. So the block keeps its count of squares, and the line sits one square further along. With `--tols` the tool also builds the four staircases again around the new block, and it quenches each start that has the count of n. A second step starts from the six lowest results of the first step in which the block changed.

**Its control is red.** The control asks for the held 261, 16.678779876, from the kinked 261. The held layout has one more tilted square, and two of its chains sit one square further along. Round 17 left four layouts with that square added, at the side of the kinked form, 16.682926829. The move ran two steps from all four of them: 1041 starts. No start ends under 16.682926829. In the first step the best result with a tilted square at a new place is 16.684433188, which is 0.0015 above. In the second step 2 starts end at 16.682926829 again, and none ends lower. The staircase builder gives these layouts one square too few, so `--tols` adds no start there.

**A weaker control is green: the move undoes itself.** On the held 261 the step `cu1l` ends at 16.680751090, with a changed block and the 105 tilted squares kept. From that layout the reverse step `cu1h` ends at the held side, 16.678779876, to 1e-9. So the move and the quench can take one chain across. Every other first step on the held layout ends at the held layout again or 0.06 or more above it.

**On the held 261 it finds nothing lower.** The first step ran 19 starts and the second 209. In 64 of them the staircases were built again. No start ends more than 1e-9 under the held side. The start is rough. On the held 261 the moved square overlaps 1.6 uprights on average. The upright that goes to the hole overlaps a tilted square by more than 0.2 in 9 of 14 moves. On the kinked form these numbers are 1.7 uprights and 27 of 38 moves. Most quenches end 0.06 to 0.22 above the start. On the held 230, the kinked form one size down, the move ran 409 starts in the same way. No start ends more than 1e-9 under the held side 15.682926830, and the lowest result away from that side is 15.683601574. With the named control red, these runs do not show that the 261 and the 230 have no lower form.

**Not run.** `rigidsoft_hop.py --moves notch` is written and has not run: it takes a square to the notch between two teeth.

### What the next round should run

1. **The flip and a kick scan after every fault move.** The quench of the fault move stops short of the best layout. The flip took 0.0044 of side off the new 263 and 0.0010 off the new 494, and a kick took 0.0021 off the new 365. Run `rigidsoft_lone.py` and the flip on every result of the fault move, and a kick scan after it. The best band before the flip need not be the best one after it. The flip with `--turn 1.35` reaches the kicked 263 from our flipped 263. With 1.2 and 1.3 it gave nothing on the other five n, so scan the factor from 1.1 to 2 there.
2. **Make `teeth` read a moved band, then run the fault move as a chain.** A layout with one moved band offers 9 to 19 bands for a second move. The teeth that face the moved band lie on another line, and `teeth` does not read them. One second step still took 0.00039 of side off the 494. The new layouts keep changes of sense: 1 on 297, 3 on 328, 2 on 365, 1 on 494 and 7 on 907. One change of sense costs one unit of room.
3. **The 3 × 22 blocks of 328 and 365 again.** The round took 0.00010 and 0.00013 of score there. The board is 0.00082 and 0.00073 below the round 17 file, so most of the prize is left. Run every first-step band as a second step, and scan `--shift7` and `--eps` on `BR8:14`.
4. **The layout with no change of sense on 332 and 409.** The room count puts the board's 332 one unit under our new 297. A band to the far end is 1 or 2 squares short on 297 and 332 at every tolerance, so the board's layout is in another count class. Build it from row counts with `rigidsoft_topo.py`: one row more or less in the block, and the end staircase that fits it. The prize is 0.0014 of side on each.
5. **The rest of the 907 list.** The 3 × 39 block of 907 has 342 bands, and 51 of them fit. The round quenched 24, and the quench of a band takes minutes there. One ended lower, the third band of the list.
6. **A home for the extra square on the blocks that are 8 wide.** These are 230, 261, 294, 329, 366, 406, 447, 584 and 850. Their tips stand 0.29 to 0.34 from the middle of the rows, so the square does not fit in a notch. A moved band there needs another home for its two squares.
7. **The chain move with a start that fits.** `rigidsoft_chain.py` moves one line of the block, and its control is red. The start overlaps, and no step from the kinked form ends under its side. The best first step that moves a square ends 0.0015 above. Make `rigidsoft_step.staircases` give the kinked ends, so that the tool can build the staircases again around a moved line of the kinked form. It builds that form one square short now. Then run the control again, and only then a search.
8. **Nothing more on rigid blocks.** The fault move brings 66 and 150 back to the held side.

## 14. Round 20: a second band inside a moved band

Round 20 took the list of section 13 and tried three new ways to reach a block with every row turned one way. Two of the new ways have a red control and found nothing. The fault move found more once the reader saw the teeth of a moved band.

**The reader now sees a moved band.** `read_teeth` used one end line for the whole block. A band that the fault move has moved stands one track off that line, so its teeth were not read. Each row now has its own end line. A tooth counts when it stands within 0.25 of the line of its row or of a row next to it. The control is the new 297 of round 19, made by `TL6:12` on the held 297. The fault predicted its pinches as 1+ 4+ 6+ 9+ 11− 13− 16−. The new reader reads exactly that. The old reader read 1+ 4+ 13− 16−. On the held 297, 263, 494 and 907 both readers read the same teeth. The fault control runs again with the new reader: `TL6:12` on the held 297 ends at 17.739455559, the side of the board to 5e-8.

**A second band inside a moved band pays on 907.** The new 907 of round 19 came from `TL3:12` and then `TL13:26`, and it still holds 7 changes of sense. The reader now offers bands inside the moved band. `TL15:24` moves rows 15 to 23 one more track toward the top left, and rows 14 and 24 each take a fourth square. It takes the changes from 7 to 5, and the quench ends at 30.616241287. That is 0.00168 of side under the 907 of round 19, and 7.06e-05 of score under the round 18 file. One fq quench of the certified file takes 1.5e-9 more. It is in the take.

**Two rules pick the bands that pay.** The fault runs of this round quench 319 bands, and 1 of them pays.

- *No extra square inside the band.* An earlier fault leaves rows with a fourth or seventh square. A band that has such a row inside it collides with a staircase when it moves. On the 907 of round 19 the nine other bands that ran all cross row 12 or row 26, and they end 0.016 to 0.23 above. `TL15:24` crosses neither. The option `--clean 1` leaves those bands out.
- *The band must take changes of sense out.* Each band adds two tilted squares, and they cost room. On the new 907 eight clean bands keep 5 changes or add some. They all end 0.027 to 0.040 above it. Their starts overlap no more than the start of `TL15:24` did, 0.30 in sum against 0.32. The option `--reduce 1` keeps only the bands that leave fewer changes. On the 907 of round 19, `--clean 1 --reduce 1 --fit 0.4` lists `TL15:24` among 14 bands, so the filter keeps the band that paid.

On the other layouts few bands pass both rules, and none of them paid:

| layout | bands run | best band | best side | bar side |
|---|---|---|---|---|
| our 365 | 18 (14 in attempt 1, 4 clean) | `BR2:3` | 19.608277773 | 19.608277774 |
| our 328 | 29 | `TL20:21` | 18.612575042 | 18.612574299 |
| our 494 | 14 | `TL8:10`, then a flip | 22.735594309 | 22.733430919 |
| 332 of the border lane | 12 | `TL8:10` | 18.747681679 | 18.739455513 |
| 409 of the forensics lane | 12 | `BR1:8` | 20.778029562 | 20.739455513 |
| 297 | 8 | `BR1:13` | 17.944930867 | 17.739455513 |
| new 907 (after `TL15:24`) | 8 that take changes out | `BR32:38` | 30.617788144 | 30.616241287 |
| 328 of round 19, `BR8:13` (second step) | 19 | `BR1:4` | 18.614012888 | 18.612574299 |
| 328 of round 19, `BR12:13` | 23 | `TL20:21` | 18.613387243 | 18.612574299 |
| 328 of round 19, `BR1:13` | 13 | `BR3:9` | 18.615911252 | 18.612574299 |

**The chains found no second gain.** `ch5.sh` runs the fault move as a chain with two workers per pass. After each pass that goes lower, it runs two things at the same time. One is the flip of the rows that stand alone. The other is a 150 s kick scan of the midm lane: `midm_scan.py` with kick and lkick at sigma 0.02 and 0.04 and `--stop6`. The chain goes on from the lowest of the three.

- The new 907 offers 8 clean bands that take changes out. The best, `BR32:38`, ends at 30.617788144, and the flip of rows 32 to 34 brings it back to 30.616241287, the start. The kick scan on the new 907 stopped after 6 tries with no find.
- On the 907 of round 19 the other 7 clean bands that take changes out end at 30.618519058 at best (`BR14:25`), above the 907 of round 19.
- On the held 365 the new reader offers 13 bands that round 19 never ran, because it now reads the teeth at the end of the block. They end at 19.648693989 at best, against 19.612856389.
- Chain g starts on the held 907 with `--fit 0.3 --clean 1 --reduce 2`. Pass 1 runs 36 bands, and round 19 never ran 29 of them. 5 end under the start. The best is `TL3:12` at 30.617919294. That is the first step of round 19, so the filter keeps the band that paid then. `TL27:36` and `TL13:26` alone end at the same side. Pass 2 runs 14 bands on `TL3:12`, and 6 end under the start. `TL20:26` ends at 30.617318085, and the kick takes it to 30.617318081. Round 19 never took this branch. It is 0.0006 under the 907 of round 19, but 0.00108 above the take.
- After `TL20:26` no clean band takes 2 changes out. Chain h runs the 5 clean bands that take 1 or 2 out, all in rows 31 to 37. They end 0.06 to 0.21 above the start, as the same rows did on the new 907.
- Chain j starts on the held 494 with `--fit 0.4 --clean 1 --reduce 2`. Pass 1 runs 24 bands, and only `TL6:12` ends under the start, at 22.734836449. That is the first step of round 19 again. The flip of rows 7 to 9 and the kick take it to 22.734455808. Pass 2 has 4 bands, and they end 0.006 to 0.07 above. Our 494 of round 19 stays lower, at 22.734443443.
- Chain k does the same from the held 365 and the held 328, with 17 bands each. On both n the best of pass 1 is `BR8:14`, the first step of round 19 again. On 365 it ends at 19.610439666, and the flip of row 10 takes it to 19.608371152. On 328 it ends at 18.612574792. Our layouts of round 19 stay lower, at 19.608277774 and 18.612574299. Pass 2 has no band on either n.

The filter keeps the first step that paid in round 19 on all four n, and it runs fewer bands. Round 19 ran the whole list on 365 and 328: 70 bands on 365 with 1 under the held side, and 95 on 328 with 8. On 494 it ran 33 bands, with 1 under. The filter runs 17 on 365 with 1 under, 17 on 328 with 2, 24 on 494 with 1 and 36 on 907 with 5.

**Two bands at once, red.** `rigidsoft_multi.py` moves two bands on the same layout, with a gap row between them or one shared row on opposite sides. The shared row takes one more square at each end and loses its pinch. Its control asks for the second step of round 19 on the 494, `TL6:12` and then `BR18:21`, which ended at 22.734443443 with a quench between. The two bands at once end at 22.738817772. So the control is red. The pairs that leave no change of sense on the held layouts all end far above:

| n | pairs | best pair | best side | bar side |
|---|---|---|---|---|
| 297 | 12 | `BR1:6+TL10:12` | 17.801993587 | 17.739455513 |
| 332 | 12 | `BR1:6+TL10:12` | 18.801934874 | 18.739455513 |
| 409 | 12 | `BR1:6+TL10:12` | 20.801993530 | 20.739455513 |
| 328 | 8 | `TL3:8+TL10:15` | 18.711052158 | 18.612574299 |
| 365 | 16 | `TL3:8+TL10:15` | 19.711055439 | 19.608277774 |

The starts overlap by 0.8 to 2.6 in sum. The reason is the fit of section 13. On the held 365 a pair needs the bands `TL3:8` and `TL10:15`. Their far leftover teeth stand at 0.17 and 0.20 of the row, not near its middle. A single band that works has an overlap of 0.06 to 0.9 in sum and at most 0.12 at one contact.

**Every row one way at a larger turn, nothing.** The uniform flip sets every row of the block to one sense, with the turn made larger first. Its control is green: on our flipped 263 the starts `r0-9p` to `r0-12p` at `--turn 1.35` end at 16.724372709, the side of the midm lane's 263. On the current 365 the turns 1.0, 1.5, 2.0 and 2.5 all end at 19.608277773, the start. On the current 328 the turns 1.5, 2.0 and 2.5 end at 18.612574298 at best, 1e-9 under the start. The pinches put the turn back, as in section 11.

**The block turned one way with new staircases, red.** Two tools turn every row of the block one way, by the board's turn. That turn is 2.78° on 328 and 2.88° on 365. Then they build the staircases again.

- `rigidsoft_step.py scan --plain` places a pure 3 × 22 block. Its control is the midm lane's 263 at 2.59°, and it ends at 16.865766085 at best, against 16.724372710. That block has a row of 7 and one tilted square outside it, and a pure block cannot hold them. On 328 the scan ends at 18.614952058 at every turn from 2.6° to 2.95°. That is the class of the held 328, with 66 tilted squares.
- `rigidsoft_return.py` is new. It keeps every site of our block, the rows of 4 and of 7 too, and puts them on the lattice of a block turned one way. Its control on the 263 ends at 16.728581300 at best, so it is red. On 328 it ends at 18.665473644 and on 365 at 19.639594584.

The count says why. At a tolerance of 0.1 or less the staircases on their wall lattices hold 5 to 24 squares too few. They reach n only at a tolerance of 0.2 to 0.25, and those starts overlap by 4 to 5 in sum. So the staircases of these soft forms are not on the wall lattices, and this builder cannot make them. That is the red control of the model in section 13 again.

### What the next round should run

1. **A fault move for a band with an extra square inside it.** The bands that would take most changes out cross rows with an extra square. On the new 907 these are rows 12, 14, 24 and 26. On our 328 and 365 they are rows 7 and 14. Every such band failed this round. Say the band moves toward the side where the extra square stands. Then the tooth that faces that row has to go back two squares, and the spare square needs a home. The prize is the rest of the gap to the board: 0.0139 of side on 907, 0.0130 on 328 and 0.0095 on 365. The control is a band of round 19 that paid, run on the layout before it with the extra square of a third fault put inside it. The first target is on 907. After `TL3:12`, the bands `TL20:26` and `TL27:36` each take 0.0006 of side off alone, and both put their spare square into row 26. So the two together need this move.
2. **The filter of this round from the held 297, 332 and 409.** Chains of `--clean 1 --reduce 2` ran this round from the held 907, 494, 365 and 328. They keep every first step that paid in round 19 and run fewer bands: 17 against 70 on 365 and 17 against 95 on 328. On 907 they opened a branch that round 19 never took. The 6 × 18 blocks are the n of the slice where they have not run: 10 bands each.
3. **No more runs of these three.** Two bands at once has a red control, and its pairs end 0.06 to 0.2 above. The uniform flip at a larger turn returns the start on 365 and 328. The block turned one way with new staircases ends 0.002 to 0.05 above, because the staircases of the soft forms are not on the wall lattices.

## 15. Round 21: a band with an extra square inside it

Round 21 took item 1 of section 14 first, because it is the only item with a measured target. Item 2 ran beside it. No layout of this round certifies. The round was cut twice, at 01:20 and at 09:55 UTC. Each attempt went on from the queues and records of the one before.

**The tool.** `rigidsoft_fault2.py` builds the fault move from the overlaps, not from the list of teeth. So a row with a fourth or seventh square inside the band moves with the band.

1. Every tilted square of the band moves one diagonal track toward the side, the extra squares too.
2. The row before the band and the row after it move 0.15 away, and each takes one more tilted square.
3. Every upright on that side that now overlaps a tilted square by more than `--rm` goes.
4. On the other side an upright goes into every notch next to a tooth that faces the band.
5. When the count is short, the spare squares go to the notches of step 4 that overlap least. When it is over, the last uprights of step 4 go again.

**Its control is green.** `TL6:12 --need 0` on the held 297 of round 18 builds the start of `rigidsoft_band.py fault`, square for square, at `--rm` 0.05 to 0.2. It ends at 17.739455558. The plain fault ends at 17.739455559, and the board holds 17.739455512. On the 907 of round 19, `TL15:24` at `--rm 0.2` gives the pinches of the move of round 20. At `--rm` 0.05 and 0.1 the count of 907 is 1 or 2 short, so every run uses 0.2. The exact control with an extra square inside the band cannot be built. `TL15:24` on the held 907 is 2 to 4 squares short at every `--rm`.

**With the default settings every such start falls to a far jam.** The fq sets alm0 and def ran 46 starts on 8 n. All 46 end 0.21 to 0.26 above the bar. On 907 they all end at 30.828427125, and on 297 at 17.949747468. These starts need 1 to 3 spare squares, and the spare squares go into notches that overlap by 0.15 to 0.35. The plain bands that paid had no spare square and an overlap near 0.

**The round set of fq moves these starts.** Seven fq sets ran on the four starts that leave no change of sense. They are alm0, def, stiff3, stiff5, shrink, soft and round, each at the side and 0.01 and 0.03 above. The round set (`--round-r0 0.1 --round-compress`) gives the lowest side every time. The others end at the far jam.

| start | round | above the bar |
|---|---|---|
| 365 `BR4:8` | 19.608500069 | 2.2e-4 |
| 297 `TL12:16` | 17.800772598 | 0.061 |
| 332 `TL1:6` | 18.800461172 | 0.061 |
| 494 `TL1:6` | 22.859308691 | 0.126 |

Then the round and shrink sets ran on every start with an extra square inside the band, 52 bands on 6 n. The shrink set ends at the far jam every time. None ends under the bar:

| n | best band | side | above the bar |
|---|---|---|---|
| 494 | `TL3:6` | 22.737156548 | 3.7e-3 |
| 328 | `TL12:15` | 18.625073951 | 0.0125 |
| 409 | `TL3:6` | 20.756186882 | 0.0167 |
| 365 | `TL11:15` | 19.642016504 | 0.034 |
| 332 | `TL2:6` | 18.776725965 | 0.037 |
| 297 | `BR10:13` | 17.800772598 | 0.061 |

**The corner radius of the round set is a lever.** The round set passes `--round-r0 0.1 --round-compress` to fq. Round 21 added the sets `round05`, `round2`, `round3`, `round4` and `round5` to `rigidsoft.py` (radius 0.05 to 0.5, against 0.1 for `round`). They ran on the best 14 starts with an extra square inside the band. At 0.05 every start falls to the far jam. At 0.4 and 0.5 fq diverges on every start, with sides of 8e3 and more. At 0.2 and 0.3 most starts end 0.008 to 0.06 under the side they reach at 0.1:

| start | round (0.1) | round2 (0.2) | round3 (0.3) | above the bar |
|---|---|---|---|---|
| 409 `TL3:6` | 20.756186882 | 20.741019043 | 20.741019044 | 1.56e-3 |
| 297 `BR10:13` | 17.800772598 | 17.797012277 | 17.741250448 | 1.8e-3 |
| 297 `TL12:16` | 17.800772598 | 17.800772598 | 17.776764096 | 0.037 |
| 332 `TL2:6` | 18.776725965 | 18.800461328 | 18.776710607 | 0.037 |
| 365 `TL7:8` | 19.648187828 | 19.616433712 | 19.627184861 | 8.2e-3 |
| 365 `BR4:8` | 19.608500069 | 19.608519239 | 19.623898167 | 2.2e-4 |
| 494 `TL3:6` | 22.737156548 | 22.737161862 | 22.737157326 | 3.7e-3 |

The 297 at 17.741250448 is the jam of the fresh 297 of section 13. On 907 six bands ran with round and round2, against a bar of 30.616241289. `TL7:13` ends at 30.629291185 with round2, and `TL3:13` drops from 30.797725873 with round to 30.637817835. So the radius takes the 907 starts up to 0.19 down, and they stay 0.013 above. At the end of the round round3 ran on three of these bands. `TL7:13` ends at 30.624368042, 0.0081 above, and `TL26:36` at 30.629458377, 0.0083 lower than with round2.

**On the layouts of radius 0.2 and 0.3, kicks take large steps.** The round3 set also ran on the other starts with an extra square inside the band. 297 `BR12:13` ends at 17.740749251, 332 `TL3:6` at 18.741019020, 328 `TL14:15` at 18.614166279 and 365 `TL7:10` at 19.613021943. Several starts on 297, 332, 409 and 494 end at a side whose fraction is .741250448, the jam of the fresh 297. Then the fault chain (`ch6.sh`) and kick scans (`midm_scan.py` kick and lkick at sigma 0.01, 0.02 and 0.04) ran from the layouts nearest to the bar.

- 409 `TL3:6` (20.741019042). Chain pass 1 takes `BR6:8` to 20.740507573, the flip of rows 7 and 8 to 20.740442814, and its 150 s kick to 20.740197525. A 900 s kick scan finds 20.739849487 at try 10 and nothing lower in 207 more tries. A second chain pass, with bands that leave up to 2 changes, ends at its start. So 409 stops 3.9e-4 of side above the bar.
- 332 `TL3:6` (18.741019020). A 300 s kick scan finds nothing. The chain takes the same steps as on 409, to 18.740292160, 8.4e-4 above the bar. 332 and 409 share the 6 × 18 block. Their start, fault and flip sides have the same fraction to 3e-8, and only the kicks differ.
- 328 `TL14:15` (18.614166279). A 300 s kick scan takes it to 18.612630613 at try 35 (a full kick at sigma 0.02), 1.5e-3 lower and 5.6e-5 above the bar. The fault chain from there has no band under it. Three more scans ran from that end. One ran 900 s of kick and lkick (426 tries), and one ran 600 s with a walk of 2e-6 (345 tries). The third added the larger moves bkick and melt until the deadline (737 tries). None found anything lower.
- 297 `BR12:13` (17.740749251). The chain has no band under it. A 300 s kick scan takes it to 17.740414148, 9.6e-4 above the bar, and the chain from there has no band under it either.

These kick steps are 1e-4 to 1.5e-3 of side. On the near misses of round 20 the kicks of this round end at the held jam, and on 365 `BR4:8` (round, 0.1) they take 1.2e-5 off.

**The round set does not help a plain band.** Its control is the band that paid. `TL6:12` on the held 297 of round 18 ends at 17.740523344 with round, 17.739455560 with shrink and 17.739455559 with alm0. The plain-band near misses of round 20 ran again on the current layouts with round, shrink, soft and stiff3, each at the side and 0.001 above. None ends lower than alm0 did. 328 `TL20:21` ends at 18.612575042, as with alm0. 365 `BR2:3` ends at 19.640203670 (alm0: 19.608277773), and 494 `TL8:10` at 22.737094110 (alm0: 22.735594442). The soft set fails on these starts and gives sides over 1e4.

**The near misses of round 20 are the held jam.** A kick scan (`midm_scan.py`, kick and lkick, 420 s) ran on the two nearest. On 328 `TL20:21` (7.4e-7 above) it ran 151 tries. It found 18.612574298069 on the first try and nothing lower after it, and 20 tries end within 1e-7 of the held 328. On 365 `BR2:3` (9.3e-10 under the held side) it ran 207 tries with no find. Both ends are 9e-10 of side under the held side. That is 5e-11 of score, under the 1e-10 of the rule. A kick scan of 365 `BR4:8` ran 202 tries and took 1.2e-5 of side off, so it stays 2.1e-4 above.

**Moves from the near misses of the round set.** On 365 `BR4:8` every row turns one way except rows 0 and 8. On 494 `TL3:6` rows 0, 1 and 6 stand against the rest. Three moves ran from them, one process at a time.

- The fault chain (`ch6.sh`, the chain of round 20 as one process, alm0, bands that leave at most 1 change). On 365 the 12 bands end 0.05 to 0.24 above the start. On 494 pass 1 takes `BR3:5` to 22.735599444, and the kick takes it to 22.735171437. Pass 2 has 16 bands and ends at 22.736768224 at best. So the chain stops 1.74e-3 above the bar.
- The flip of the lone rows, on the starts themselves. On 365 `r7-7m` ends at 19.608496511, 3.6e-6 under its start. On 494 `r5-7m` ends at 22.737154965.
- Every row one sense at a larger turn (`--from r0 --only 21p,21m`, the whole span). The turn of 365 `BR4:8` is 1.56°, and the board's 365 has 2.88° by the rule of section 11. At 1.0 to 1.6 times the turn the quench ends at the start, and at 1.85 times it ends 0.0036 higher. On the end of the 494 chain (0.92°) the factors 1.0, 1.3 and 1.67 give 22.735034772, 22.734988080 and 22.734980500, still 1.55e-3 above the bar. The pinches put the turn back, as on the held layouts in round 20.

**The measured target of item 1 is dry.** After `TL3:12` on the held 907, `TL20:26` and `TL27:36` each took 0.0006 off. The branch of round 20 holds `TL3:12` and `TL20:26` at 30.617318081. Six bands with an extra square inside them on row 26, and `BR7:13` and `BR9:13`, ran on it with round and alm0. The best ends at 30.618126292, 0.0008 above the branch. So the two bands do not add up through row 26.

**Item 2 is dry.** The chain of `--clean 1 --reduce 2` ran 3 passes from the held 297, 332 and 409 of round 18. On 297 it finds `TL6:12` again, at 17.739455559. On 332 `TL6:12` and the kick end at 18.739455512, the held side of round 19. On 409 `BR11:13` ends at 20.750220096, 0.011 above.

### What the next round should run

1. **Kick the layouts of radius 0.2 and 0.3, long and with walks, then chain them.** On these layouts kicks take steps of 1e-4 to 1.5e-3 of side. That is 1.5e-3 on 328, 6e-4 on 409 in two scans and 3.4e-4 on 297. On the near misses of round 20 they end at the held jam. The ends of this round are 328 at 18.612630613, 409 at 20.739849487, 332 at 18.740292160 and 297 at 17.740414148. The 328 and 409 files are in `take-rigidsoft-r21/near/`, and all four are in `work/boxE-r21/mirror`. The 328 end is a hard minimum for kick, lkick, the walk, bkick and melt (1,508 tries, no find). So it needs another fault step or another start, not more kicks.
2. **Radius 0.2 and 0.3 on more starts with an extra square.** They ran on the current layouts only. The other first steps of round 19 on 328 and 365 (the starts of `fa.sh` in round 20) are new branches. On 907 round2 took six bands 0.03 to 0.19 down, to 0.013 above the bar, and round3 took `TL7:13` to 0.0081 above. The other 907 bands have not run at round3. Then item 1 on each layout that ends within 2e-3.
3. **Closed this round.** The corner radius 0.05, 0.4 and 0.5. The round set on a plain band. Kicks on the near misses of round 20, which are the held jam. The whole-span flip at a larger turn on layouts that turn one way but for 1 or 2 rows. The row-26 bands on the 907 branch of round 20. Item 2 of section 14, the filter chains from the held 297, 332 and 409.

## 16. Round 22

Round 22 certifies no n.
The final take has its header only, with zero gain against round 20 and zero over the other takes.
The [results table](../results/rigidsoft-r22-2026-11-13.tsv) has 120 grouped records and 3,048 starts or kick trials, including controls.
Each fault row counts band starts, and each walk row counts kick trials.
Side differences in that table precede certification.

The round started with longer walks on 409, 332 and 297.
Those rounded layouts had taken large kick steps in round 21.
The 328 minimum had already resisted 1,508 trials, so it needed a new start.

The spare squares had always gone to the least-overlapping notches.
`rigidsoft_fault2.py --spare-rank` now rotates that order and removes duplicate starts.
The default order stays unchanged.
`--minch` lets another sweep cover higher-change bands without repeating the first sweep.
The default-order control matches the old 365 `BR4:8` start at every coordinate.
Its round quench ends at 19.608500069072416, against the expected 19.608500069.
The 297 plain-band control ends at 17.739455558, as in round 21.

The new notch order takes 907 to 30.621785877.
Two runs reproduced it.
Most other target bands have only one feasible set of spare homes.
Raising the overlap limit from 0.35 to 0.6 added no homes on those bands.
The twelve alternate first-step donors ran at radii 0.2 and 0.3.
There were 32 bands with at most two changes, 42 with more changes, and 73 distinct alternate-home starts.
None crossed the bar.

The higher-change sweep gave a fresh 328 at 18.613822756.
Its 219-trial walk took 0.000817448 off the side, ending at 18.613005307849.
The next fault chain ran 28 bands and found no lower end.
That new branch remains above the 328 minimum of round 21.
The 409 walk ran 223 trials with no find.
A shifted start later reached 20.740204227 through a walk and a chain, also above the round 21 minimum.

The first 297 walk ran 382 trials and reached 17.739685832898.
The second ran 426 trials and reached 17.739478137963.
Together they took 0.000936010 off the start, but stopped 2.2625e-5 above the bar.
Both following fault passes ran 33 bands and found no lower end.

Eleven new corner radii were sampled from 0.305 to 0.36.
Radius 0.32 on 907 `TL7:13` ends at 30.618797179.
Radius 0.31 on `TL26:32` ends at 30.618679502, 0.002438 above the bar.
The finer grid and the thirteen remaining bands found no lower end.
A 43-trial walk then reached 30.618343162382.
Its six clean, reducing plain faults ended far above it with alm0.
Those six faults ran again at radii 0.31 and 0.32, after a green plain-fault control at 17.739455562.
Their best side was 30.629370275.
This changes the radius and the input from the failed plain-band experiment of round 21, but still gives no take.

The border builder is imported from [border_sweep.py](../border_sweep.py).
Its control adds one border to held 297 and reaches 332 at 18.739455512067.
That matches the held form, so the control is green.
Four corners from each new 297 source give eight more starts.
They keep the donor's fraction: 0.739478 or 0.739686.
The closer 332 then ran 205 kick trials with no find.
Its clean, reducing fault list was empty.

New k123, invent and soft layouts of 494 also ran through the block reader.
One extra-inside start reached 22.735387067 and its walk reached 22.735355357.
Later inputs were already lower than that.
The last radius experiment used the soft 494 at 22.731336727 and reproduced its control before three new band starts.
None beat the live take.
The collector therefore uses frozen round 21 and live round 22 scores for follow-up cuts.
The measurement table keeps round 20 as its reference.

`--resume 1` skips recorded tags when their expected raw files exist.
A fresh-table control runs once at 17.739455558, and the repeated call runs zero trials.
A file-state control checks that missing expected files and partial records are run again.
Resume requires the same input, options and keep threshold.
Equal sides alone do not prove a clone.
The new 365 kick and the round 21 kick both ended at 19.608487868474, but their full geometry comparison failed.
Its remaining eighteen fault bands ran and found no lower end.

The final screen read 203 raw files against the round 20 score floor and all frozen and live peer scores.
None was eligible.
Floatsafe rejected the apparent numerical gains on 449 and the 332 border control.
The collector handed off each new near design instead of keeping only the best near per n.
It classified or ran 33 incoming layout versions.
One 539 intake stopped with its nine plain bands complete and five extra-inside rows recorded.
Its input and resume records are in the archive.

All search jobs ended by 15:15:36 UTC.
The final archive has 1,029 payload files, 17,115,570 bytes, verified by SHA-256 before boxE scratch was removed.
The shared boxE base was left in place.
No process of this lane remains.

### Next

1. Build a held-side control for an extra-inside fault.
   Try undoing the middle `TL13:26` on held 907 after its later `TL15:24`, then require fault2 to put it back.
   The current controls reproduce plain faults or rounded layouts above the bar.
2. After that control passes, give spare squares homes outside the current notch list.
   Most target bands had only one feasible home set even at overlap 0.6, and all 73 cyclic alternatives stayed above the bar.
3. Resume the partial 539 intake on the newest soft-block designs, using recorded tags and live source scores.
   New 494 layouts lowered the live bar during this round, while old inputs kept returning known fractions.
4. Do not repeat the exact 297, 332, 328, 365 or 409 kick scans.
   The walks made their largest steps early, and later trials stopped at the same minima.
   Require another cell move or a new layout first.

The queue records and controls are in `take-rigidsoft-r22/work/boxE-r22/mirror` on boxA.

## 17. Round 23

Round 23 certifies no n and stops after the required held-side control fails.
The final take has its header only.
Gain is zero against round 21 and against frozen round 22 and live round 23 takes.
The [results table](../results/rigidsoft-r23-2026-11-13.tsv) records five completed quenches and one interrupted precheck.

[rigidsoft_control907.py](../rigidsoft_control907.py) reverses `TL13:26` on held 907 while keeping the later `TL15:24` extras.
The reference faults identify the teeth that moved.
Assignment follows those squares through relaxation.
The inverse moves every current square of rows 13 to 25 back, including the later extras in rows 14 and 24.
It restores eleven teeth and reverses the shifts of rows 12 and 26.
A valid inverse must survive a quench before fault2 can try to restore the held side.
This prevents a raw coordinate cycle from passing the control.

The archived inputs correct the ancestry given in section 14.
`TL3:12` is a separate branch with extra squares in rows 2 and 12.
The held branch has `TL13:26`, followed by `TL15:24`.
Its tilted count grows from 116 to 118 to 120.
The middle layout has extra squares in rows 12 and 26.
Held 907 also has extras in rows 14 and 24.

The first precheck used the separate branch as its inverse reference and was interrupted before a result.
A corrected plain-fault2 precheck ended at 30.616638585570, then 30.616638585377 after polish.
That is 0.000397296 above held.
The actual positive control therefore uses the historical plain fault and its certified round 19 donor.
With alm0 at side plus 0.003 and then polish, it ends at 30.616241287471.
Held 907 is 30.616241288951, so that positive control passes.

The raw inverse retains extras in rows 14 and 24 and removes the original boundary extras.
The maximum reference matching distances are 0.193914720 and 0.119895838.
Its alm0 quench ends at 30.889087297654, 0.272846009 above held.
The reader then reports extra rows 13 through 21, 24 and 25 inside the target band.
The inverse has lost the topology that the recovery test requires.
The control is red, and fault2 recovery was not run on that invalid inverse.
This measures a failed inverse construction, not a limit on every extra-inside move.

The brief requires an immediate stop after a red control.
No spare-home search or repeat of the 297, 332, 328, 365 or 409 scans ran.
The measurements, inputs and command log are in `take-rigidsoft-r23/work/boxE-final` on boxA.
boxE ran one compute process at a time, with a common deadline of 18:30 UTC.

The archive copy completed before boxE scratch removal.
The remote checksum command failed, and cleanup still ran, so remote checksum equality is unverified.
Local checks match the copied script and inputs, the JSON records and logs, and all five measured CSV sides.
boxE scratch is removed, the shared base remains, and no process of this lane remains.

### Next

1. Build an inverse that preserves the later extra rows through its own quench.
   The raw inverse had the requested rows, but its quench changed them and ended 0.272846009 above held.
   Keep the historical positive control at 30.616241287471.
2. After a held-side extra-inside control passes, try spare homes outside the notch list.
   Round 22 found one feasible home set on most target bands, and all 73 cyclic alternatives stayed above the bar.

## Files

| file | what it does |
|---|---|
| `rigidsoft.py` | `blocks`: the 45° blocks of a held n. `gen` and `run`: one quench start per shear or turn of the blocks, also from the held n + 1 with uprights taken out. `kick`: kicks and quenches from the best packing so far. |
| `rigidsoft_scan.py` | `plan` and `run`: every rigid block just above a held side, at every position, exact fill, quench. `shear`: a tight sheared block with a tolerant fill. `deep`: the sheared block with one slide per chain, by a coordinate search on the exact-fill count. |
| `rigidsoft_pin.py` | `pblock`: the block sheared along both diagonals. `shear`: that block with the tolerant fill. |
| `rigidsoft_topo.py` | `one`, `held` and `deep`: a start from the row counts of the four staircases and a uniform or stepped block. |
| `rigidsoft_step.py` | `scan`: the stepped block, or the plain turned block, at every place of a grid. It builds the staircases on their wall lattices and quenches once per set of row counts. |
| `rigidsoft_hop.py` | `run`: one upright moved to another row, the kink move of section 10, the grow move and its reverse, or the flip of section 11, then a quench. `--moves notch` takes a square to the notch between two teeth. It is written and has not run. `block_rows` and `facing`: the rows of a block, their turn and the teeth that meet them. |
| `rigidsoft_band.py` | `fault`: a band of rows moved one diagonal track, with one more tilted square in the row before it and in the row after it. `end`: a band that runs to one end of the block, with the staircases built again. `scan`: a fresh block with end sites left out. `room`: the room of every chain. `teeth` and `pinches`: the teeth of the two side staircases and the rows they pinch; each row has its own end line, so the teeth of a moved band are read (round 20). `fault --clean 1` leaves out a band with an extra square inside it, and `--reduce R` keeps the bands that take R changes of sense out. |
| `rigidsoft_fault2.py` | `dry` and `run`: the fault move built from the overlaps, so a band may hold a row with an extra square (round 21). The spare squares go to the notches that overlap least. `--need 0` also runs the plain bands, its control against `rigidsoft_band.py fault`. |
| `rigidsoft_multi.py` | `list` and `run`: two fault moves at once, with a gap row between them or one shared row on opposite sides. Its control is red. |
| `rigidsoft_return.py` | `dry` and `run`: the sites of a block, extra squares too, on the lattice of a block turned one way, with the four staircases built again. Its control is red. |
| `rigidsoft_bandlist.py` | every n of a held file read as a block with two side staircases, with the bands that the fault move accepts. No quench. |
| `rigidsoft_lone.py` | the rows of a block that stand against their neighbours, as the `--from` list of the flip. |
| `rigidsoft_chain.py` | `run`: one line of tilted squares moved one square along its length, as it is or with the four staircases built again, then a quench. One or two steps. |

`EVAND_PACKER` points at the dir that holds Evan Daniel's `fillfast.py` (MIT, imported, default: the clone on boxA). The records of every run are in `<scratch>/bounties-squares/take-rigidsoft-r17/work/boxE` on boxA, and those of round 19 in `take-rigidsoft-r19/work/boxE`. Round 20 has them in `take-rigidsoft-r20/work/boxE-r20`, with the chain scripts `ch3.sh` to `ch5.sh`. Round 21 has them in `take-rigidsoft-r21/work/boxE-r21/mirror`, with `ch6.sh` (the chain as one process) and the queue scripts `sa.sh` to `su.sh`. The fq sets `round05` to `round5` (the round set at corner radius 0.05 to 0.5) are in `FLAGSETS` of `rigidsoft.py`. The rows of round 19 are in [`results/rigidsoft-r19-2026-11-12.tsv`](../results/rigidsoft-r19-2026-11-12.tsv), those of round 20 in [`results/rigidsoft-r20-2026-11-13.tsv`](../results/rigidsoft-r20-2026-11-13.tsv), and those of round 21 in [`results/rigidsoft-r21-2026-11-13.tsv`](../results/rigidsoft-r21-2026-11-13.tsv).

## Summary

- **Round 21: no certified gain.** `rigidsoft_fault2.py` moves a band that holds a row with an extra square. Its control is green. With the default fq settings all 46 such starts end at a far jam, 0.21 to 0.26 above the bar.
- **The corner radius of the fq round set is the lever.** At 0.2 and 0.3 these starts end within 1e-3 to 2e-3 of the bar. That holds on 297, 328, 332 and 409. At 0.05 they fall to the far jam, and at 0.4 and 0.5 fq diverges. On a plain band the round set ends 0.001 higher than alm0.
- **Kicks take large steps on those layouts.** 328 went 1.5e-3 down in one 300 s scan, to 18.612630613, 5.6e-5 above the bar. 409 stops 3.9e-4 above and 332 8.4e-4 above. On the near misses of round 20 the same scans end at the held jam.
- **Dry this round.** The row-26 bands on the 907 branch of round 20 and the filter chains from the held 297, 332 and 409 found nothing. The whole-span flip at a larger turn found nothing either. The near misses of round 20 are the held jam, so kicks there find nothing.
- **Round 20 certified 907.** It is in the take, 7.06e-05 of score under the round 18 file and 5.57e-05 under round 19. A band inside the band that round 19 moved, `TL15:24`, moved one more track and took 2 changes of sense out.
- **The reader sees a moved band now.** Each row has its own end line. Its control reads the pinches that the fault predicted on the new 297.
- **Two rules pick the bands that pay.** The band holds no row with an extra square, and it takes changes of sense out. Every other band of the round ended above its start. As a filter the two rules keep every first step that paid in round 19 on 907, 494, 365 and 328 with fewer bands than round 19 ran. Their chains found no second gain.
- **Three new ways have red controls and found nothing:** two bands at once, the plain turned block and the block turned one way with its sites kept. The last two show that the staircases of the soft forms are not on the wall lattices.
- **Round 19 certified 8 n.** 297, 328, 365, 494 and 907 are in the take, 0.00053 of score against the round 17 file. The 263, 332 and 409 of this lane certified too, and other lanes hold those n with lower layouts built from ours.
- **The fault move takes a band out.** A band of rows moves one diagonal track. The teeth on one side go back, and squares fill the notches on the other side. The two squares left over become one more tilted square in the row before the band and in the row after it. Its control is green: the held 297 ends at 17.739455512, the side the board holds.
- **The flip works after a fault move.** A row that the fault has freed from its pinch takes the sense of its neighbours and stays there. The 263 went 0.0044 lower that way, and every row of its block now turns one way. On held layouts the flip still does nothing.
- **A band works where both leftover teeth stand near the middle of their rows.** On 328 that is 8 of 95 bands. Rigid blocks (66, 150) come back to the held side.
- **The chain move is new, and its control is red.** `rigidsoft_chain.py` moves one line of tilted squares one square along. From the kinked 261 with one more tilted square it does not reach the held 261. On the held 261 it finds nothing lower, and one step there undoes itself.
- **The control of the model is red.** The fresh 297 and the held 297 have the same teeth, and their sides differ by 0.00083. A scan from fresh blocks ends at the side of the fresh 297. So the moves start from held layouts.
- **One change of sense costs one unit of room.** The ratio of room to turn is 3.90 on the held 297 and 2.49 on the new 297. On the board's 332 it is 1.50. So the board's 332 and 409 have no change of sense. A band to the far end of the block is 1 or 2 squares short on 297 and 332, so that layout is in another count class.
- **Round 17: no certified gain.** Its `take.tsv` has no row. Nothing ended below a held side by more than the 1e-9 rounding of the quench.
- **The idea as put is dead.** A rigid square block or a strip has no soft version near it. 0 of 178 starts on 11 held rigid layouts end below the held side, and 0 of 221 fresh rigid blocks on 110 n. A rectangle softens only when its long extent is the tight one, and the held file already has that form.
- **What fixes a soft form.** The quench never moves an upright to another row. So the row counts of the four staircases and the sign of the block's turn decide where the quench ends. Controls A, B and C rebuild the held 230 and the held 261 from row counts, and control C needs only n and the block shape.
- **The deep form of 261 has a rule** (`f = (√(2b² − 1) − B)/2`, B odd), and almost no target: 451 and 230. The scan found nothing below the held side on either.
- **One upright moved to another row** finds nothing on 261, 536 and 584. The lists of that run were short, so the hop is not closed there.
- **The kink move is new and its control is green.** It moves three squares from one end to the other with the block set to 43.6° or 44.3°. That turns the fq-soft 230 (15.684379) into the held 230 (15.682927). It found nothing below a held side. That holds for the held layouts with a free cell in a wall row, rigid or soft, and for the fresh fq-soft layouts of 297, 332 and 494.
- **The first control stays red, but closer.** Scan, quench and kink take a fresh rigid 8 × 13 block to 16.682927 at n = 261. The held 261 is 0.0041 lower and has one more tilted square. A move that makes an upright into a tilted square gives the count and not the side.
- **A soft block is bands of rows.** Its side follows from its turn. One rule gives the turn from the side on 11 layouts, to 0.0001°. The 6 × 18 block of 297, 332 and 409 has 18 rows in four bands, turned by +0.26° and −0.26°. A row is turned by the two teeth that pinch it.
- **The room along the block limits the turn.** Each change of sense costs room, and the room is spent. A model with that room puts the board's 297 at two changes of sense and its 332 and 409 at one. Ours have three. The fit is within 0.0005 of side and has no control.
- **No move of round 17 takes a band out.** The reverse grow and the flip leave the fresh 297 where it is, so both controls are red. 990 single hops on the held soft layouts end at the held side or above. The nearest new layout is 0.00007 above the held 332. The square that leaves a tooth has no free cell.
- **Next:** the flip and a kick scan on every result of the fault move. Then make `teeth` read a moved band and run fault and flip as a chain. Then the 3 × 22 blocks of 328 and 365 again, where most of the prize is left.
