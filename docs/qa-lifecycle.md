# QA lifecycle

Every markup carries a status in the register. It moves one way.

```
AI_PROPOSED -> MEASURED -> QA_CHECKED -> ESTIMATOR_REVIEWED -> APPROVED
                                       \-> REJECTED-REWORK -> (AI_PROPOSED | MEASURED)
```

| State | Meaning | Who may set it |
|---|---|---|
| `AI_PROPOSED` | Geometry placed, nothing verified beyond scale | agent or person |
| `MEASURED` | The tool has computed a quantity for it | agent or person |
| `QA_CHECKED` | Rendered and looked at; reconciled against an independent source | agent or person |
| `ESTIMATOR_REVIEWED` | A qualified person has reviewed it | **person only** |
| `APPROVED` | Cleared for use in an estimate | **person only** |
| `REJECTED-REWORK` | Sent back, with a reason in the register | agent or person |

## Why the last two are closed to automation

Not a technical limit — a rule, and the only one in this repository enforced by code rather than by prose.

Research on automation bias is the reason. A systematic review of 74 studies found that people over-rely on automated advice, that inexperience and time pressure make it worse, and that the mitigations which help are showing confidence alongside the output and keeping accountability with the user ([Goddard, Roudsari & Wyatt, JAMIA 2012](https://academic.oup.com/jamia/article/19/1/121/732254)).

An estimating department on bid day has time pressure by design. So the mitigations go into the file: a `CHECK` flag that shows both numbers instead of choosing, a `DO NOT SUM` layer, and an approval an agent cannot reach no matter how the prompt is worded.

## Enforcing it

```bash
python tools/qa_state_transitions.py MEASURED QA_CHECKED --actor automation      # ok
python tools/qa_state_transitions.py QA_CHECKED APPROVED --actor automation      # refused
python tools/qa_state_transitions.py AI_PROPOSED APPROVED --actor human          # refused: skips states
```

A skipped state is refused as well as a forbidden one. `QA_CHECKED` straight to `APPROVED` means nobody reviewed it, and that is exactly the gap this ladder exists to keep visible.
