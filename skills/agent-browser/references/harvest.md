# Harvest an API Client

Driving a browser fits the first visit, not the hundredth. Record traffic once, then generate a standalone client that calls the internal API directly.

## Workflow

- Record. Start HAR capture, drive every flow the client needs, each twice with different inputs. URL diffs reveal parameters. Log in before recording so credentials stay out of the capture.
- Identify. Query the HAR with jq for first-party JSON calls. Ignore telemetry, third-party trackers, and static assets.
- Extract. Read request shapes, response schemas, and auth headers from the capture. Export live cookies to a file. Never hardcode cookie values into source.
- Generate. One function per flow, typed from observed bodies. Auth loads from file or environment with a clear re-login error. Reproduce required headers. Keep pagination, sort, and filter options.
- Verify. Call every endpoint live and compare shapes. 401 means re-login. CSRF failures mean fetch the token first or keep that flow in the browser. Signed params that rot mean browser fallback for that step.

## Commands

```bash
agent-browser network har start
agent-browser network har stop /tmp/site.har
agent-browser network requests --filter api
jq -r '.log.entries[] | select(.response.content.mimeType | test("json")) | "\(.request.method) \(.response.status) \(.request.url)"' /tmp/site.har
```

## Caveats

Internal APIs change without notice. Keep the HAR for re-derivation. Respect terms and rate limits. HAR files hold live credentials, so keep them out of version control and delete them when done.
