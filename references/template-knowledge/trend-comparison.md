# Trend and comparison routing

Use `line.*` when x is ordered and continuity or trajectory matters. Use `line.confidence_band` or
`line.errorbar` only when the uncertainty meaning is explicit. Use `bar.*` for categorical
magnitudes, not to conceal a distribution; use `estimation.point_interval` when estimate precision
is central. A zero baseline is the default for magnitude bars and must not be truncated when that
would mislead.

