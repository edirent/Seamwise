# Seamwise 逻辑失败研究结论

本次完成归因、条件局部求解比较、BP 与候选/半径策略实现，以及新独立样本上的固定配置检验。成功标准是可复现的证据与诚实的准确率—计算代价结论，不预设必须达到 Tesseract 水平。原始论文实验、旧结果及旧解码器未改动。

## Q1：可证实的失败比例

旧测试已降为探索数据。84 个分层诊断样本的 native trace 与归档解码器逐位一致，其中 d3/d5 各含16个失败、BB含12个失败。P0/P1阶段生产半径下，便宜正确候选的搜索不足证据为6/16、2/16、0/12；全部测试后，对固定选定配置回放原84个诊断样本，合并正见证增至7/16、4/16、12/12；不可达为2/16、0/16、0/12；按生成候选的仿射基点修正后，正确逻辑方向未在增长支撑中暴露为14/16、13/16、7/12。类别可重叠，未暴露不等于证明它是唯一原因，也不证明存在便宜的正确候选。最终搜索见证的分层加权比例为44.9%、27.8%、100.0%，探索性点位95%有限总体区间分别为15.2%–81.7%、6.9%–68.1%、78.6%–100.0%；阶段记录及最终交集见 `failure_attribution/FINAL_ATTRIBUTION.md`。未找到见证不是不存在正确低成本解的证明。没有拿到证明所有正确解都无法下降的 ACCEPTANCE_LIMITED 最优性证书；这不是证明成本规则从未受限。

实际原版生产路径另有以下选择冲突：surface_d3_p0.003_B4 0/16（正确候选被拒0，正确初值被错误更新破坏0）；surface_d5_p0.006_B4 3/16（正确候选被拒3，正确初值被错误更新破坏0）；bb144_p0.015_B4 7/12（正确候选被拒2，正确初值被错误更新破坏5）。BB按分层加权为58.3%，点位95%有限总体区间33.3%–81.0%。这与最终状态条件查询的计数范围不同，不应混为同一张表，也不是所有正确解均被成本规则阻挡的最优性证明。详见 failure_attribution/TRAJECTORY_SELECTION.md。

## Q2：主要限制是什么

证据支持多种并存限制：有直接的搜索不足证书；多数失败样本缺少增长支撑中的目标逻辑方向；d5/BB有正确候选因成本被拒绝，BB还出现便宜但逻辑错误的更新破坏正确初值。成本与逻辑正确性不一致得到逐样本证实，但精确逻辑类后验与全局最优性未被解决。BB的固定配置回放已为12/12旧失败给出更便宜的正确全带解，因此这些样本在形式定义上都不是ACCEPTANCE_LIMITED。匹配的32个验证输入上，原BP即使增加到60次迭代仍为0/32收敛；尺度0.8、60次上限不加阻尼为7/32收敛，加阻尼后为32/32收敛、平均5.09次迭代。d3也观察到阻尼改善，但d5的硬残差降低并未保证更好的逻辑结果。详见 `BP_QUALITY.md`。这支持BB上的推断/候选排序限制，不能把BP认定为所有工作负载的唯一主因。固定外部变量与搜索/选择的影响应按对照分别判断。未发现模型/数值不一致，但检查范围有限。

## Q3：新独立测试中的改善

以下配置完全由512个验证样本选定，再固定测试样本数及五小时预算。主比较使用相同的8000个新独立电路样本；多重比较校正固定为425组。

- surface_d3_p0.003_B4：原版 403/8000 → 选定版 178/8000，观察到的相对失败数下降 55.8%；Tesseract 125/8000。配对校正结论：A_LOWER_FAILURE_RISK。零失败不代表真实风险为零。
- surface_d5_p0.006_B4：原版 1011/8000 → 选定版 868/8000，观察到的相对失败数下降 14.1%；Tesseract 231/8000。配对校正结论：NOT_ESTABLISHED。零失败不代表真实风险为零。
- bb144_p0.015_B4：原版 29/8000 → 选定版 1/8000，观察到的相对失败数下降 96.6%；Tesseract 0/8000。配对校正结论：NOT_ESTABLISHED。零失败不代表真实风险为零。
主配置相对原版观察到的最大绝对风险下降位于 surface_d3_p0.003_B4，下降 2.813 个百分点。这是对冻结配置的描述，不据此重新选择测试配置。

## Q4：延迟与内存代价

- surface_d3_p0.003_B4：独立计时均值 0.2424 → 1.171 ms；p99 1.183 → 2.99 ms。
- surface_d5_p0.006_B4：独立计时均值 7.527 → 56.03 ms；p99 14.88 → 86.62 ms。
- bb144_p0.015_B4：独立计时均值 15.48 → 3.942 ms；p99 30.09 → 12.78 ms。

