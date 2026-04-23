# Fraud Detection – Most Impactful Changes

## 1. Fixed: High-risk device scores now raise the fraud score (+25 points)
**Before:** A device risk score ≥70 subtracted 25 points from the risk score.  
**After:** It adds 25 points.  
**Why it matters:** 7 of the 8 confirmed fraud transactions had a device risk score ≥70. The bug was actively pushing the most suspicious devices toward "low" risk, hiding them from the fraud team entirely.

---

## 2. Fixed: International transactions now raise the fraud score (+15 points)
**Before:** Transactions flagged as international subtracted 15 points.  
**After:** They add 15 points.  
**Why it matters:** Every single confirmed chargeback in the dataset came from an international transaction. The sign error meant cross-border fraud was being rewarded with a lower risk score.

---

## 3. Fixed: High transaction velocity now raises the fraud score (+20 points)
**Before:** Making 6 or more transactions in 24 hours subtracted 20 points.  
**After:** It adds 20 points.  
**Why it matters:** Rapid-fire transactions are a textbook fraud signal — fraudsters move fast before a card is blocked. The bug was treating high velocity as evidence of trustworthiness.

---

## 4. Fixed: Prior chargeback history now raises the fraud score (+20 points)
**Before:** Accounts with 2 or more prior chargebacks had their score reduced by 20 points.  
**After:** Prior chargebacks add to the score (up to +20).  
**Why it matters:** Repeat offenders were being treated as lower risk than first-time customers. This is the most counterintuitive of the four bugs — known bad actors were getting a clean-slate advantage.

---

## Net business impact

| Metric | Before fixes | After fixes |
|---|---|---|
| Confirmed fraud transactions scored "high" | 0 of 8 | 7 of 8 |
| Confirmed fraud transactions scored "low" | 8 of 8 | 0 of 8 |
| Fraud dollars visible in "high" queue | $0 | $4,234.98 |
| "High" bucket chargeback rate | — | 100% |

All four bugs pointed in the same direction — each one independently reduced the score on exactly the transactions that turned out to be fraud. Combined, they were causing the scoring system to produce results that were the opposite of correct.
