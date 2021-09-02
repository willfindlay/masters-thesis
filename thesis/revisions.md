- [ ] fix typos (see Viau's notes)
  - [x] grsecurity

- [ ] early definition of confinement
  - NOTE: in progress, background.tex line 16
  - TODO: revisit section 3.6.1 (confinement policy and enforcement engine)
    - either need to make this match or completely replace it with our definition in the background
  - Viau: definition is too generic, same as reference monitor.
          should explicitly contrast bpfbox and bpfcontain.
  - TODO: probably just remove CHERI capabilities from our discussion

- [x] explain geometric mean
  - evaluation.tex line 675 (in the middle of this paragraph)
  - evaluation.tex line 634 (tab:phoronix-geometric)

- [x] clarify 2% STDEV/11+ runs

- [ ] explain performance oddities
  - put this in its own subsection: "Performance Degradation in BPFContain"
  - discuss the fact that BPFContain deals in a higher level of abstraction than BPFBox
  - BPFBox is basically a thin wrapper over LSM hooks
  - BPFContain adds additional confinement semantics on top of this
  - this additional level of abstraction complicates the code in the BPF programs, which
    introduces the potential to make performance-critical mistakes
  - highlight the need for subsequent optimization

- [ ] compare overhead with academic security efforts (quote stats)
  - TODO: get a nice list of comparable performance results
    (probably should be things already cited in the background?)

- [ ] virtualization: aggregation & segregation
  - TODO: revisit this in the intro
  - TODO: revisit this in background
  - TODO: revisit this in confinement problem

- [ ] remove virtualization less secure than container confinement
  - paragraph in confinement problem line 94

- [x] clarify forward & backward compatibility

- [ ] discuss how to break it
  - put this in its own subsection in the security evaluation
  - things to maybe talk about:
    - LSM hook placement (but all LSMs rely on this)
    - input validation (system calls vs LSM hooks)
    - input validation (BPF programs, verifier)
    - killing the daemon (self-defence)
    - unloading/manipulating BPF programs / maps
    - loading code into the kernel to bypass enforcement (this is already game over, so it's not a concern)
    - taking advantage of an overly-permissive policy
