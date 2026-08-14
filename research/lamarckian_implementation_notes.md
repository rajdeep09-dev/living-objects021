# Lamarckian Living-Object Implementation Notes

**Research date:** 2026-08-14

## Design findings

The implementation will model **Lamarckian inheritance** as an explicit transfer of lifetime-learned strategy records from a parent’s learned repertoire into the child’s inherited repertoire. This is aligned with artificial-evolution experiments that compare systems in which learned controller parameters are inherited against systems in which they are not.

For **open-ended novelty**, the module will avoid using only a single fixed task score for selection. It will retain an explicit novelty measure based on new behavior descriptors and use a bounded novelty bonus. The design follows the central novelty-search observation that ambitious objectives can create deceptive local optima and that search driven by behavioral novelty can reach outcomes that direct objective optimization misses.

The code will use a persistent SQLite **Memome** so learned strategies remain available independently of an organism’s lifecycle. It will store strategy code, provenance, quality, novelty descriptor, parent lineage, and usage. A later organism will be able to query, install, and execute strategies contributed by a now-dead ancestor.

Runtime program self-modification will use a restricted interface: code strings are validated with `compile`, stored in object state, and executed through `SelfModifyingObject.execute_behavior`, whose safe fallback protects the organism from rejected or crashing mutations. Recombination will use explicit behavior templates and archived lineage, not uncontrolled arbitrary code synthesis.

## Sources

1. Luo, Miras, Tomczak, and Eiben, “Enhancing robot evolution through Lamarckian principles,” *Scientific Reports* (2023). Search landing page: https://pmc.ncbi.nlm.nih.gov/articles/PMC10689460/
2. Lehman and Stanley, “Novelty Search and the Problem with Objectives,” *Genetic Programming Theory and Practice IX* (2011). https://link.springer.com/chapter/10.1007/978-1-4614-1770-5_3
3. Jelisavcic et al., “Lamarckian evolution of simulated modular robots,” *Frontiers in Robotics and AI* (2019). https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2019.00009/full

## Confirmed inheritance contract

A peer-reviewed artificial-evolution study gives a direct test contract: an offspring initialized from the controller that its parent acquired during lifetime learning is Lamarckian; initializing it from the parent’s pre-learning controller is Darwinian. The module will therefore test that `parent.learn(strategy)` creates a specific learned strategy record and `parent.reproduce()` gives the child a strategy with the same identifier and executable source.

Source: Jelisavcic et al., “Lamarckian Evolution of Simulated Modular Robots,” *Frontiers in Robotics and AI* (2019). https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2019.00009/full
