# Operator Digest — 2026-10-03 (cleanup session)
- The Sunday paper-trading shadow jobs are now switched on on the server. Nothing was restarted and the live MLB job was not touched.
- Your Mac's working folder is caught up with the latest code; everything I moved aside is backed up with checksums.
- The held change (PR #157) is NOT merged: merging restarts the live bot, and games were on all evening. Earliest safe time is about 03:30 UTC.
- Found why the live bot kept restarting by itself: every code upload restarts it. That is now a logged gap; changing it is your call.
- Dashboard works and goes blank when the connection drops. One panel shows a 58-day-old reading next to live data, now logged.
- Still zero real money at risk.
