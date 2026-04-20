# Branch Protection Checklist

Apply these settings to `main`.

## Required status checks
- [ ] `backend-tests`
- [ ] `frontend-ci`
- [ ] `integrated-smoke`

## Recommended branch protection settings
- [ ] Require pull request before merging
- [ ] Require approvals
- [ ] Dismiss stale approvals when new commits are pushed
- [ ] Require branches to be up to date before merging
- [ ] Restrict force pushes
- [ ] Restrict deletions

## Deployment controls
- [ ] Use `staging` environment
- [ ] Use `production` environment
- [ ] Require reviewer approval for `production`
- [ ] Set concurrency so only one deploy per environment can run

## Merge policy
- [ ] Block merge if any required workflow fails
- [ ] Do not bypass checks for normal feature branches
