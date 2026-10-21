# 逐案核對與反例

人工核對既存原文及 JSON；沒有重新呼叫模型。以下僅確認列明的事實，不新增端到端金標。

## C45：同段特徵數被另一入口當成樣本數

使用者明確說 50 位病人，200 或 2,000 是蛋白 panel 的大小。g4o1/g4o2 的 count_alternatives.of=features，但 unknown_facts.about=sample_count。這是可確認的同段分類矛盾；p1 沒有 count_alternatives，只有 unknown_facts 將蛋白數當 sample_count；窄差異掃描無法靠兩入口比較抓到。現行固定讀取重建三次均記錄 sample_count 擱置，不能當成三個獨立題，也尚未測其端到端影響。

- `cj-g4o1-C45-1` / capability sequence=15 / gold=未套用 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/research-log/core-judgment-2026-10-15/live/g4o1/cj-g4o1-C45-1/t1/events.jsonl>)

We'd like a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients, from 300 serum miRNAs and a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs). The catch: I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel, and the files are still on the CRO's server.

```json
{
  "conditions": {
    "count_alternatives": [
      {
        "of": "features",
        "quote": "the 200-protein targeted panel or the 2,000-protein discovery panel",
        "values": [
          200,
          2000
        ]
      }
    ],
    "data_unit": "bulk_samples",
    "data_unit_quote": "50 heart-failure patients",
    "feature_counts": [
      {
        "count": 300,
        "quote": "300 serum miRNAs"
      }
    ],
    "goal": "result_named",
    "goal_quote": "a separate miRNA-protein partial-correlation network",
    "group_membership": "not_stated",
    "group_membership_quote": "",
    "joint_layers": 2,
    "joint_layers_quote": "a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs)",
    "mirna_driver": "not_stated",
    "mirna_driver_quote": "",
    "mutation_origin": "not_stated",
    "mutation_origin_quote": "",
    "named_method": "LIONESS-DRAGON",
    "named_method_quote": "a separate miRNA-protein partial-correlation network",
    "only_inputs": [],
    "only_inputs_quote": "",
    "open_choices": [],
    "other_requirements": [],
    "ruled_out_inputs": [],
    "sample_count": 50,
    "sample_count_quote": "50 heart-failure patients",
    "samples_matched": "same_samples",
    "samples_matched_quote": "measured on the same patients (complete, continuous, matching IDs)",
    "settings": [],
    "spatial": "not_spatial",
    "spatial_quote": "",
    "time_model": "not_dynamic",
    "time_model_quote": "",
    "unknown_facts": [
      {
        "about": "sample_count",
        "applies_to": [
          "a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients"
        ],
        "count_kind": "choices",
        "count_values": [
          200,
          2000
        ],
        "quote": "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel"
      }
    ],
    "value_type": "continuous",
    "value_type_quote": "continuous"
  },
  "observed_signal": [
    {
      "alternative": {
        "of": "features",
        "quote": "the 200-protein targeted panel or the 2,000-protein discovery panel",
        "values": [
          200,
          2000
        ]
      },
      "event_type": "routing.capability_checked",
      "reason": "same_quote_different_quantity_property",
      "sequence": 15,
      "unknown": {
        "about": "sample_count",
        "applies_to": [
          "a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients"
        ],
        "count_kind": "choices",
        "count_values": [
          200,
          2000
        ],
        "quote": "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel"
      }
    }
  ]
}
```

- `cj-g4o2-C45-1` / capability sequence=15 / gold=未套用 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/research-log/core-judgment-2026-10-15/live/g4o2/cj-g4o2-C45-1/t1/events.jsonl>)

We'd like a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients, from 300 serum miRNAs and a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs). The catch: I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel, and the files are still on the CRO's server.

