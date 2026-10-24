# Muse Android — Security review (preliminary)

Date: 2026-10-20. Scope: source inspection of the user's fork, **not** a complete audit of the installed APK. No dynamic testing, dependency scanning, build, or APK signature comparison completed.

## Confirmed observations

1. **Broad Android permissions** — `app/src/main/AndroidManifest.xml` declares SEND_SMS, READ_CONTACTS, RECORD_AUDIO, CAMERA, READ_MEDIA_IMAGES, REQUEST_INSTALL_PACKAGES, WRITE_SETTINGS, notification listener, and other sensitive capabilities. Presence of a permission does not prove misuse. Avoid granting optional high-privilege access until relevant execution paths are reviewed.
2. **Tasker broadcast entry point** — `TaskerTriggerReceiver` is exported without a sender permission. `TaskerTriggerGuard` defaults disabled, caps prompts at 4,000 characters, and enforces a **5-second in-process throttle** when enabled. Five seconds is not a billing quota, and the throttle resets on process restart. Investigate a permission-protected integration or explicit pairing/token and a durable, restrictive rate/budget limit; verify tool access is actually disabled for this route.
3. **Virtual-display binder receiver** — exported broadcast receiver accepts a binder only when its handoff token matches the registry expectation. The token's generation, secrecy, lifecycle, and origin authentication require review.
4. **Network configuration** — `network_security_config.xml` disables cleartext traffic by default except localhost and 127.0.0.1. This does not establish whether API credentials or user content are safely handled by all endpoints.
5. **FileProvider** — non-exported with grantUriPermissions, but `file_paths.xml` exposes broad app files and cache trees to individually granted URIs. Review all URI grant call sites and restrict paths where feasible.
6. **Portuguese UI** — `res/xml/locales_config.xml` declares pt-rBR and `res/values-pt-rBR/strings.xml` exists. Translation quality is uneven (e.g., SOCKS5 translated as MEIAS5, Host as Hospedar). The installed APK's actual locales are not yet verified against this fork.

## Prioritized next checks

- Trace API key storage, logging, network clients, TLS verification and exported data interfaces.
- Review Tasker guard, virtual-display token origin and all exported components under adversarial intents.
- Review plugin installation/execution, shell/Termux/Shizuku/root commands, accessibility gating and approval bypasses.
- Check third-party dependencies against known advisories and build reproducibility.
- Analyze the provided APK offline: manifest, signatures, resources, network endpoints, and compare against source-built output.
- Add tests for security guards, and validate pt-BR translations, placeholders, and language selection.

## Current verdict

**NOT CLEARED FOR PRIVILEGED USE.** No malware finding has been established, but the scope reviewed cannot establish safety. Do not grant root, Shizuku, accessibility, SMS, or notification access until the corresponding controls have been tested. Never store production API keys in source control.
