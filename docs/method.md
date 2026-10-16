# The method

Six steps. The first two are refusals as much as actions.

## 1. Fix the basis

Record the exact file, its revision, and the **page label** — not just the page index. A measurement is only as trustworthy as the identity of the sheet under it, and "page 3" stops meaning anything the moment an addendum reorders a set.

If a set has a revision history, confirm which revision is authoritative before measuring. Do not silently measure off a superseded sheet.

## 2. Verify scale at the spot

Do this before every new measurement, not once per file. A single sheet often carries a plan at one scale and a profile at another, and a detail at a third.

- Ask the tool for page information. If a page-level scale is populated, record that.
- If it is blank, do not conclude there is no scale. A calibrated local space may still cover the target. Attempt the measurement and see.
- If the attempt fails for want of a scale, stop. A person calibrates it, then the agent retries.

Never assume or fabricate a scale. This is a stop condition, not a guess-and-flag situation.

## 3. Read geometry and text from the file

The drawing's own vector content is the source of geometry. Stations, callouts and schedules are text at known positions. Both come out of the PDF directly; see `tools/build_synthetic_sheet.py` for the shape of the data on a sheet whose geometry is known by construction.

Two things are worth extracting before anything is placed:

- **The alignment**, as an ordered list of points, so offsets and station-to-station segments can be computed rather than eyeballed.
- **What the sheet claims**, such as a schedule of run lengths. This becomes the independent check in step 6.

## 4. Place native markups

Native means the tool computes the quantity, not the model. Lengths as polylines, areas as polygons, structures and fittings as point markups.

Connector specifics — payload shape, which intents produce a live measurement, what cannot be created at all — are in `mcp-notes.md`.

## 5. Tag everything, immediately

An untagged markup is a coloured line. Apply the naming pattern and write the register row in the same breath as creating the markup, not in a cleanup pass later. See `traceability-contract.md`.

## 6. Read back, look, reconcile, roll up

In that order, and the second step is the one people skip.

- **Read back** the computed quantities from the tool.
- **Look** at each markup rendered in place. One question: does the boundary sit on the feature the drawing draws?
- **Reconcile** every measured run against what the sheet prints. Agreement within a metre is normal. A larger difference is flagged `CHECK`, with both numbers shown. The agent does not choose between them.
- **Roll up** into the takeoff table, excluding anything labelled `DO NOT SUM`.

Why the order matters is in `failure-modes.md`: reading a quantity back is circular, and numeric checks prove validity, never location.

## What stays with a person

- Calibrating a scale where none exists.
- Count-style measurements, where the connector cannot create a live count.
- Ambiguity the drawing does not resolve. A fitting with no material label stays an open question in the register; it does not become a guess.
- Every approval.