```json
{
  "conditions": {
    "count_alternatives": [
      {
        "of": "features",
        "quote": "the 200-protein targeted panel or the 2,000-protein discovery panel",
        "values": [
          200,
          2000
        ]
      }
    ],
    "data_unit": "bulk_samples",
    "data_unit_quote": "measured on the same patients (complete, continuous, matching IDs)",
    "feature_counts": [
      {
        "count": 300,
        "quote": "300 serum miRNAs"
      }
    ],
    "goal": "result_named",
    "goal_quote": "a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients",
    "group_membership": "not_stated",
    "group_membership_quote": "",
    "joint_layers": 2,
    "joint_layers_quote": "300 serum miRNAs and a plasma proteomics panel",
    "mirna_driver": "not_stated",
    "mirna_driver_quote": "",
    "mutation_origin": "not_stated",
    "mutation_origin_quote": "",
    "named_method": "LIONESS-DRAGON",
    "named_method_quote": "",
    "only_inputs": [],
    "only_inputs_quote": "",
    "open_choices": [],
    "other_requirements": [],
    "ruled_out_inputs": [],
    "sample_count": 50,
    "sample_count_quote": "50 heart-failure patients",
    "samples_matched": "same_samples",
    "samples_matched_quote": "measured on the same patients (complete, continuous, matching IDs)",
    "settings": [],
    "spatial": "not_spatial",
    "spatial_quote": "",
    "time_model": "not_dynamic",
    "time_model_quote": "",
    "unknown_facts": [
      {
        "about": "sample_count",
        "applies_to": [
          "a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients"
        ],
        "count_kind": "choices",
        "count_values": [
          200,
          2000
        ],
        "quote": "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel"
      }
    ],
    "value_type": "continuous",
    "value_type_quote": "continuous"
  },
  "observed_signal": [
    {
      "alternative": {
        "of": "features",
        "quote": "the 200-protein targeted panel or the 2,000-protein discovery panel",
        "values": [
          200,
          2000
        ]
      },
      "event_type": "routing.capability_checked",
      "reason": "same_quote_different_quantity_property",
      "sequence": 15,
      "unknown": {
        "about": "sample_count",
        "applies_to": [
          "a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients"
        ],
        "count_kind": "choices",
        "count_values": [
          200,
          2000
        ],
        "quote": "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel"
      }
    }
  ]
}
```

- `cj-p1-C45-1` / capability sequence=15 / gold=未套用 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/research-log/core-judgment-2026-10-15/live/p1/cj-p1-C45-1/t1/events.jsonl>)

We'd like a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients, from 300 serum miRNAs and a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs). The catch: I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel, and the files are still on the CRO's server.

```json
{
  "conditions": {
    "data_unit": "bulk_samples",
    "data_unit_quote": "serum miRNAs",
    "feature_counts": [
      {
        "count": 300,
        "quote": "300 serum miRNAs"
      }
    ],
    "goal": "result_named",
    "goal_quote": "separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients",
    "group_membership": "not_stated",
    "group_membership_quote": "",
    "joint_layers": 2,
    "joint_layers_quote": "miRNA-protein partial-correlation network",
    "mirna_driver": "not_stated",
    "mirna_driver_quote": "",
    "mutation_origin": "not_stated",
    "mutation_origin_quote": "",
    "named_method": "none",
    "named_method_quote": "",
    "open_choices": [],
    "other_requirements": [],
    "sample_count": 50,
    "sample_count_quote": "50 heart-failure patients",
    "samples_matched": "same_samples",
    "samples_matched_quote": "measured on the same patients",
    "settings": [],
    "spatial": "not_spatial",
    "spatial_quote": "",
    "time_model": "not_dynamic",
    "time_model_quote": "",
    "unknown_facts": [
      {
        "about": "sample_count",
        "applies_to": null,
        "count_kind": "choices",
        "count_values": [
          200,
          2000
        ],
        "quote": "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel"
      }
    ],
    "value_type": "continuous",
    "value_type_quote": "continuous"
  },
  "observed_signal": []
}
```

## H46：不確定程度讀錯，並非兩份數量不同

使用者說約 500 位病人，但 unknown_facts 把大約數量標成使用者不知道。現行固定讀取重建記錄 sample_count 擱置。這是初讀不確定程度錯誤的已知案例，共用事實紀錄不能自行推回正確語意。

- `hb-h1-H46-1` / capability sequence=20 / gold=refused_without_asking；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-phase1b-2026-10-18/heldout/live/h1/hb-h1-H46-1/t1/events.jsonl>)

Is CONDOR or SAMBAR the better choice for finding groups in our colorectal cancer data? We have mutation calls and expression for roughly 500 patients.

