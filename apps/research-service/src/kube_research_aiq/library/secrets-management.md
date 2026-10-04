---
title: Secrets and credential management
url: https://kubernetes.io/docs/concepts/configuration/secret/
topics: secrets, credentials, api keys, security, external secrets, encryption, rbac
---
Kubernetes Secrets hold credentials such as model API keys and database URLs and are injected into Pods as environment variables or files. Secret data is only base64 encoded by default, so encryption at rest and tight RBAC on who can read Secrets are needed for real protection.

Credentials should never be committed to Git or baked into images. Charts can reference an existing Secret by name, so the deployment pipeline creates the Secret separately from the application manifests.

The External Secrets Operator synchronises values from managers such as AWS Secrets Manager, HashiCorp Vault or Azure Key Vault into Kubernetes Secrets, and Sealed Secrets lets an encrypted form of a Secret live safely in a GitOps repository. Rotating keys becomes a change in the secret manager rather than a redeploy.
