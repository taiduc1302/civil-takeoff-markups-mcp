# Connector notes

Observations from working against Bluebeam's MCP connector. Dated, because connector behaviour changes — see the last section.

## What the connector gives you, and what it doesn't

The vendor's documentation is explicit: the server runs locally, transmits text and metadata, and **non-textual drawing details such as linework and shapes are not transmitted** ([Revu and MCP](https://support.bluebeam.com/revu/resources/revu-mcp.html)). Visual searches return nothing.

That single sentence is the whole design constraint. The agent can create, read and modify markups, set a page scale, and read page information. It cannot see the drawing. The geometry has to come from the PDF's own vector content, read separately — for example with [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/recipes-drawing-and-graphics.html).

MCP itself is an open standard for connecting AI applications to other software ([spec](https://modelcontextprotocol.io/)); the connector is one server among many, and nothing in this method is specific to the protocol.

## Coordinates

PDF space, origin at the lower-left of the page, units of points (72 pt = 1 inch). Paths use a subset of SVG path syntax: `M`, `L`, `C`, `H`, where `H` closes a polygon and is ignored on open shapes.

A warning worth repeating: the `x`, `y`, `width`, `height` properties returned when listing markups are **display** coordinates with a flipped y-axis. They are not interchangeable with the coordinates used to create geometry. Mixing the two produces markups that are plausibly placed and wrong.

## Making a measurement rather than a shape

Creating a `PolyLine` gives you a coloured line. Creating a `PolyLine` **with a measurement intent set in the same call** gives you a live measurement the tool computes and keeps updated.

- Set the intent inside the creation call. Setting it afterwards on an existing markup does not take effect.
- Length and perimeter: `PolyLine` with intent `Perimeter`.
- Area: `Polygon` with intent `Area`.
- Depth or wall area: set as a property on an existing length or area measurement.
- **Counts cannot be created as live count measurements.** A count-style marker placed this way is a static shape. It will not auto-increment or feed a count total. Use the application's own count tool, then read the result back and tag it like any other markup.

There is no `Length` or `Count` markup *type*. Passing one returns an invalid-type error.

## When a write fails with a bare, generic error

In order:

1. **Check the payload shape.** This has been the cause every time so far. As of 2026-09-17 the working form is plain objects:

   ```jsonc
   { "pageNumber": 1,
     "properties": { "type": "PolyLine", "intent": "Perimeter", "subject": "...", "color": "#1A59D9" },
     "shape": { "path": "M 238.35 1024.0 L 654.47 1024.0" } }
   ```

   An earlier connector version accepted only arrays of `{key, value}` pairs and rejected the form above. Both forms fail with the *same* bare error, so if one does not work, try the other before concluding anything.

2. **Check the host application's log** for whether a transaction was even started for your call. No transaction means the request never arrived, which means it is still your payload.

3. **Confirm reads still work.** If they do, the connector is healthy. Reads and writes fail together on a genuine connector fault, so "reads work, writes don't" is evidence *for* the connector, not against it.

4. **Check the markup type is supported** and that any layer you reference already exists — the connector will not create one.

Only after all four is it reasonable to suspect the connector itself. Starting a fresh conversation cannot fix a malformed request, and the appearance that it might has cost several wasted sessions.

## Version note

Everything above was observed against Revu 21 with the MCP connector as of **2026-09-17**. The payload-shape change described in step 1 happened between July and September 2026. Re-test rather than trusting these notes if they are more than a few weeks stale, and open an issue if behaviour has moved.