均值、尾延迟、最大值及独立内存/分配/浸泡结果均在 `LATENCY_RESULTS.md`。候选预算固定，不隐藏无界搜索；表中如有显著 p99 回退，则准确率收益需要承担该代价。RSS包含解释器/样本/分配器，容量负载不是完整总内存。
独立512-ID内存浸泡的进程高水位RSS：surface_d3_p0.003_B4 109.7→109.8 MiB；surface_d5_p0.006_B4 117.7→142.7 MiB；bb144_p0.015_B4 132.2→129.2 MiB。RSS含解释器、样本和分配器；调用分配请求不是同时存活内存，观测值不是所有输入的内存上界。

## Q5：是否满足 Tesseract 的10%约束

- surface_d3_p0.003_B4：NOT_ESTABLISHED。
- surface_d5_p0.006_B4：VIOLATION_DEMONSTRATED。
- bb144_p0.015_B4：NOT_ESTABLISHED。

不以边际区间重叠推断优劣，不把双零误当相对非劣证明；未通过校正的非劣门槛就不宣称获得“准确率匹配的速度优势”。

## Q6：收益来自修复结构还是更强内层

固定2000个共享测试ID的对照如下；完整配对区间在 `accuracy_analysis.json`。更换内层、BP参数、半径、候选与初值的作用不能混成同一个结构性收益。

| 工作负载 | 对照 | 失败数/N |
|---|---|---:|
| surface_d3_p0.003_B4 | selected_combined | 43/2000 |
| surface_d3_p0.003_B4 | same_BP_fixed_radius | 43/2000 |
| surface_d3_p0.003_B4 | same_BP_radius2 | 40/2000 |
| surface_d3_p0.003_B4 | same_BP_joint | 43/2000 |
| surface_d3_p0.003_B4 | matched_cut | 55/2000 |
| surface_d3_p0.003_B4 | matched_joint | 43/2000 |
| surface_d3_p0.003_B4 | stronger_solver | 96/2000 |
| surface_d3_p0.003_B4 | strong_joint | 103/2000 |
| surface_d3_p0.003_B4 | strong_cut | 99/2000 |
| surface_d3_p0.003_B4 | strong_all_repair | 86/2000 |
| surface_d5_p0.006_B4 | selected_combined | 206/2000 |
| surface_d5_p0.006_B4 | same_BP_fixed_radius | 262/2000 |
| surface_d5_p0.006_B4 | same_BP_radius2 | 218/2000 |
| surface_d5_p0.006_B4 | same_BP_joint | 226/2000 |
| surface_d5_p0.006_B4 | matched_cut | 353/2000 |
| surface_d5_p0.006_B4 | matched_joint | 226/2000 |
| surface_d5_p0.006_B4 | stronger_solver | 252/2000 |
| surface_d5_p0.006_B4 | strong_joint | 345/2000 |
| surface_d5_p0.006_B4 | strong_cut | 438/2000 |
| surface_d5_p0.006_B4 | strong_all_repair | 328/2000 |
| bb144_p0.015_B4 | selected_combined | 0/2000 |
| bb144_p0.015_B4 | same_BP_fixed_radius | 0/2000 |
| bb144_p0.015_B4 | same_BP_radius2 | 0/2000 |
| bb144_p0.015_B4 | same_BP_joint | 0/2000 |
| bb144_p0.015_B4 | matched_cut | 0/2000 |
| bb144_p0.015_B4 | matched_joint | 0/2000 |
| bb144_p0.015_B4 | stronger_solver | 11/2000 |
| bb144_p0.015_B4 | strong_joint | 168/2000 |
| bb144_p0.015_B4 | strong_cut | 184/2000 |
| bb144_p0.015_B4 | strong_all_repair | 100/2000 |

### 相同输入的部件配对证据

下表A−B为风险差，区间已按预定比较矩阵及两类终点保守校正；负值支持A更好。未建立差异不等于证明相同。

