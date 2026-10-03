# Explicit cure contrast, October 2, 2026

Expiration and bulk clearing are observed. Curia, La Curia and Sylphen Guard's
exact English descriptors include cure selectors 95/96. Native 95 calls 80730
at DF122 (return DF127); 96 calls at DF202 (return DF207), distinct from expiration
813BE and bulk clearing E6932.

Keep `ConditionRemove`: DBE40, 7FD63, 80730, 80780. Exact EXE SHA-256:
`d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`.
At removal entry, only those two cure callers may supply descriptor R14 and
source effect context RSI. Require R13+598=manager, capture full B0 descriptor
and source first-pointer status 2A0. Target status comes through manager[0],
context+1D90 and linked object's first pointer. Reconciliation rechecks caller
and manager before propagating identities. Expiration/clear callers do not
borrow these register meanings. Unknown identities remain representable.

Paired complete arrays with successful AL and unchanged bytes except disabled
+4, or an active record erased under removal flag R8B=1, gain `Dispelled`
candidates on DF127/DF207. Failed calls, sequence gaps, conflicting frames,
incomplete arrays or an unproven removal do not gain a successful cure label.
The live Pommify/Curia positive and no-debuff contrast are complete; see
[the result](CONDITION-CURE-LIVE-RESULT-20261002.md). Existing old sources
cannot reconstruct the additional identity bytes.

Player chooses fight and available cure. Minimum: allow an ally to acquire a
visible debuff (Poison is sufficient), cast Curia/La Curia/Sylphen Guard on that
ally while active, report caster/spell/target/debuff and disappearance, then
finish normally. No Forte, expiration, crit or interrupt repetition is needed.

Verify armed marker, bridge and actual viewer source proof before controls.
No duration/hit cutoff. Finished report authorizes sentinel stop after inspection
and separate detach/helper/viewer/game-survival checks. Continue offline without
milestone confirmation. Profile has no primary-action/resource/boundary slots.
