# AI usage

## Tools I used

I used Claude/Codex/Antigravity throughout this assignment for planning, code generation, tests, documentation, and explanations. Most of the implementation and test code was generated with AI assistance.

## How I used AI

I started by comparing the two assignments and breaking Assignment A into phases. I asked for explanations and commands after each phase so I could follow how the pieces fit together.

For the implementation, I used AI to help write the CLI, CSV normalization, SQLite storage, encryption and HMAC matching, event linking, and report calculations. It also helped generate tests for malformed input, duplicates, late events, overrides, and repeat imports.

The documentation and setup instructions were drafted with AI assistance too.

## My decisions and involvement

I chose Assignment A and kept the scope focused on the required core. I asked to work through one phase at a time.
I worked through questions about phone fingerprints, invalid amounts such as `twelve thousand`, database inspection, report outputs.
The detailed design choices were developed with AI assistance. These include SQLite for local storage, Fernet encryption for customer and event bodies, keyed HMAC for phone matching, and recalculating event links without changing the original ledger.

## Where the AI needed correction

The AI initially got the project running by copying packages from another local environment when downloads failed. That hid a setup gap: the environment had no `pip`, and the full requirements had not been installed through the package installer.

## How I checked the result

The project has 99 passing tests. These cover normalization, merge rules, privacy, event deduplication, late linking, report calculations, and failure recovery.
The five reports are compared against small hand-calculated expected files. Separate process-level tests use generated seeds 42, 7, and 99 to compare sequential and combined imports, repeated runs, and reopening the database. A deliberately failing import checks that the whole drop rolls back and can be retried safely.
Privacy checks cover known test values and sampled generated records, key permissions, wrong-key handling, and database integrity. The clean environment also passed all 99 tests. The assistant ran these checks through its tools as part of the implementation work.