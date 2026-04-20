You are Codex operating on this repository.

Objective:
Implement GitHub Actions workflows for backend CI, frontend CI, integrated smoke, Docker validation, deployments, and nightly validation.

Constraints:
- Do not redesign the application.
- Keep the workflow set simple and maintainable.
- Prefer repo-specific commands already documented in README.
- Use path filters so irrelevant changes do not trigger unnecessary jobs.
- Use GitHub environments for deploy jobs.
- Use concurrency for deploy workflows.
- Keep secrets out of the repo.

Tasks:
1. Inspect the repo for actual dependency files, startup commands, and deployment assumptions.
2. Align workflow commands to the real repo shape.
3. Create or update:
   - `.github/workflows/ci-backend.yml`
   - `.github/workflows/ci-frontend.yml`
   - `.github/workflows/ci-integrated.yml`
   - `.github/workflows/docker-validate.yml`
   - `.github/workflows/deploy.yml`
   - `.github/workflows/nightly.yml`
4. Ensure backend CI runs tests.
5. Ensure frontend CI runs install, type-check, lint, test, and build.
6. Ensure integrated CI starts backend and frontend and runs the smoke script.
7. Ensure Docker validation checks config and build path.
8. Ensure deploy workflow is environment-gated and concurrency-safe.
9. Update README or docs if the exact commands differ from current assumptions.
10. Keep workflow names stable enough to be used in branch protection.

Definition of done:
- workflows validate syntax
- commands match the repo
- workflows are understandable and minimal
- docs explain required secrets/variables and rollout order
