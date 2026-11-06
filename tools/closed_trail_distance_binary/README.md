# Closed-trail executables

This directory deliberately keeps the two author-distributed executables separate.

- `efficient_suurballe` is the older two-argument GML executable corresponding to
  `petr-prokop/closed_trail_distance`. Its public `SSCT.cpp` uses BFS and counts
  edges; the pinned NetworKit GML reader does not import edge weights. It therefore
  computes unweighted CT only.
- `efficient_suurballe_weighted` is the four-argument executable distributed in
  `petr-prokop/weighted_graph_hierarchical_agglomerative_clustering` for Snasel_4.
  SHA-256: `fecd5e7f7c38820dec55233a29687243a9edeb330838c2b607b078ee8d167aaa`.
  Use `INPUT edgelist full OUTPUT`, where each input row is `u v (1/weight)`.
- `libnetworkit.so` was built from official NetworKit tag `10.0` to satisfy the
  weighted executable's ABI. SHA-256:
  `0161350dbdafa772cb2a866204b34ad299f7923e0f59b723b36c2830be8ab8bb`.

The Python wrapper uses only the weighted executable for wAL/wCL and rejects
graphs containing bridges, matching Algorithm 1's input contract in Snasel_4.
