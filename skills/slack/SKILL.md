---
name: slack
description: Slack workspace operations through Slack's hosted MCP server - read, search, and post messages, and manage canvases, lists, and files as the user. Use when the user mentions Slack, a channel, a DM, a thread, a canvas, or a slack.com URL. Avoid for email, Trello, or Zendesk.
metadata:
  agents: ["claude", "codex", "opencode", "pi"]
---

# Slack Skill

You are a **workspace operator** for the user's Slack. You read, search, and post as the user through the Slack MCP server.

## Operations

The server owns the tool list, so it changes without this skill. Use the `slack_*` tools the Slack MCP server exposes, and read a tool's description before its first call.

<!-- fleet:only pi -->
In pi codemode, list them with `describeNamespace("mcp__slack")`, read one with `describeTool("mcp__slack__<tool>")`, and call it as `tools.mcp__slack__<tool>`.
<!-- fleet:end -->

## Resolving Targets

Resolve people and channels with the search tools at call time. Never hardcode IDs.

A slack.com link carries the channel and the message: `https://<team>.slack.com/archives/<channel_id>/p<digits>`. The message timestamp is the digits with a `.` before the last six, so `p1730000000123456` becomes `1730000000.123456`. A `thread_ts` query parameter is the thread's parent message.

## File Upload

Upload takes three calls. The tool descriptions cover each step.

1. Call `slack_get_file_upload_url` with `content_length` set to the exact byte count.
2. POST the raw bytes to the returned URL with `curl`. Require HTTP 2xx.
3. Call `slack_complete_file_upload`.

The upload is done only when `slack_read_file` returns the local bytes. No tool deletes a file, so a wrong upload must be removed in Slack by hand.

## Operational Rules

| Rule         | Detail                                                                                                                                                           |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity     | Every call acts as the user. The server accepts user tokens only, so there is no bot path                                                                        |
| Large output | Search and history return large formatted text. Pass `response_format: "concise"`, and narrow with `limit`, `oldest`, `latest`, and `cursor`                     |
| Timezone     | The user is in IST. Slack timestamps are UTC epoch seconds                                                                                                       |
| Voice        | Lowercase, casual, terse, no em dashes. One message with line breaks, not several. `(via <your agent name>)` only when the recipient should know it is the agent |

## Error Handling

<!-- fleet:only pi -->
In pi codemode, MCP calls resolve even when they fail. Check `result.isError` before reading `content` or `structuredContent`.
<!-- fleet:end -->

| Error                              | Meaning                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------------ |
| `invalid_token_type` (401)         | The configured token is not a user token (`xoxp`). The server rejects bot tokens     |
| Tool not found                     | Slack changed its tool list. Reconnect the Slack MCP server and list its tools again |
| Upload succeeded, readback differs | The bytes never reached Slack. Remove the shared file in Slack, then upload again    |
