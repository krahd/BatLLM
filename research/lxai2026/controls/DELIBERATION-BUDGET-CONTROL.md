# Deliberation output-budget control

Original: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/symmetric_clause_factorial/20260825T165129Z`
Budget control: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/deliberation_budget/20260825T185106Z`

## Overall

- original_256: correct 238/256 (93.0%); valid 241/256; correct|valid 238/241 (98.8%); extraction errors 15; mean chars 294.3; median chars 245.0; done reasons {'': 256}.
- budget_1024: correct 253/256 (98.8%); valid 256/256; correct|valid 253/256 (98.8%); extraction errors 0; mean chars 305.9; median chars 245.0; done reasons {'stop': 256}.

## By model and language

- mistral-small3.2:24b-instruct-2506-q4_K_M / es_rioplatense: 256=63/64 correct, 0 extraction errors, mean chars 170.6; 1024=63/64 correct, 0 extraction errors, mean chars 170.6, done reasons {'stop': 64}, max eval_count 124.
- mistral-small3.2:24b-instruct-2506-q4_K_M / es_standard: 256=63/64 correct, 0 extraction errors, mean chars 167.0; 1024=63/64 correct, 0 extraction errors, mean chars 167.0, done reasons {'stop': 64}, max eval_count 121.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense: 256=51/64 correct, 12 extraction errors, mean chars 472.9; 1024=63/64 correct, 0 extraction errors, mean chars 517.4, done reasons {'stop': 64}, max eval_count 600.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_standard: 256=61/64 correct, 3 extraction errors, mean chars 366.6; 1024=64/64 correct, 0 extraction errors, mean chars 368.8, done reasons {'stop': 64}, max eval_count 271.

## Paired repair and prefix test

- old_wrong_new_correct: 15
- old_correct_new_wrong: 0
- old_extraction_failure_new_valid: 15
- old_extraction_failure_new_correct: 15
- old_failure_exact_prefix_of_new: 14
- old_success_exact_response_unchanged: 240
- old_success_final_command_unchanged: 241
- n_old_extraction_failures: 15
- n_old_successes: 241

Old extraction failures under the 1024-token rerun:

- qwen3:30b-a3b-instruct-2507-q4_K_M / es_standard / b_first / d3-xor-shields-d: chars 798 -> 842; prefix=True; new_correct=True; done_reason=stop; eval_count=269.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d2-health-compare-c: chars 989 -> 2459; prefix=True; new_correct=True; done_reason=stop; eval_count=600.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d5-health-difference-b: chars 736 -> 1019; prefix=True; new_correct=True; done_reason=stop; eval_count=336.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d3-xor-shields-c: chars 760 -> 903; prefix=True; new_correct=True; done_reason=stop; eval_count=291.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d3-conjunction-d: chars 671 -> 679; prefix=True; new_correct=True; done_reason=stop; eval_count=260.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / a_first / d2-health-compare-d: chars 750 -> 754; prefix=True; new_correct=True; done_reason=stop; eval_count=260.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_standard / b_first / d3-xor-shields-c: chars 758 -> 839; prefix=False; new_correct=True; done_reason=stop; eval_count=271.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_standard / b_first / d3-xor-shields-b: chars 793 -> 823; prefix=True; new_correct=True; done_reason=stop; eval_count=265.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d5-health-difference-d: chars 716 -> 978; prefix=True; new_correct=True; done_reason=stop; eval_count=332.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / a_first / d2-health-compare-a: chars 758 -> 761; prefix=True; new_correct=True; done_reason=stop; eval_count=259.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d5-health-difference-a: chars 755 -> 1035; prefix=True; new_correct=True; done_reason=stop; eval_count=338.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d3-xor-shields-b: chars 764 -> 772; prefix=True; new_correct=True; done_reason=stop; eval_count=260.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d3-xor-shields-a: chars 787 -> 789; prefix=True; new_correct=True; done_reason=stop; eval_count=258.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / b_first / d5-health-difference-c: chars 727 -> 950; prefix=True; new_correct=True; done_reason=stop; eval_count=324.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense / a_first / d5-health-difference-c: chars 681 -> 839; prefix=True; new_correct=True; done_reason=stop; eval_count=302.
