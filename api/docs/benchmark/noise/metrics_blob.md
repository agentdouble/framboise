# MetricsBlob Format (Unrelated)

MetricsBlob is a binary format for telemetry.

- Magic: "MBL0"
- Payloads are protobuf
- Trailer is CRC-32C

It is not compatible with PackX.
