# GitHub Publishing

This repo is ready to publish as `agrovr/kube-research-aiq`.

## Create the repository

Create an empty public repository named `kube-research-aiq` under your GitHub
account. Do not add a README, license, or `.gitignore` from the GitHub UI because
this project already contains those files.

## Push the local repo

From the project root:

```powershell
git remote add origin https://github.com/agrovr/kube-research-aiq.git
git push -u origin main
```

If Git asks you to sign in, authenticate with GitHub in the browser or with a
personal access token through Git Credential Manager.

## GitHub Actions

The CI workflow runs on pull requests and pushes to `main`:

- Python lint and tests
- Helm lint and template rendering
- Dashboard lint and production build
- Docker image builds
- GHCR image push on `main`

After the first successful push to `main`, GitHub Container Registry will publish:

- `ghcr.io/agrovr/kube-research-aiq/research-service:latest`
- `ghcr.io/agrovr/kube-research-aiq/dashboard:latest`
- SHA-pinned tags for each image
