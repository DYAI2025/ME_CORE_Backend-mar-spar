---
name: "🚨 CI/CD Bug Report"
about: "Report issues with the CI/CD pipeline"
title: "[CI/CD Bug] "
labels: ["bug", "CI/CD", "infrastructure"]
assignees: []
---

## 🐛 Bug Description

**Clear description of the bug:**


**Which CI/CD component is affected:**
- [ ] Main CI Pipeline (ci.yml)
- [ ] Security Workflow (security.yml)
- [ ] E2E Tests (e2e-tests.yml)
- [ ] Deployment Validation (deployment-validation.yml)
- [ ] Deployment Scripts (deploy.sh/rollback.sh)

## 🔍 Steps to Reproduce

1. 
2. 
3. 
4. 

## 💥 Expected vs Actual Behavior

**Expected:**


**Actual:**


## 📋 Environment Information

**Platform:** 
- [ ] GitHub Actions
- [ ] Render
- [ ] Fly.io
- [ ] Railway
- [ ] Local Development

**Branch:** 

**Commit SHA:** 

**Workflow Run:** (if applicable)

## 📊 Logs and Screenshots

<details>
<summary>Error Logs</summary>

```
Paste relevant logs here
```

</details>

## 🔧 Potential Solution

If you have ideas on how to fix this, please describe them.

## 🚨 Impact Assessment

**Severity:**
- [ ] Critical (blocks all deployments)
- [ ] High (blocks specific deployments)
- [ ] Medium (causes delays)
- [ ] Low (minor inconvenience)

**Affected Users:**
- [ ] All developers
- [ ] Specific team members
- [ ] Production deployments
- [ ] Staging deployments

## ✅ Definition of Done

- [ ] Bug is reproducible
- [ ] Root cause identified
- [ ] Fix implemented and tested
- [ ] Documentation updated (if needed)
- [ ] Prevention measures added