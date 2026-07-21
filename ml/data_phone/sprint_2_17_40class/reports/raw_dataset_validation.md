# Sprint 2.17 Raw Phone Dataset Validation

## Status: PASS

- Source JSON files: 1000
- Valid samples: 1000
- Frozen banking labels: 40
- Samples per label: 25
- Sequence shape: 60 x 126
- Exact duplicate sequence groups: 0
- Cross-label duplicate groups: 0
- Raw files repaired or rewritten: 0

## Checks

- [x] json file count
- [x] valid sample count
- [x] label count
- [x] per label count
- [x] repetition coverage
- [x] participant metadata
- [x] unique sample ids
- [x] unique filenames
- [x] no exact duplicate sequences
- [x] no cross label identical content
- [x] pilot counts
- [x] no parse or contract errors
- [x] raw files unchanged during validation
- [x] protected flutter dynamic hash
- [x] protected flutter float32 hash
- [x] protected backup hash

## Protected Hashes

- Flutter dynamic model: `88cdc0367f40e50081e5bde7644ede242937061843cb68ea1235214e62308ddd`
- Flutter float32 model: `36ec44e5ebefd1c7de56161a305324488bfd6cfc58337ca9b2679198f424fac8`
- Dataset backup: `f3f76c6bbe06305c7ae82e2772c5daca7f76619444f7eca892d7aa253986b70b`

The validator is read-only for all phone source JSON files.
