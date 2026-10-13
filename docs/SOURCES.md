# Dataset provenance and permitted use

## REES46 marketplace, October 2019
- Publisher: REES46; official catalog https://data.rees46.com/ and https://rees46.com/en/datasets
- Direct file: https://data.rees46.com/datasets/marketplace/2019-Oct.csv.gz
- Audited original: 42,448,764 event rows. Official catalog spans seven months (October 2019–April 2020); the often-quoted 285M total is not a two-month count.
- Project input: deterministic session-preserving 13% hash bucket sample, 5,511,929 events. Unit selected is `(user_id,user_session)`; all its available October events are retained.
- Source sessions missing user/session identifiers: two events excluded before selection.
- Source event types actually observed: view, cart, purchase. A schema slot for remove_from_cart does not imply any such observations.
- Fields: event_time, event_type, product_id, category_id, category_code, brand, price, user_id, user_session. No reliable transaction/order ID, quantities, refunds, currency code, or confirmed fraud outcomes.

## ULB/Worldline Credit Card Fraud Detection
- Original card: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
- Official TensorFlow tutorial documents the ULB/Worldline provenance and download: https://www.tensorflow.org/tutorials/structured_data/imbalanced_data
- Download: https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv
- Audited: 284,807 transactions, 492 fraud labels; September 2013 European cardholder transactions over approximately two days.
- Numeric PCA features V1–V28, elapsed Time, Amount, binary Class. Exact calendar/user/merchant identifiers are unavailable. No calendar dates or identities are inferred.

`results/source_audit.json` records the exact byte counts, download URLs, and SHA-256 hashes. Acquired for this course project on 12 October 2026. Raw files are excluded from the distributable package: rerun acquisition from the publishers, with attribution and review of current source terms before any further distribution. Do not interpret technical download access as a broad license grant. The included warehouse contains pseudonymous source-derived analytical records and is intended for this project's review; avoid public redistribution without checking source terms. No attempts to reidentify individuals are made.
