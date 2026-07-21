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

- Flutter dynamic model: `25efbcef375769f50fa4ad8f46cc18bb816e89982a86225d9e9e7771267c14ad`
- Flutter float32 model: `a819b655b5341223641ed62f7cc36c593d222beebac4156fe7972079ef8602be`
- Dataset backup: `07b5660e08640ea2eac11216e41f4696d01be52627cf3e1dd15d46f99c20286a`

The validator is read-only for all phone source JSON files.
