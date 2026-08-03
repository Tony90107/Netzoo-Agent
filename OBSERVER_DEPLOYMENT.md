# NetZoo Observer deployment

The Observer is the secure data service behind the browser Dashboard. The Agent
keeps `.netzoo/traces` as its source of truth and uploads in the background; an
Observer outage does not stop a NetZoo task.

## Local Compose startup

1. Copy `.env.example` to `.env` without committing it.
2. Replace every Observer placeholder with a separately generated random value.
3. Run `docker compose up -d observer-db observer-object-store observer-api`.
4. Verify `curl http://127.0.0.1:8000/health` returns `{"status":"ok"}`.
5. Start the `netzoo` service. It reaches the API over the private Compose network.

PostgreSQL and MinIO have no host ports. The API binds only to loopback by
default. For Internet sharing, put it behind an HTTPS reverse proxy and expose
only the API/Dashboard origin. Never expose PostgreSQL or MinIO directly.

## Credential boundaries

- Agent key: creates runs, uploads events and reads acknowledgement only.
- Admin key: creates and revokes viewing links. Do not place it in the Agent service.
- Share token: generated once, placed after `#token=` in the viewing URL, exchanged
  for a Secure/HttpOnly/SameSite=Strict cookie, then removed from browser history.
- Pepper: hashes stored credentials and must be backed up separately from the DB.

Rotate the Agent key by changing it on the API and all Agent instances together.
Rotate the Admin key independently. Rotating the pepper invalidates every share
and session; schedule that operation and issue fresh links afterward.

## Backup and retention

- Back up the `observer-db-data` volume and `observer-object-data` volume together.
- Encrypt backups and test restoring them in an isolated environment.
- Local sealed traces default to the Agent retention policy; cloud deletion is an
  administrative operation and should delete the run, its events, shares, sessions,
  and object-store prefix as one auditable job.
- The first deployment should cap individual attachments at 10 MiB, event batches
  at 100, share links at seven days, and cloud run retention at 90 days. Reassess
  after measuring real class usage rather than raising limits pre-emptively.

## Privacy checklist

- Keep uploads opt-in by configuring `NETZOO_OBSERVER_URL` and the Agent key only
  on machines intended to sync.
- Redaction occurs before the first local write; nevertheless, use `restricted` or
  `local_only` visibility for memory/debug records.
- Shared viewers receive only `shareable` events and attachments.
- Disable proxy request-body/header logging and never put credentials in query
  strings. The bundled API disables access logging and adds no-store, no-referrer,
  CSP, and nosniff headers.
- Revoke a link immediately if it reaches the wrong recipient.

The current milestone supplies the collector and live-event interface. The next
milestone adds the dark orange browser Dashboard for L1/L2/L3 playback, token and
cost charts, search, anomaly markers, and link management.
