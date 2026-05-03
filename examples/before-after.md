# Brevix Compression Examples

Real before/after samples across the three modes.

---

## Example 1 — React performance question

**Original (verbose):**
> The reason your React component is re-rendering on every parent update is that you are passing an inline object as a prop. In JavaScript, every render creates a new object reference, even if the contents are identical. To fix this, you should wrap the object in `useMemo` so the reference stays stable across renders.

**Lite (~25% saved):**
> Your React component re-renders on every parent update because you're passing an inline object as a prop. Every render creates a new object reference, even if contents are identical. To fix, wrap the object in `useMemo` so the reference stays stable across renders.

**Full (~55% saved):**
> Component re-renders every parent update because passing inline object as prop. Every render creates new object reference, even if contents identical. Fix: wrap object in `useMemo` so reference stays stable.

**Ultra (~75% saved):**
> Inline object prop = new ref each render → re-render. Wrap in `useMemo`.

---

## Example 2 — Database explanation

**Original:**
> Database connection pooling is essentially a technique where the application keeps a set of open database connections ready for reuse, instead of creating a new connection every time a request needs to talk to the database. This avoids the overhead of the TCP handshake and authentication on every request, which can significantly improve latency and throughput under load.

**Full:**
> Database connection pooling is technique where application keeps set of open database connections ready for reuse, instead of creating new connection every time request needs to talk to database. Avoids overhead of TCP handshake and authentication on every request, can improve latency and throughput under load.

**Ultra:**
> Pool reuses open DB connections. No new connection per request → skip TCP handshake + auth → faster latency, more throughput.

---

## Example 3 — Bug diagnosis (Accuracy Guard relevant)

**Original:**
> The bug is in the auth middleware. Specifically, the token expiry check on line 42 uses a strict less-than comparison (`<`) instead of less-than-or-equal (`<=`), which means tokens that expire at exactly the current timestamp are still considered valid for one millisecond. The fix is to change the operator.

**Ultra (risk: meaning loss):**
> Bug → auth middleware. Line 42 token check use `<` not `<=`. Fix: change operator.

**Accuracy Guard verdict:** similarity ~0.88 (passes threshold 0.85). Compression preserves the diagnosis and the fix.

---

## What Brevix never compresses

- Code blocks (`` ```...``` ``)
- Inline code (`` `...` ``)
- URLs
- Quoted error messages and stack traces
- Numeric values, version numbers, and exact identifiers
