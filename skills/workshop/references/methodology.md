# Workshop Methodology

## The Design Tree

Every plan or decision is a tree. The root is the problem. Each branch is a decision point. Some decisions depend on others: you cannot ask "which queue backend?" until "do we need async processing?" is settled.

The frontier is every decision whose prerequisites are already settled: the questions you can ask now without guessing at answers you have not heard yet.

## Rounds

Work the tree in rounds. Each round:

- Identify the frontier: all decisions whose dependencies are resolved.
- Ask every frontier question in one numbered batch.
- For each question, give your recommended answer with reasoning.
- Wait for the user's answers.
- Recompute the frontier based on what just settled.

A question whose answer depends on another question still open in this round belongs to a later round.

### Round Format

```text
Q1. <Question title>
<Question body. May include context, constraints, options.>

Recommendation: <your recommended answer with reasoning>

---

Q2. <Question title>
<Question body.>

Recommendation: <your recommended answer with reasoning>
```

## Facts vs Decisions

Two kinds of open questions appear on the frontier:

- Facts: "Does the codebase already have a queue implementation?" Look this up yourself. Read files, search code, check configs. Do not put facts to the user.
- Decisions: "Should we use Redis or SQS for the job queue?" Present options, recommend one, wait for the user.

When a fact-finding task is slow (large codebase search, multiple files to read), do it in parallel with asking the decision questions that do not depend on it. Note which questions are waiting on the lookup.

## Completion

The session is done when the frontier is empty: every branch visited, every decision settled or explicitly deferred. Nothing left silently assumed.

Summarize the result as a decisions artifact:

### Decisions Summary Format

```markdown
## Settled

- <Decision>: <What was decided>
- <Decision>: <What was decided>

## Deferred

- <Decision>: <Why it was deferred, what it's waiting on>

## Assumptions

- <Assumption>: <What was assumed without explicit discussion>
```

If the decisions are worth sharing or archiving, offer to publish via postplan.