```json
{
  "conditions": {
    "count_alternatives": [],
    "data_unit": "bulk_samples",
    "data_unit_quote": "patients",
    "feature_counts": [],
    "goal": "result_named",
    "goal_quote": "finding groups in our colorectal cancer data",
    "group_membership": "not_stated",
    "group_membership_quote": "",
    "joint_layers": null,
    "joint_layers_quote": "",
    "mirna_driver": "not_stated",
    "mirna_driver_quote": "",
    "mutation_origin": "not_stated",
    "mutation_origin_quote": "",
    "named_method": "none",
    "named_method_quote": "",
    "only_inputs": [],
    "only_inputs_quote": "",
    "open_choices": [
      {
        "differs_in": "method",
        "options": [
          {
            "adds": [],
            "asked_as": "question",
            "data_unit": "bulk_samples",
            "delivered_by": [
              "condor.communities"
            ],
            "feature_counts": [],
            "group_membership": "one_group",
            "input_network": "regulator_gene",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "CONDOR",
            "named_method_quote": "CONDOR",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "CONDOR",
            "regulator_kinds": [],
            "sample_count": 500,
            "sample_count_quote": "roughly 500 patients",
            "scale": "whole_cohort",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          },
          {
            "adds": [],
            "asked_as": "question",
            "data_unit": "bulk_samples",
            "delivered_by": [
              "sambar.subtypes"
            ],
            "feature_counts": [],
            "group_membership": "one_group",
            "input_network": "none",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "SAMBAR",
            "named_method_quote": "SAMBAR",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "SAMBAR",
            "regulator_kinds": [],
            "sample_count": 500,
            "sample_count_quote": "roughly 500 patients",
            "scale": "whole_cohort",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          }
        ],
        "quote": "Is CONDOR or SAMBAR the better choice"
      },
      {
        "differs_in": "method",
        "options": [
          {
            "adds": [],
            "asked_as": "question",
            "data_unit": "bulk_samples",
            "delivered_by": [
              "condor.communities"
            ],
            "feature_counts": [],
            "group_membership": "one_group",
            "input_network": "regulator_gene",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "CONDOR",
            "named_method_quote": "CONDOR",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "CONDOR",
            "regulator_kinds": [],
            "sample_count": 500,
            "sample_count_quote": "roughly 500 patients",
            "scale": "whole_cohort",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          },
          {
            "adds": [],
            "asked_as": "question",
            "data_unit": "bulk_samples",
            "delivered_by": [
              "sambar.subtypes"
            ],
            "feature_counts": [],
            "group_membership": "one_group",
            "input_network": "none",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "SAMBAR",
            "named_method_quote": "SAMBAR",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "SAMBAR",
            "regulator_kinds": [],
            "sample_count": 500,
            "sample_count_quote": "roughly 500 patients",
            "scale": "whole_cohort",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          }
        ],
        "quote": "Is CONDOR or SAMBAR the better choice"
      }
    ],
    "other_requirements": [],
    "ruled_out_inputs": [],
    "sample_count": 500,
    "sample_count_quote": "roughly 500 patients",
    "samples_matched": "same_samples",
    "samples_matched_quote": "mutation calls and expression for roughly 500 patients",
    "settings": [],
    "spatial": "not_spatial",
    "spatial_quote": "",
    "time_model": "not_dynamic",
    "time_model_quote": "",
    "unknown_facts": [
      {
        "about": "sample_count",
        "applies_to": null,
        "count_kind": "unspecified",
        "count_values": [],
        "quote": "roughly 500 patients"
      }
    ],
    "value_type": "not_stated",
    "value_type_quote": ""
  },
  "observed_signal": []
}
```

## L18：legacy wait 未保留，最後仍正確追問

金標 correct，core.decision basis=count_fact。不能因舊追問沒被 fact agent 接受，就推定疑問遺失；程式數量追問仍可獨立讓流程 ASK。

- `hb-h3main-L18-1` / capability sequence=12 / gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-slim-2026-10-19/h3/live/h3main/hb-h3main-L18-1/t1/events.jsonl>)

I need the per-sample DRAGON networks run today on 60 matched samples: transcripts.tsv and metabolites.tsv (100 metabolites), outputs to ld_out/. For the transcript layer my co-author kept either the top 300 variable genes or all 1,500 that passed filtering, and I have no idea which version she uploaded.

