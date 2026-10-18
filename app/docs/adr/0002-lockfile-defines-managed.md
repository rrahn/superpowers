# 0002: Managed means "recorded in the scope lockfile"; installs are copies

**Status:** accepted

A skill directory carries no trace of how it got there, so `skillctl` keeps a `.skillctl-lock.json`
in each scope directory. An installation is **managed** iff the lockfile has an entry for it.
Everything else (hand copies, symlinks into a local clone) is **unmanaged**; the `installed` view
still shows whether an unmanaged skill's name exists in the catalog and where a symlink points, so
the user can see which ones could be adopted later.

Installs **copy** files rather than symlink: the catalog is a remote branch, there may be no local
clone, and a copy pins exactly what was installed. The lockfile stores the commit and the git tree
hash of the skill directory, which later lets update checks compare against the catalog without
downloading file contents.

Considered: a marker file inside each skill directory. Rejected: it pollutes the skill and Copilot
would expose it to the model as a skill resource.
