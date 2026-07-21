# Formal Offline Held-Out Evaluation

This is the formal recognition evaluation. It uses the locked corrected-v2
prediction artifact with 200 rows, 40 classes, and 5 real
phone samples per class. It is separate from A55 deployment smoke testing.

| Metric | Result |
|---|---:|
| Accuracy | 0.9550 |
| Accuracy 95% Wilson CI | 0.9167 to 0.9761 |
| Macro precision | 0.9625 |
| Macro recall | 0.9550 |
| Macro F1 | 0.9542 |
| Weighted precision | 0.9625 |
| Weighted recall | 0.9550 |
| Weighted F1 | 0.9542 |
| Correct / incorrect | 191 / 9 |

## Per-Class Results

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `deposit` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `withdraw` | 1.0000 | 0.8000 | 0.8889 | 5 |
| `balance` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `transfer` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `account` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `card` | 0.5000 | 0.6000 | 0.5455 | 5 |
| `pin` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `password` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `identity_verification` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `cash` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `payment` | 1.0000 | 0.8000 | 0.8889 | 5 |
| `fee` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `loan` | 1.0000 | 0.6000 | 0.7500 | 5 |
| `savings` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `open_account` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `close_account` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `fraud` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `block_card` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `help` | 1.0000 | 0.6000 | 0.7500 | 5 |
| `confirm` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `statement` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `document` | 1.0000 | 0.8000 | 0.8889 | 5 |
| `bill_payment` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `atm` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `branch` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `cheque` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `interest_rate` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `credit_card` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `debit_card` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `lost_card` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `replace_card` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `change_pin` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `reset_password` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `refund` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `signature` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `complaint` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `appointment` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `account_number` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `card_limit` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `daily_limit` | 1.0000 | 1.0000 | 1.0000 | 5 |
