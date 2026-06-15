<!--
NOTE: This file is a design reference and runtime policy check.
SafetyResponseNode uses a hardcoded reply to avoid LLM dependency on the
high-risk path. This file documents the original safety response intent.
-->

safety_response

Generate or guide a safety reply for high-risk input.

Requirements:

- Express care calmly.
- Encourage contacting local emergency services when there is immediate danger.
- Encourage contacting a trusted nearby person or qualified crisis support service.
- Do not provide medical diagnosis, therapy, crisis intervention claims, or harm instructions.
- Do not continue ordinary growth coaching, pattern discovery, or task generation.
