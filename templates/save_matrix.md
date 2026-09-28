# Save Matrix

Adapt scenario names to the real project. Keep equivalent coverage.

| Scenario | Expected run state | Expected meta state | Result |
|---|---|---|---|
| Settings/navigation round trip | preserved | preserved | TBD |
| Stable checkpoint -> reload | restored | preserved | TBD |
| Completion -> home | cleared/archived by contract | preserved/updated | TBD |
| Repeat settlement same runId | no duplicate reward | unchanged after first settlement | TBD |
| Corrupt save | safe fallback | safe fallback | TBD |
| Incompatible schema | migrate or safe reject | migrate or safe reject | TBD |
