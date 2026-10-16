# What fooled me, and the checks that survived

Every item here is something that looked right. That is the pattern worth internalising: with AI on drawings, the dangerous output is not an error. It is a believable substitute.

## Reading a quantity back proves nothing about location

After placing a markup you can ask the tool for the computed length. It feels like verification. It is circular — it proves the tool measured the path you gave it, and says nothing about whether that path lies on the right feature.

Thirteen area polygons once passed every numeric check available: areas reconciled against each other, no mutual overlap, clean geometry, parts summing to the whole. They were tracing curb-return arcs, callout leader lines and a gas line instead of pavement. All thirteen were deleted.

On the same set, corridor bands passed those same checks while running up to 1.8 m inside the pavement edge — a 16 to 21% error on three area items. Two shoulder polylines came back 2.2 and 2.6 times too long.

**Every numeric check in that list is a check of validity, not of location.**

### The check that survived

Independent evidence has to be a *different kind* of evidence. Three are accepted:

1. A dimension printed on the drawing.
2. The drawing's own vector geometry.
3. A rendered image of the markup in place, which a person looks at.

Every markup gets rendered and looked at before it is reported as done. One question: does the boundary sit on the feature the drawing draws? It costs seconds and it is the cheapest check in the method.

## Two methods agreeing is not validation if they share a flaw

An area traced from a colour mask on the rendered sheet was cross-checked against a second raster trace. They matched to 0.03%. Both were wrong in the same way, because both were looking at the same pixels.

Two witnesses who read the same wrong report are one witness.

This applies with no AI involved at all. A takeoff checked by re-measuring the same way has not been checked. It has been repeated.

## The error message lied, twice

Five working sessions once went into what looked like a broken connector. Reads worked. Every write failed with the same bare, generic error.

The cause was the shape of the request payload, not the connector. **Reads succeeding while writes fail is evidence the connector is healthy** — on a genuine connector fault, reads fail too.

It recurred later: a connector update changed the accepted payload shape, and notes that said "this is the only form that works" were now wrong. Same bare error, same wasted first guess. The application log settled it in a minute by showing the write never reached the host at all.

### The checks that survived

- A bare generic write error means the payload, until proven otherwise.
- Reads working is evidence *for* connector health, not against it.
- Check the host application's own log for whether the call arrived before theorising about anything else.
- Notes about a connector age in weeks. That is a reason to keep them in a repository with a date on them, not in your head.

## Reconcile against what the sheet claims

Where a drawing carries a schedule of run lengths, every measured run is compared with it. Most agree within a metre.

When one does not, the agent does not pick a winner. It flags `CHECK`, shows both numbers, and the difference becomes a question for a person — and sometimes for the designer, because occasionally the drawing is the one that is wrong.

The synthetic sheet in `examples/` has one such disagreement built in on purpose.

## Measure twice, differently

Re-measuring already-completed segments with the same method gave differences from -0.06 to +0.03 m against the earlier values.

That says the method is **stable**. It does not say it is **right**. Stability and correctness are different claims, and conflating them is how the thirteen polygons survived as long as they did.

## Separate the roles

Drawing work, spreadsheet work and review run as separate agent sessions that audit each other.

One caught the other counting vertical risers at poles as trench length — a measurement-rule disagreement, not an arithmetic error. Neither would have caught it alone.
