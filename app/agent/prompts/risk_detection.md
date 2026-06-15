risk_detection

Classify the user input into exactly one risk level:

- none: ordinary growth conversation or neutral small talk.
- low: negative emotion without self-harm, suicide, or violence intent.
- medium: strong hopelessness, self-denial, or vague danger expression without an explicit plan.
- high: self-harm, suicide, harm to others, an explicit dangerous plan, preparation, or imminent danger.

Return JSON only:

```json
{
  "risk_level": "none | low | medium | high",
  "risk_reason": "short reason"
}
```

Do not diagnose. If the input includes imminent danger, explicit self-harm, suicide, or harm-to-others intent, classify it as high.
