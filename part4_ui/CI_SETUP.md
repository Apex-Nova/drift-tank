# CI setup — GitHub Actions (OWNER: Person 4, Phase 1–2)

**Goal:** every Pull Request is checked automatically by GitHub, so broken code
(e.g. a syntax error) can't sneak into `main`.

When you're ready, create the file `.github/workflows/ci.yml` yourself
(it isn't created yet on purpose — an empty workflow file would make GitHub fail).

## Topics to study
1. What CI ("continuous integration") means and why teams use it
2. GitHub Actions basics: workflow, trigger (`on: pull_request`), job, steps, `runs-on`
3. The ready-made actions `actions/checkout` and `actions/setup-python`
4. Running shell commands in a step (`pip install -r requirements.txt`)
5. A cheap first check: `python -m compileall` (finds syntax errors in every file)
6. (Later) running Pygame with no screen: the `SDL_VIDEODRIVER=dummy` environment variable

## Steps
- [ ] Workflow runs on every pull request to `main`
- [ ] Installs Python + requirements
- [ ] Fails if any file has a syntax error
- [ ] (Later) a small test that imports every module
- [ ] On GitHub: Settings → Branches → protect `main` so PRs must pass CI
