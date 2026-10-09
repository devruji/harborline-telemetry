# Trial log

Append an entry when an approach fails and a later one works, or when a file does not match the brief. Skip typos and one-off sandbox noise.

```markdown
## YYYY-MM-DD — short title

- Tried:
- Failed because:
- Do instead:
```

## 2026-10-09 — Source A is one object

- Tried: treat `data/source_a_gps_vendor.json` as a JSON array, as the brief describes.
- Failed because: the file is a single object. The rerun file is the same bytes.
- Do instead: accept either one object or an array. Dedup the rerun against the original by payload, not by filename.

## 2026-10-09 — Connected-vehicle keys differ by packet

- Tried: read both packets as `B2B Event List` plus a top-level contained-data list, with `+B Voltage Value` under `CAN`.
- Failed because: `source_b_toyota_0x51.json` nests `Contained data List` under `Engine RPM information`. `source_b_toyota_0x52.json` uses `B2B event` (singular) and has no contained-data list. `+B Voltage Value` is under `WNG`.
- Do instead: branch the parser on those keys. Keep the event snapshot and the signal rows in separate tables.

## 2026-10-09 — GitHub auth looked logged out

- Tried: `gh auth status` inside the default sandbox and treat a keyring failure as a dead token.
- Failed because: the sandbox cannot read the keyring. The same command outside the sandbox showed `devruji` logged in.
- Do instead: rerun `gh` with full permissions before asking for a new login.

## 2026-10-09 — No shared vehicle id in the samples

- Tried: assume a plate or device id joins GPS vendor, connected vehicle, and logistics rows.
- Failed because: the connected-vehicle sample has an empty licence card and no plate. Logistics ids look like `pluto-lake-r`. The GPS vendor id is a Thai plate.
- Do instead: keep query 3 correct, and record in the README when the loaded sample cannot produce a pair.
