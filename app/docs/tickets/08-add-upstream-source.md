# 08: Add an upstream source

**What to build:** `skillctl sources add` adds a public GitHub upstream source, prompting interactively for missing values (rich prompts) or taking flags; validates that the repo, ref, and path exist before writing the sources file.

**Blocked by:** 07

**Status:** done

- [x] Non-interactive with flags, interactive otherwise
- [x] Validation failure writes nothing
- [x] Existing formatting/comments of the sources file preserved where possible
