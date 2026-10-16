# Traceability contract

Every markup gets the same treatment, whether an agent placed it or a person drew it by hand.

## Subject: where identity lives

```
<scope or bid item> | <plan ID> | <short description with stations>
```

Examples from `examples/derived_markups.json`:

```
DUCT     | S-M1   | Duct 8-125 C.E. 0+005.00 - 0+078.40
RESTO    | R-S-M1 | Trench patch 1.9 m 0+005.00 - 0+078.40
CROSSING | OBS-003| 300 STM ABOVE 0+157.00
QA CHECK - DO NOT SUM | Sample A | reinforced extent vs printed START/END REINF.
```

Subject survives. It is readable in the markup list, it sorts, and it is what a reviewer sees first.

## Comment: not a place for structured data

This is the part that has to be learned once and then never forgotten.

**Once a markup becomes a live measurement, the tool may overwrite its comment field with the computed value.** Anything you stored there is gone, silently. In the reference run the comment of every measurement came back as `Duct\r73.40 m` — the tool's own text, not the author's.

So the comment field is the tool's. Structured traceability goes in the register.

## Register: the authoritative record

One row per markup, in a workbook, CSV or JSON kept alongside the drawing. Keyed on the markup's own ID plus page, so a subject rename can never orphan it.

| Column | Purpose |
|---|---|
| `Markup_ID` | The annotation's own ID, returned when it is created |
| `Page` | Page index |
| `PLAN_ID` | Ties the markup back to the takeoff plan row it fulfils |
| `SHEET` | The page **label** |
| `SOURCE` | Which drawing file and revision this was measured from |
| `BIDITEM` | The bid item this quantity feeds |
| `STA` | Station range or a plain-language location |
| `STATUS` | QA lifecycle state — see `qa-lifecycle.md` |
| `SCALE_VERIFIED` | Whether and how scale was confirmed before creating this |
| `CREATED_BY` | `MCP` or `GUI` — record honestly |
| `NOTE` | Free text: why a value looks unusual, what was ambiguous |

`tools/validate_register.py` checks a row string against this contract:

```bash
python tools/validate_register.py "PLAN_ID=S-M1;SHEET=C-101;SOURCE=SYN-U-0002 rev A;BIDITEM=33.01;STA=0+005.00-0+078.40;STATUS=MEASURED;SCALE_VERIFIED=Y (page-level);CREATED_BY=MCP;NOTE=reconciled against printed schedule"
```

## The DO NOT SUM rule

Some markups exist only to check other markups: a trace of a reinforced section against the printed note, a tick at a printed station, a sample line for a reviewer.

In a markup list they look exactly like measurements. Same tool, same length column. Export, sum the column, and QA geometry has silently become quantity.

So they carry `QA CHECK - DO NOT SUM` at the front of the subject, and the roll-up excludes them **by rule, not by memory**. A file gets opened on bid day by someone who was not there when it was made.