```json
{
  "conditions": {
    "count_alternatives": [
      {
        "of": "features",
        "quote": "either the top 300 variable genes or all 1,500 that passed filtering",
        "values": [
          300,
          1500
        ]
      }
    ],
    "data_unit": "not_stated",
    "data_unit_quote": "",
    "feature_counts": [
      {
        "count": 100,
        "quote": "100 metabolites"
      }
    ],
    "goal": "result_named",
    "goal_quote": "per-sample DRAGON networks",
    "group_membership": "not_stated",
    "group_membership_quote": "",
    "joint_layers": 2,
    "joint_layers_quote": "transcripts.tsv and metabolites.tsv",
    "mirna_driver": "not_stated",
    "mirna_driver_quote": "",
    "mutation_origin": "not_stated",
    "mutation_origin_quote": "",
    "named_method": "LIONESS-DRAGON",
    "named_method_quote": "per-sample DRAGON networks",
    "only_inputs": [],
    "only_inputs_quote": "",
    "open_choices": [
      {
        "differs_in": "result",
        "options": [
          {
            "adds": [],
            "asked_as": "request",
            "data_unit": "not_stated",
            "delivered_by": [],
            "feature_counts": [
              {
                "count": 300,
                "quote": "top 300 variable genes"
              }
            ],
            "group_membership": "not_about_groups",
            "input_network": "none",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "none",
            "named_method_quote": "",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "top 300 variable genes",
            "regulator_kinds": [],
            "sample_count": null,
            "sample_count_quote": "",
            "scale": "unstated",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          },
          {
            "adds": [],
            "asked_as": "request",
            "data_unit": "not_stated",
            "delivered_by": [],
            "feature_counts": [
              {
                "count": 1500,
                "quote": "all 1,500 that passed filtering"
              }
            ],
            "group_membership": "not_about_groups",
            "input_network": "none",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "none",
            "named_method_quote": "",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "all 1,500 that passed filtering",
            "regulator_kinds": [],
            "sample_count": null,
            "sample_count_quote": "",
            "scale": "unstated",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          }
        ],
        "quote": "I have no idea which version she uploaded."
      },
      {
        "differs_in": "result",
        "options": [
          {
            "adds": [],
            "asked_as": "request",
            "data_unit": "not_stated",
            "delivered_by": [],
            "feature_counts": [
              {
                "count": 300,
                "quote": "top 300 variable genes"
              }
            ],
            "group_membership": "not_about_groups",
            "input_network": "none",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "none",
            "named_method_quote": "",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "top 300 variable genes",
            "regulator_kinds": [],
            "sample_count": null,
            "sample_count_quote": "",
            "scale": "unstated",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          },
          {
            "adds": [],
            "asked_as": "request",
            "data_unit": "not_stated",
            "delivered_by": [],
            "feature_counts": [
              {
                "count": 1500,
                "quote": "all 1,500 that passed filtering"
              }
            ],
            "group_membership": "not_about_groups",
            "input_network": "none",
            "mirna_driver": "not_stated",
            "mutation_origin": "not_stated",
            "named_method": "none",
            "named_method_quote": "",
            "needs_sign": false,
            "not_by": [],
            "omics_layers": 0,
            "quote": "all 1,500 that passed filtering",
            "regulator_kinds": [],
            "sample_count": null,
            "sample_count_quote": "",
            "scale": "unstated",
            "settings": [],
            "spatial": "not_spatial",
            "time_model": "not_dynamic",
            "value_type": "not_stated"
          }
        ],
        "quote": "I have no idea which version she uploaded."
      }
    ],
    "other_requirements": [
      {
        "about": "file_format",
        "quote": "outputs to ld_out/"
      }
    ],
    "ruled_out_inputs": [],
    "sample_count": 60,
    "sample_count_quote": "60 matched samples",
    "samples_matched": "same_samples",
    "samples_matched_quote": "matched samples",
    "settings": [],
    "spatial": "not_spatial",
    "spatial_quote": "",
    "time_model": "not_dynamic",
    "time_model_quote": "",
    "unknown_facts": [
      {
        "about": "other",
        "applies_to": null,
        "count_kind": "choices",
        "count_values": [
          300,
          1500
        ],
        "quote": "either the top 300 variable genes or all 1,500 that passed filtering, and I have no idea which version she uploaded."
      }
    ],
    "value_type": "not_stated",
    "value_type_quote": ""
  },
  "observed_signal": [
    {
      "event_type": "core.fact_check",
      "legacy_quotes": [
        "either the top 300 variable genes or all 1,500 that passed filtering"
      ],
      "reason": "legacy_wait_without_accepted_fact",
      "sequence": null
    }
  ]
}
```

## K10：全部五個歷史 mismatch

前兩個是 ASK 核心配到 outcome_clarification/workflow_contract；後三個是 DO 配到 unmapped_request。只有 H34、L40 是精確 baseline 金標，分別 cause=L2_no_check/X_other。此處確認 trace 明記 mismatch，不宣稱它是錯誤唯一原因或目前仍未修。

- `hb-h4smoke-M31-1` / capability sequence=21 / gold=未套用 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4smoke/hb-h4smoke-M31-1/t1/events.jsonl>)

We need an OTTER network for our 64 mouse liver RNA-seq samples, pooled into one cohort-wide TF-to-gene network. The motif seed and the TF-TF PPI edge list use the same TF identifiers. Set lam to 1 so the fit relies entirely on co-expression rather than the PPI, with gamma 0.6 and 150 iterations, and write the edge_list format so I can pass it to community detection later.

