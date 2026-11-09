# KrishiAssist: administrator guide

## Become an administrator
Nobody can make themselves an administrator from the website. Do this on the computer that runs the server:

1. Register the account normally on the website.
2. In the `ka\backend` folder (with the virtual environment active) run:
   ```
   python -m app.scripts.make_admin your-email@example.com
   ```
3. Sign out and sign in again. An **Admin** button appears in the top bar.

To remove the rights again, add `--revoke` to the same command. The effect is immediate.

## What the Admin page does
- **Cards and gaps:** how many schemes are verified, how many farmers use the system, and where the data is thin (never verified, verified too long ago, no source link, Hindi text missing, only one eligibility rule, states with no scheme).
- **Switch a scheme off:** set its status to "Switched off" and press **Save**. Farmers stop seeing it everywhere straight away.
- **Mark a scheme verified:** after you have checked a scheme against the official source, press **Verified today** (or pick the date and Save). This lifts the "unverified" cap, so the scheme can show *Eligible* again, and the date is stored with every evaluation as the scheme data version.
  - A scheme with only one eligibility rule needs you to tick a box to confirm you checked the official guideline.
- **Revert to file:** removes your change and goes back to exactly what `schemes.json` says.
- **Check a new scheme:** paste one scheme as JSON to see if it is valid. Nothing is added by this tool; new schemes go into `schemes.json` itself.

## Good to know
- Your decisions are stored in the database (table `scheme_overrides`). `schemes.json` is never rewritten.
- Every admin action is written to the audit trail (`GET /api/admin/audit`), without e-mail addresses or names.
- Changes are held in the server's memory. If you ever run several server processes, restart them after an admin change.