| 工作负载 | A 对 B | 风险差及校正区间（百分点） | 结论 |
|---|---|---|---|
| surface_d3_p0.003_B4 | selected_combined / same_BP_fixed_radius | 0 [-0.5548, 0.5548] | NOT_ESTABLISHED |
| surface_d3_p0.003_B4 | selected_combined / same_BP_joint | 0 [-1.083, 1.083] | NOT_ESTABLISHED |
| surface_d3_p0.003_B4 | selected_combined / matched_cut | -0.6 [-1.835, 0.6314] | NOT_ESTABLISHED |
| surface_d3_p0.003_B4 | strong_all_repair / strong_joint | -0.85 [-2.682, 0.9961] | NOT_ESTABLISHED |
| surface_d5_p0.006_B4 | selected_combined / same_BP_fixed_radius | -2.8 [-5.796, 0.2352] | NOT_ESTABLISHED |
| surface_d5_p0.006_B4 | selected_combined / same_BP_joint | -1 [-4.051, 2.065] | NOT_ESTABLISHED |
| surface_d5_p0.006_B4 | selected_combined / matched_cut | -7.35 [-11.23, -3.373] | A_LOWER_FAILURE_RISK |
| surface_d5_p0.006_B4 | strong_all_repair / strong_joint | -0.85 [-5.592, 3.902] | NOT_ESTABLISHED |
| bb144_p0.015_B4 | selected_combined / same_BP_fixed_radius | 0 [-0.5548, 0.5548] | NOT_ESTABLISHED |
| bb144_p0.015_B4 | selected_combined / same_BP_joint | 0 [-0.5548, 0.5548] | NOT_ESTABLISHED |
| bb144_p0.015_B4 | selected_combined / matched_cut | 0 [-0.5548, 0.5548] | NOT_ESTABLISHED |
| bb144_p0.015_B4 | strong_all_repair / strong_joint | -3.4 [-5.933, -0.8169] | A_LOWER_FAILURE_RISK |

在同一2000-ID前缀上，d3的选定K2策略与相同BP的单候选策略均为43次失败，增加候选没有展示独立准确率收益；BB选定版本身只改变BP配置，外层结构和严格成本规则保持原样。d5相对同BP切分控制的改善得到校正确认，但相对同BP联合/固定半径控制尚未建立优势。BB的统一OSD0修复控制相对统一OSD0联合控制得到校正后的收益证据，这只说明该内层设置中的修复作用，不能推广为优于最佳联合解码器。

预定角色在相同2000-ID前缀上的最低观察失败数如下，仅作描述，不据此更换冻结主配置或宣称统计最优：

| 工作负载 | 观察最低的预定新策略角色（允许并列） | 失败/2000 |
|---|---|---:|
| surface_d3_p0.003_B4 | adaptive_radius | 41 |
| surface_d5_p0.006_B4 | best_bp | 202 |
| bb144_p0.015_B4 | best_bp, multi_candidate, adaptive_radius, selected_combined, same_BP_fixed_radius | 0 |

其他角色之间的差异未因观察排名就自动被认定为显著；完整配对区间及运行代价保留在结果文件中。

如果选定版相对相同BP固定半径没有经校正的优势，则不能把其相对旧版的收益归因于增加候选。如果相对相同BP联合解码没有经校正的优势，则不能宣称修复结构优于匹配的联合控制。切分到修复的改善仅证明修复能补救该切分初值，并不自动证明它优于全局联合求解。

固定半径增加K的验证结果为阴性；逻辑类截断质量选择也没有展示足以选为主策略的优势。最终选中的三项均保留原严格成本下降规则。是否能归因于外层修复，应看相同BP、相同求解器、切分/联合/修复的配对差异；相对旧版的改善本身不能证明修复结构优于更强联合解码。没有对其他距离、物理错误率、硬件或长期运行作外推。

所有完整/部分/失败/超时/不支持及人为失败的流程自检记录保存在 `MASTER_EXECUTION_LEDGER.json`；原始阶段账本未覆盖。可重现入口见上级 `README.md`。


Execution recovery: three complete primary jobs were retained from the initial execution. The interrupted 3188-ID Tesseract prefix remains unchanged and is excluded as an independent estimate; the exact same configuration was retried on all fixed 8000 IDs. If a later stage watchdog left another incomplete Tesseract attempt, the budget-only completion rule can continue its remaining fixed IDs in a fresh process after exact checkpoint replay checks; this retains one unique result per ID and is excluded from dedicated timing. Duplicate predictions were crosschecked and never increase N. An estimated 46.6 minutes of prior active execution are charged to the five-hour planning cap; the offline interruption is excluded. The old worker termination time and uncommitted in-flight work were not recorded, so this is accounted active time with a 30-second allowance, not a certified upper bound on all historical CPU work. The resumed supervisor itself enforces its remaining wall cap. Configuration/source/binary/data locks did not change. Accuracy-run timings across execution dates are auxiliary; dedicated timing is measured entirely in fresh paired workers after recovery. See evidence/P4_recovery_plan.json and recovery_prediction_crosscheck.json.


Mechanistic follow-up (exploratory, no policy changes): failure_attribution/FINAL_ATTRIBUTION.md combines positive cost witnesses from P0/P1 and the fixed selected-policy replay. BP_QUALITY.md compares all eight predeclared BP presets on identical validation syndromes. These diagnostics do not add confirmatory samples.
