# Research Questions

## Phase 2 New Questions

### Object Generation
1. What is the minimum schema vocabulary that can express 80% of useful intelligent objects?
2. Can a schema be as expressive as a hand-written class?
3. How do we handle schema evolution (changing a schema after objects are created)?
4. Can objects generate their own schema extensions?
5. What is the security risk of dynamic object generation?

### Intelligence as Resource
6. What is the latency of allocating cognition on demand?
7. Can we maintain "warm pools" of reasoning capacity?
8. What is the cold-start penalty for dormant objects?
9. How do we prevent reasoning allocation from becoming a bottleneck?
10. Can we predict which objects will need reasoning before they request it?

### Runtime as Intelligence OS
11. What OS primitives are needed for intelligence? (beyond process, memory, file)
12. Can the runtime be implemented in user-space first?
13. What is the minimal viable runtime?
14. How does the runtime handle failure of an intelligent object?
15. Can the runtime itself be an intelligent object?

### Object Economics
16. What is the simplest viable economic model? (budgets vs. markets vs. auctions)
17. How do we measure the value of an object's action?
18. How do we measure the value of learning (not just action)?
19. What prevents objects from gaming the economic system?
20. Can economic incentives stabilize large object populations?

### Scaling
21. Does the Sparse Cognition Hypothesis hold for real applications?
22. What is the actual active fraction α for different domains?
23. What is the break-even object count for different economic models?
24. How does cost scale with relationship density?
25. What is the maximum event throughput per object?

### Object Lifecycle
26. What are the minimum lifecycle states needed? (birth, observe, sleep, retire)
27. When should objects specialize vs. remain general?
28. When should objects merge vs. remain separate?
29. What is the optimal retirement policy?
30. Can objects be resurrected from archive? When?

### Memory
31. What is the optimal memory hierarchy for intelligent objects?
32. How fast does memory retrieval degrade with memory size?
33. What is the optimal forgetting rate?
34. How do we handle memory contradictions at scale?
35. Can memory be shared between objects safely?

### Communication
36. What is the optimal communication topology? (mesh, star, hierarchical)
37. How do we prevent O(N²) communication?
38. Can objects discover each other without central registry?
39. What is the cost of semantic discovery?
40. How do we prevent communication spam?

### Security
41. What attacks are possible on an intelligent object runtime?
42. How do we prevent prompt injection at scale?
43. How do we prevent memory poisoning?
44. What is the security model for object-to-object communication?
45. Can a malicious object take down the entire system?

### World Models
46. For what class of problems is a world model worth its cost?
47. Can a shared world model be maintained by the runtime?
48. How do objects plan inside a world model?
49. What is the reality gap for software world models?
50. Can world models be learned from object interactions?

### Probabilistic Beliefs
51. Do confidence scores improve decision quality?
52. Can LLMs reason effectively with probabilistic state?
53. What is the cost of maintaining belief distributions?
54. When is causal inference worth the cost?
55. Can prediction error reliably drive learning?

### Surprise and Attention
56. What is the best surprise metric for software objects?
57. Does surprise-driven cognition improve efficiency?
58. Can we predict surprise before it happens?
59. What is the optimal surprise threshold?
60. Does surprise correlate with learning opportunity?

### Composition
61. What is the composition algebra for intelligent objects?
62. What happens to identity when objects merge?
63. What happens to memory when objects merge?
64. Can composed objects be decomposed later?
65. What is the security model for composition?

### Self-Organization
66. Can objects self-organize into useful structures?
67. What local rules produce global coherence?
68. How do we prevent self-organization from producing chaos?
69. What is the role of noise in self-organization?
70. Can self-organization be directed by developer goals?

### Meta-Questions
71. Is the Intelligence OS concept genuinely new or just a rebranding?
72. What is the smallest falsifiable experiment for the paradigm?
73. What would prove the paradigm wrong?
74. What would prove the paradigm right?
75. What is the most likely way this project fails?
76. What is the most likely unexpected success?
77. If this works, what kind of computer are we building?
78. If this fails, what is the most valuable salvage?
79. What existing system is closest to the vision?
80. What single feature would make developers adopt this?
