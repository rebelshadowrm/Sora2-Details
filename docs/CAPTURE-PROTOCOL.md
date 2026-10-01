# Local capture protocol (v1)

This v1 protocol is an **effect-centric scaffold**, not the full [combat-log contract](COMBAT-LOG-PRIORITY.md). It has no standalone action-execution record, generic unknown-result payload, or entry-state snapshot. A future version must add those before an adapter can claim complete command-battle logging; preserve v1 replay compatibility rather than silently redefining existing messages.

The desktop window listens on the local named pipe `sora2-details-capture-v1`. A future game adapter sends newline-delimited UTF-8 JSON. The desktop records messages through `EncounterRecorder` and persists snapshots in `%LOCALAPPDATA%\Sora2 Details\encounters`. The pipe is a transport, not a validated game hook.

The first line on every connection must be a `hello` envelope. A game adapter must supply protocol version `1`, origin `Game`, the exact SHA-256 of the currently supported executable, and its observed field capabilities. The receiver currently supports only executable hash `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`. It rejects unsupported versions before reading encounter data. The future adapter must independently hash the game executable it is attached to; the receiver cannot prove the sender's claim. Normal desktop mode rejects `Fixture` origin. Tests can opt into fixture origin explicitly.

```json
{"type":"hello","message":{"protocolVersion":1,"origin":"Game","executableSha256":"D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF","capabilities":{"sourceIdentity":false,"moveIdentity":false,"effectiveHpChange":true,"damageClass":false,"encounterBoundary":false}}}
```

After the hello, send `start`, `effect`, `gap`, and `end` envelopes. Serialize them with `CaptureMessageCodec`; the shape below is illustrative. Emit `start` only at a **verified command-battle boundary** and exclude preceding field combat. This boundary has not yet been verified in the game. Encounter IDs must be globally unique across app restarts; the recorder rejects an ID already in saved history. Actor IDs must identify **instances** within the encounter, even when two enemies have the same displayed name. Event sequences start at 1 and advance once per resolved target effect. `effectiveAmount` is the HP change counted by default meters; `resolvedAmount` preserves a separately observed displayed or engine-resolved amount when available.

```json
{"type":"start","message":{"encounterId":"fight-123","at":"2026-09-26T19:48:00-05:00","actors":[{"id":"party-agate-1","name":"Agate","team":"Party"}]}}
{"type":"effect","message":{"encounterId":"fight-123","effect":{"sequence":1,"observedAt":"2026-09-26T19:48:30-05:00","actionId":null,"sourceId":null,"targetId":"party-agate-1","moveId":null,"moveName":"Tear Balm","kind":"Healing","effectiveAmount":81,"hpBefore":6601,"hpAfter":6682,"damageClass":"Unknown","resolvedAmount":1500}}}
{"type":"end","message":{"encounterId":"fight-123","at":"2026-09-26T19:49:00-05:00","outcome":"Victory"}}
```

The example's move name and 1,500 amount were **player-reported** during research; the memory watcher only observed 6601 to 6682. It is not a captured game message. Do not emit manually inferred actor, move, amount, or outcome as if read from the game.

If the adapter drops any result, send a `gap` message with that encounter ID and a reason. A connection loss marks open encounters interrupted. Malformed messages and orphan effects stop ingestion rather than silently creating false totals. Exact retransmissions by sequence are deduplicated; conflicting duplicates, sequence gaps, unknown attribution/class, and HP mismatches mark the snapshot partial. See [implementation status](IMPLEMENTATION-STATUS.md) for evidence and remaining hook research.

The research bridge writes optional `moveLookupReason` on each saved effect. It is `null` for a resolved move. An unresolved move records the failed evidence gate, such as `effect-descriptor-missing`, `skill-parameters-mismatch`, `enemy-unit-key-ambiguous`, `enemy-ai-skill-id-absent`, `enemy-ai-skill-name-unlocalized`, or `hp-write-without-attack-result`. These codes describe what the bridge observed; they do not identify the missing move. A `Knockout` derived from a damaging result carries the same reason. Older snapshots without the field remain readable.

The receiver uses an asynchronous named pipe so the app can cancel while waiting for a client, as documented by [Microsoft's `WaitForConnectionAsync` reference](https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.namedpipeserverstream.waitforconnectionasync?view=net-9.0).