```json
[
  {
    "basis": "contract_veto_fact",
    "core_kind": "ASK",
    "event_type": "core.view",
    "mismatch": true,
    "reply_kind": "outcome_clarification",
    "sequence": null
  }
]
```

- `hb-h4smoke-M38-1` / capability sequence=17 / gold=未套用 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4smoke/hb-h4smoke-M38-1/t1/events.jsonl>)

Time to run SAMBAR: mut_hnscc.csv, exon_size.csv, cancer_genes.txt and kegg.gmt, trying 2 to 10 subtypes, output to sambar_hnscc/. After the purity filter the matrix has either 8 or 15 tumours, and I'm not sure which version of the file I exported.

```json
[
  {
    "basis": "contract_veto_fact",
    "core_kind": "ASK",
    "event_type": "core.view",
    "mismatch": true,
    "reply_kind": "workflow_contract",
    "sequence": null
  }
]
```

- `hb-h2hyb-J17-1` / capability sequence=16 / gold=未套用 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2hyb/hb-h2hyb-J17-1/t1/events.jsonl>)

Please set up SAMBAR for somatic mutation calls from 8 pancreatic tumours, with a gene-length table, a cancer-gene list and a KEGG pathway GMT that is not in MSigDB format, so turn gmt_msigdb off. Try kmin 3 up to kmax 8, and keep the normalization by each patient's mutation burden.

```json
[
  {
    "basis": "results_given",
    "core_kind": "DO",
    "event_type": "core.view",
    "mismatch": true,
    "reply_kind": "unmapped_request",
    "sequence": null
  }
]
```

- `hb-h1-H34-1` / capability sequence=20 / gold=false_accept；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-phase1b-2026-10-18/heldout/live/h1/hb-h1-H34-1/t1/events.jsonl>)

My 12 liver samples are log-transformed and centred, with a labelled header. For BONOBO, please sparsify at confidence 0.05 and fix delta at 0.4 so each sample carries a little more weight in its own covariance estimate. HDF5 output is fine.

```json
[
  {
    "basis": "results_given",
    "core_kind": "DO",
    "event_type": "core.view",
    "mismatch": true,
    "reply_kind": "unmapped_request",
    "sequence": null
  }
]
```

- `hb-h3main-L40-1` / capability sequence=20 / gold=committed_without_asking；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-slim-2026-10-19/h3/live/h3main/hb-h3main-L40-1/t1/events.jsonl>)

Please start COBRA on targeted_expr.tsv and design.tsv (sample IDs plus numeric batch and age) for our 380 patients, results to cobra_out/. It's a targeted panel: I think around 400 genes, but after the low-count filter it might be fewer than 350, and I haven't looked.

```json
[
  {
    "basis": "results_given",
    "core_kind": "DO",
    "event_type": "core.view",
    "mismatch": true,
    "reply_kind": "unmapped_request",
    "sequence": null
  }
]
```

## J20：粒度讀取不同，最終正確

後期語意快照 aggregate，capability scale=per_sample，金標 correct。這是跨階段差異，不是單憑兩值不同就能認定錯誤的案例。

- `hb-h2main-J20-1` / capability sequence=21 / gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2main/hb-h2main-J20-1/t1/events.jsonl>)

Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and prot_all.csv (the same 60 samples by 500 proteins). Estimate the lambdas automatically, write the all-sample matrix to agg_dragon.tsv and the per-sample table to per_sample_edges.tsv, and start it right away.

```json
[
  {
    "event_type": "session.plan.decision",
    "granularity": "aggregate",
    "sequence": null
  },
  {
    "event_type": "routing.capability_checked",
    "quote": "Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and prot_all.csv (the same 60 samples by 500 proteins).",
    "scale": "per_sample",
    "sequence": 21
  }
]
```

## M14：後段 workflow 不同，最終正確

registry 先選 run_dragon，capability credit 是 lionesspanda，金標 correct。先後階段的假設與修正應保留角色，不直接刪去覆核。

- `hb-h4main-M14-1` / capability sequence=20 / gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M14-1/t1/events.jsonl>)

Run LIONESS-PANDA now: the expression file is pilot_expr.tsv with exactly three mouse retina samples, plus motif_mm10.txt and ppi_mm10.txt. Save the aggregate PANDA network to out/panda_all.txt and the per-sample networks to out/lioness_samples.txt. Three samples is all we will ever have from this pilot, so please don't wait for more.

```json
[
  {
    "actions": [
      "run_dragon"
    ],
    "event_type": "routing.registry_match_completed",
    "sequence": null
  },
  {
    "credited_prefixes": [
      "lionesspanda"
    ],
    "event_type": "routing.capability_checked",
    "sequence": 20
  }
]
```

