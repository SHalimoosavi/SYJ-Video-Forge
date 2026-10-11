# v0.1.0 audit reproductions and fixes

Audit baseline: commit `0bbe185b7c549a2eb098c192e29ca97a7ee0f632`.

## 1. Pages deployment

**Reproduction evidence:** GitHub Actions run `38140327274` failed in `actions/configure-pages@v5` before artifact upload. Its log reports: `Get Pages site failed. Please verify that the repository has Pages enabled and configured to build using GitHub Actions ... Not Found`. This is a repository Pages configuration/API `Not Found` failure, not a static-site build error. The subsequent dynamic Pages build/deployment run `38140433953` completed successfully after the repository's Pages configuration became available; that historical run is not proof that this new workflow has deployed.

**Fix:** `.github/workflows/pages.yml` builds `site/` and uploads only that folder. `scripts/build-site.sh` and `.ps1` copy `index.html`, `styles.css`, and `src/`. Workflow permissions, `github-pages` environment, and `pages` concurrency group are explicit. Maintainer must set Settings → Pages → Source to GitHub Actions; the workflow cannot enable that setting.

## 2. Provider disclosure

**Reproduction from v0.1.0:** `requestDisclosure("custom", "https://example.test")` generated `After submission, prompthttps://example.test and, in image mode, the selected image are sent to https://example.test.` The prompt label was joined directly to the URL. The regression test now asserts exact text for `mock`, `local`, `custom`, and unknown providers.

## 3. Cancellation race

**Reproduction from v0.1.0:** the submit path waited for `submitText/submitImage` before assigning `job`; cancel only called the provider cancellation method when `job` already existed. There was no abort signal or run-token guard, so a late submit/status/result promise could continue mutating the UI after cancel. `RunGate` and `AbortController` now abort in-flight fetches, invalidate late responses, and preserve a known job ID for backend cancellation. A cancellation before the ID arrives cannot send an ID-based cancellation; the server still bounds jobs and cleans them by TTL.

## 4. HTTP provider coverage

**Reproduction from v0.1.0:** `tests/core.test.js` covered core helpers but no injected-fetch HTTP provider cases. The HTTP client also assumed successful responses were JSON and returned generic network errors without CORS/private-network guidance. `tests/providers.test.js` now exercises health, network failure, abort, non-JSON responses, 4xx/5xx, submit text/image, status, result URL, cancellation, and exact disclosures.

## 5. Release metadata

**Reproduction evidence:** GitHub release API metadata for `v0.1.0` showed `prerelease: false`. The repository owner is correcting this manually; this build does not mutate Git history or attempt to edit the published v0.1.0 release. v0.2.0 notes explicitly identify a pre-release.

## 6. Commit identity

The initial commit's author/committer email field was `YOUR_GITHUB_EMAIL`. The repository owner says this is being fixed separately. This build does not rewrite Git history.
