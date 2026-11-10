# Primus Pharmacy website assistant

A WhatsApp-style chat button for primuspharmacy.com. It answers common customer
questions instantly from a fixed list of facts and hands the customer to the
pharmacy's WhatsApp (+234 816 617 7733) with their request already typed.

| File | What it is |
| --- | --- |
| `hostinger-embed.html` | The paste-ready code for Hostinger Website Builder |
| `primus-assistant.js` | The source: your details at the top, then the answers, then the chat window |
| `demo.html` | A preview page. Open it in a browser to try the assistant |

## Install on Hostinger Website Builder

1. Open `hostinger-embed.html` and copy **everything** in it.
2. In the Hostinger builder, open **Website settings → Integrations → Custom code**.
3. Paste the code into the custom code box and save.
4. **Publish / Update** the website. Custom code only runs on the live site, not inside the editor preview.

Do not use the "Embed code" element on a page for this: that element sits in a
fixed box, so the chat button could not float in the corner.

If the site already has a floating WhatsApp button in the bottom-right corner,
either remove it or set `side: 'left'` in the details below so they don't overlap.

## What it answers

| Customer asks about | What the assistant does |
| --- | --- |
| Stock ("do you have…") | Asks for the product name, then opens WhatsApp with the request filled in. It never claims an item is in stock |
| Delivery | Confirms same-day/next-day Lagos delivery and nationwide shipping, then hands off to arrange it |
| Prescriptions | Explains how to send one on WhatsApp |
| Talking to a pharmacist | WhatsApp and call buttons |
| Location | Address plus a Google Maps button |
| Prices, opening hours, payment | Hands off to WhatsApp, because these are not set yet (see below) |
| Health questions (dosage, symptoms, pregnancy, side effects) | Never advises; passes the question to the pharmacist |
| Emergencies (overdose, heavy bleeding, chest pain…) | Tells the customer to go to hospital or call 112 |
| Anything else | Says it is not sure and offers WhatsApp |

## Changing your details

All details are in the `CONFIG` block at the top of `primus-assistant.js`
(and the same block inside `hostinger-embed.html`). Edit the text between the
quotes. Three are empty on purpose; fill them in and the assistant starts
answering those questions itself:

- `hours`, e.g. `'Monday to Saturday 8am to 9pm'`
- `deliveryFee`, e.g. `'Delivery within Lagos starts from ₦2,000'`
- `payment`, e.g. `'We accept bank transfer, POS and cash on pickup'`

After editing `primus-assistant.js`, rebuild the paste-ready file and paste it
into Hostinger again:

```sh
{ echo '<script>'; cat primus-assistant.js; echo '</script>'; } > hostinger-embed.html
```

## Privacy

The assistant runs entirely in the visitor's browser. Nothing a visitor types
is stored or sent anywhere unless they tap a button to continue on WhatsApp.
