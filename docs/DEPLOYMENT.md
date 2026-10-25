# Deployment and recovery

This Compose configuration is for local development. Bindings default to loopback. Do not expose it publicly without completing the validation and hardening work below.

1. Set `DEBUG=False`; replace development secrets and disable `AIHMS_ENABLE_DEMO`. Create an operator account with `python manage.py createsuperuser`. Never seed a production database.
2. Put frontend/backend behind an HTTPS reverse proxy. Set public allowed hosts/origins, rebuild frontend proxy/WebSocket addresses, use WSS, and forward the trusted HTTPS scheme header correctly. Restrict direct backend access to that proxy.
3. Use least-privilege runtime database credentials and a separately authorized migration role. Enable database TLS and encrypted database/document/backup volumes. Pin dependency/image versions after validation and scan the resulting artifacts.
4. Ensure Django static assets are collected (startup does this); WhiteNoise serves the Django admin assets. Documents must stay outside static/public roots.
5. Redact Authorization/cookie headers and signed document/WebSocket token query strings in proxy/access logs. Never log medical bodies. Run backend, Celery worker, and one scheduler against shared PostgreSQL/Redis and the same private document storage. Monitor backend readiness, worker ping, stale pending jobs, queue depth, and failed processing.
6. Perform migration, auth, cross-patient, concurrent booking, PDF/vision failure, browser, and restore tests in a staging environment. Review signed clinical record/versioning requirements before real use.

## Backups

Treat database and original documents as one recoverable dataset. Stop application writes briefly for a consistent development backup; do not stop PostgreSQL while dumping it. Keep backups encrypted outside the source repository with restricted access.

```bash
# With application writes paused by the operator:
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > /secure/backup/aihms.dump
# Back up the private_documents volume using your encrypted volume backup mechanism.
```

Restore to an isolated deployment first. Restore the private document volume together with the matching database dump, then restore PostgreSQL using `pg_restore` with the intended owner/schema privileges. Run migrations and validate record/file hashes before restoring access. Retest expiring document links, which intentionally invalidate when signing secrets rotate. Document and periodically exercise point-in-time recovery and recovery-time objectives.

Retention, patient deletion, and correction requests need an approved legal/clinical policy. Account self-deletion is disabled to avoid cascaded clinical data destruction. Do not delete original prescriptions or review/correction history ad hoc. There is no claim of healthcare or DPDP compliance; formal security, privacy, operational, and clinical assessments remain necessary.

The repository has no application license declaration. Assess redistribution/reuse permission before public distribution. This adaptation adds no ownership claim.
