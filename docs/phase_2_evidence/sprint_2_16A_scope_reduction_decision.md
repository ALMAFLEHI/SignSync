# Sprint 2.16A Scope Reduction Decision

## Decision

The active SignSync banking vocabulary is reduced from 50 to exactly 40 intents before phone recording. The future vocabulary contains 26 alphabet labels, 10 digit labels, and 40 banking intents, for 76 classes total.

## Removed Banking Intents

1. `online_banking`
2. `mobile_banking`
3. `currency_exchange`
4. `exchange_rate`
5. `fixed_deposit`
6. `customer_service`
7. `update_details`
8. `phone_number`
9. `email_address`
10. `address_change`

## Retained Banking Intents

1. `deposit`
2. `withdraw`
3. `balance`
4. `transfer`
5. `account`
6. `card`
7. `pin`
8. `password`
9. `identity_verification`
10. `cash`
11. `payment`
12. `fee`
13. `loan`
14. `savings`
15. `open_account`
16. `close_account`
17. `fraud`
18. `block_card`
19. `help`
20. `confirm`
21. `statement`
22. `document`
23. `bill_payment`
24. `atm`
25. `branch`
26. `cheque`
27. `interest_rate`
28. `credit_card`
29. `debit_card`
30. `lost_card`
31. `replace_card`
32. `change_pin`
33. `reset_password`
34. `refund`
35. `signature`
36. `complaint`
37. `appointment`
38. `account_number`
39. `card_limit`
40. `daily_limit`

## Rationale

- `online_banking` and `mobile_banking` overlap and are lower priority for an in-person banking-service demonstration.
- `currency_exchange` and `exchange_rate` are semantically related and may increase confusion.
- `fixed_deposit` overlaps with retained concepts such as `deposit` and `savings`.
- `customer_service` overlaps with retained `help`.
- `update_details` overlaps with other account-related concepts.
- `phone_number` can be handled using Number Mode.
- `email_address` can be supported through Alphabet Mode.
- `address_change` was weak and confusing during limited live phone testing.

This reduction lowers class confusion and recording workload, supports a more reliable mobile demonstration, and keeps the FYP achievable within the academic timeline. No replacement intents were added.

## Historical Preservation

Old laptop videos, landmark arrays, masks, datasets, label mappings, models, Flutter assets, and Sprint 2.12-2.15 evidence remain physically unchanged. Removed labels are excluded only from the V3 active scope and future training. The current deployed model and its Flutter mapping remain 86-class for reproducibility; the future retrained model will have 76 outputs.

## Investigation Report Note

The Investigation Report currently describes approximately 50-80 banking intents. The final report will be revised later to specify exactly 40 banking intents in the project objective, scope, functionalities, deliverables, evaluation description, and any other affected sections.

The submitted Investigation Report DOCX and PDF were not edited in this task.
