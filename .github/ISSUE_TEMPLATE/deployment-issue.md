---
name: "🚀 Deployment Issue"
about: "Report problems with deployments"
title: "[Deployment] "
labels: ["deployment", "ops", "urgent"]
assignees: []
---

## 🎯 Deployment Information

**Platform:**
- [ ] Render
- [ ] Fly.io
- [ ] Railway

**Environment:**
- [ ] Staging
- [ ] Production

**Deployment Method:**
- [ ] Unified script (`./scripts/deploy.sh`)
- [ ] Manual deployment
- [ ] Git push (auto-deploy)
- [ ] Platform CLI

## 🚨 Issue Description

**What happened during deployment:**


**Current Status:**
- [ ] Deployment failed completely
- [ ] Deployment succeeded but app not working
- [ ] Deployment partially succeeded
- [ ] Rollback needed

## 📋 Deployment Details

**Commit SHA:** 

**Deployment Time:** 

**Command Used:** 
```bash

```

**Configuration Files:**
- [ ] Dockerfile
- [ ] Platform config (render.yaml/fly.toml/railway.json)
- [ ] Environment variables
- [ ] Requirements files

## 🔍 Error Information

<details>
<summary>Deployment Logs</summary>

```
Paste deployment logs here
```

</details>

<details>
<summary>Application Logs</summary>

```
Paste application logs here
```

</details>

## 🏥 Health Check Status

**Health Endpoints:**
- [ ] `/health` - ✅ Working / ❌ Failing
- [ ] `/api/health/live` - ✅ Working / ❌ Failing
- [ ] Database connection - ✅ Working / ❌ Failing
- [ ] External APIs - ✅ Working / ❌ Failing

## 🔧 Troubleshooting Attempted

- [ ] Checked environment variables
- [ ] Verified configuration files
- [ ] Tested Docker build locally
- [ ] Checked platform status
- [ ] Reviewed recent changes

## 🚑 Immediate Actions Needed

**Priority:**
- [ ] Critical (production down)
- [ ] High (staging/features affected)
- [ ] Medium (can wait for business hours)

**Rollback Required:**
- [ ] Yes, rollback immediately
- [ ] No, fix forward
- [ ] Unsure, need investigation

## 🔄 Rollback Information

**Previous Working Version:**

**Rollback Command:**
```bash
./scripts/rollback.sh [platform] --version=[version]
```

## 📞 Contact Information

**On-call Engineer:** 

**Incident Channel:** 

**Stakeholders Notified:** 
- [ ] Product team
- [ ] Management
- [ ] Customer support

## ✅ Resolution Checklist

- [ ] Issue identified and resolved
- [ ] Application health verified
- [ ] Stakeholders notified
- [ ] Post-mortem scheduled (if critical)
- [ ] Prevention measures identified