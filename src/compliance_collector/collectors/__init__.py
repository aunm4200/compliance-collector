"""Evidence collectors.

Each collector is a small, focused module that fetches one type of evidence
(e.g. Conditional Access policies, MFA registration) and writes it to disk
as JSON. Collectors should be idempotent and never mutate tenant state.
"""
