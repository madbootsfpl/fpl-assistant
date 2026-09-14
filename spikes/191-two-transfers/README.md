# 191 — is one transfer the right answer when you hold two?

Run: `venv/bin/python spikes/191-two-transfers/measure.py [n_squads] [bank] [seed]`

Measures three strategies against the same squad, bank and 5-GW xP map, each scored as the lift to the
**best legal XI**: one move (today's recommendation), two moves taken greedily, and the best pair chosen
together. See `result-2026-09-14.txt`.

⚠️ **Random legal squads understate the value of planning**, because they have so much headroom that
almost any two moves gain a lot and the order barely matters. The two real squads disagree with the random
population on exactly that point, which is why both are in the result file and neither is called the answer.
