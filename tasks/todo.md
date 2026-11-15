# Primus Pharmacy WhatsApp assistant

Decisions (confirmed with owner): website chat widget, scripted answers,
Hostinger Website Builder, public details from the sample are correct.

- [x] Build self-contained widget (`whatsapp-assistant/primus-assistant.js`)
- [x] Scripted answers with WhatsApp handoff; health questions go to the pharmacist
- [x] Preview page (`demo.html`) and paste-ready Hostinger file (`hostinger-embed.html`)
- [x] Browser tests: desktop and phone, 18 question cases, link targets, Escape, no page overflow
- [x] Install guide (`whatsapp-assistant/README.md`)

- [x] Move to bottom-left (site already has Hostinger's WhatsApp button bottom-right)
- [x] Owner-editable prepared questions (`CONFIG.prepared`), five seeded from the site's own FAQ and delivery text

## Review

- All browser checks passed, both from `demo.html` and with the embed pasted into a page `<head>`.
- Not tested on the live Hostinger site; the owner needs to paste and publish.
- Open items for the owner: opening hours, delivery fee, payment options (empty in `CONFIG`).
