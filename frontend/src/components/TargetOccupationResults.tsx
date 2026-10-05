import { useEffect, useState } from "react";
import type { ReactNode } from "react";

type SkillGap = {
  skill_id: string;
  skill_name: string;
  relation_type: string;
  match_type: string;
  coverage: number;
  gap: number;
};

type Recommendation = {
  occupation_id: string;

  match_esco: number;
  match_market: number | null;
  market_reason?: string | null;

  canonical_skill_count: number;
  exact_match_count: number;
  semantic_match_count: number;
  missing_skill_count: number;
  average_gap: number;

  skill_gaps: SkillGap[];
};

type LearningPriorityItem = {
  rank: number;

  skill_id: string;
  skill_name: string;

  relation_type: string;
  match_type: string;

  current_coverage: number;
  residual_gap: number;

  improvement_esco: number;

  direct_improvement: number;
  semantic_spillover: number;
  semantic_dependency_ratio: number;

  rca: number | null;
  market_gap_severity: number | null;
  improvement_market: number | null;

  affected_esco_skill_count: number;
};

type LearningPriorityResult = {
  occupation_id: string;

  current_match_esco: number;
  current_match_market: number | null;

  canonical_skill_count: number;
  total_candidate_skills: number;

  ranking_criterion: string;

  ranked_skills: LearningPriorityItem[];
};

type RelatedSkill = {
  rank: number;
  skill_id: string;
  skill_name: string;

  jaccard_similarity: number;
  shared_occupation_count: number;
  union_occupation_count: number;
};

type PersonalizedSkillItem = {
  rank: number;

  skill_id: string;
  skill_name: string;

  recommendation_type: string;
  relation_type: string;

  current_coverage: number;
  residual_gap: number;

  improvement_esco: number;
  direct_improvement: number;
  semantic_spillover: number;
  semantic_dependency_ratio: number;

  rca: number | null;
  market_gap_severity: number | null;
  improvement_market: number | null;

  affected_esco_skill_count: number;

  structurally_related_skills: RelatedSkill[];

  explanation: string;
};

type PersonalizedSkillResult = {
  occupation_id: string;

  current_match_esco: number;
  current_match_market: number | null;

  canonical_skill_count: number;
  total_candidate_skills: number;

  ranking_criterion: string;

  graph_similarity_method: string;
  graph_signal_role: string;

  recommendation_count: number;

  recommendations: PersonalizedSkillItem[];
};

type RoadmapStep = {
  step: number;

  skill_id: string;
  skill_name: string;

  relation_type: string;

  match_esco_before: number;
  match_esco_after: number;

  marginal_improvement_esco: number;

  match_market_before: number | null;
  match_market_after: number | null;

  marginal_improvement_market: number | null;

  selection_reason: string;
};

type Roadmap = {
  occupation_id: string;

  selection_method: string;
  selection_strategy: string;

  initial_user_skill_count: number;

  initial_match_esco: number;
  initial_match_market: number | null;

  requested_max_steps: number;
  roadmap_step_count: number;

  roadmap_steps: RoadmapStep[];

  final_simulated_skill_count: number;

  final_match_esco: number;
  final_match_market: number | null;

  remaining_candidate_skill_count: number;
};

type TargetOccupationResponse = {
  analysis_type: "target_occupation";

  occupation: {
    occupation_id: string;
    occupation_name: string;
  };

  user_skill_count: number;

  recommendation: Recommendation;

  learning_priority: LearningPriorityResult;

  personalized_skill_recommendations:
    PersonalizedSkillResult;

  roadmap: Roadmap;

  explanations?: unknown;
};

type Props = {
  data: TargetOccupationResponse;
};

function toPercent(
  value: number | null | undefined
) {
  if (
    value === null ||
    value === undefined
  ) {
    return null;
  }

  return value * 100;
}

export default function TargetOccupationResults({
  data,
}: Props) {
  const recommendation =
    data.recommendation;

  const priorities =
    data.learning_priority?.ranked_skills ?? [];

  const personalized =
    data.personalized_skill_recommendations
      ?.recommendations ?? [];

  const roadmapSteps =
    data.roadmap?.roadmap_steps ?? [];

  const currentFit =
    toPercent(
      recommendation.match_esco
    ) ?? 0;

  const marketFit =
    toPercent(
      recommendation.match_market
    );

  const initialRoadmapMatch =
    toPercent(
      data.roadmap?.initial_match_esco
    );

  const finalRoadmapMatch =
    toPercent(
      data.roadmap?.final_match_esco
    );

  const firstThree =
    priorities.slice(0, 3);

  const remainingPriorities =
    priorities.slice(3);

  const missingSkills =
    recommendation.skill_gaps
      ?.filter(
        (skill) =>
          skill.match_type === "none"
      )
      .slice(0, 10) ?? [];

  return (
    <section
      style={{
        marginTop: "32px",
        width: "100%",
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        color: "#111827",
      }}
    >
      {/* HEADER */}

      <div
        style={{
          marginBottom: "32px",
        }}
      >
        <div
          style={{
            fontSize: "13px",
            color: "#6B7280",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: "8px",
          }}
        >
          Target career analysis
        </div>

        <h2
          style={{
            margin: 0,
            fontSize: "34px",
            lineHeight: 1.2,
            color: "#111827",
            textTransform: "capitalize",
          }}
        >
          {data.occupation.occupation_name}
        </h2>

        <p
          style={{
            marginTop: "12px",
            marginBottom: 0,
            maxWidth: "720px",
            color: "#4B5563",
            lineHeight: 1.65,
            fontSize: "16px",
          }}
        >
          See where you currently stand,
          which skills could improve your
          profile next, and how your match
          may change as you learn them.
        </p>
      </div>

      {/* STEP 1 */}

      <ResultCard>
        <SectionHeader
          eyebrow="Step 1"
          title="Your current fit"
          description="How much of this occupation's ESCO skill profile is currently covered by your selected skills."
        />

        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: "12px",
            marginTop: "28px",
            marginBottom: "26px",
          }}
        >
          <div
            style={{
              minWidth: "220px",
            }}
          >
            <div
              style={{
                fontSize: "50px",
                fontWeight: 750,
                lineHeight: 1,
                color: "#111827",
              }}
            >
              {currentFit.toFixed(1)}%
            </div>

            <CoverageBar
              percent={currentFit}
              variant="esco"
            />
          </div>

          <div
            style={{
              color: "#6B7280",
              fontWeight: 500,
            }}
          >
            current skill coverage
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(155px, 1fr))",
            gap: "14px",
          }}
        >
          <Metric
            label="Exact matches"
            value={
              recommendation.exact_match_count
            }
          />

          <Metric
            label="Related matches"
            value={
              recommendation.semantic_match_count
            }
          />

          <Metric
            label="Missing skills"
            value={
              recommendation.missing_skill_count
            }
          />

          <Metric
            label="Skills analysed"
            value={
              recommendation.canonical_skill_count
            }
          />
        </div>

        <details
          style={{
            marginTop: "20px",
          }}
        >
          <summary
            style={summaryStyle}
          >
            How is this calculated?
          </summary>

          <div
            style={detailBodyStyle}
          >
            <p>
              <strong>
                Exact matches
              </strong>{" "}
              are direct matches between
              your selected skills and the
              occupation's ESCO skills.
            </p>

            <p>
              <strong>
                Related matches
              </strong>{" "}
              are partial semantic matches.
              They can contribute to skill
              coverage but are not treated as
              exact matches.
            </p>

            <p>
              <strong>
                Missing skills
              </strong>{" "}
              are required skills for which
              the system found no current
              match.
            </p>
          </div>
        </details>
      </ResultCard>

      {/* STEP 2 */}

      <ResultCard>
        <SectionHeader
          eyebrow="Step 2"
          title="Skills to focus on next"
          description="These skills currently have the largest estimated impact on your ESCO skill coverage."
        />

        <div
          style={{
            display: "grid",
            gap: "14px",
            marginTop: "24px",
          }}
        >
          {firstThree.map(
            (item) => {
              const personalizedItem =
                personalized.find(
                  (x) =>
                    x.skill_id ===
                    item.skill_id
                );

              const topRelated =
                personalizedItem
                  ?.structurally_related_skills
                  ?.[0];

              return (
                <div
                  key={item.skill_id}
                  style={{
                    padding: "20px",
                    borderRadius: "12px",
                    background: "#F9FAFB",
                    border:
                      "1px solid #E5E7EB",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent:
                        "space-between",
                      alignItems:
                        "flex-start",
                      gap: "18px",
                      flexWrap: "wrap",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          color:
                            "#6B7280",
                          fontSize:
                            "13px",
                          fontWeight:
                            600,
                          marginBottom:
                            "5px",
                        }}
                      >
                        Priority #
                        {item.rank}
                      </div>

                      <strong
                        style={{
                          fontSize:
                            "18px",
                          color:
                            "#111827",
                        }}
                      >
                        {
                          item.skill_name
                        }
                      </strong>
                    </div>

                    <div
                      style={{
                        background:
                          "#EEF2FF",
                        color:
                          "#4338CA",
                        padding:
                          "7px 12px",
                        borderRadius:
                          "999px",
                        fontWeight:
                          700,
                        fontSize:
                          "14px",
                        whiteSpace:
                          "nowrap",
                      }}
                    >
                      +
                      {(
                        item.improvement_esco *
                        100
                      ).toFixed(2)}{" "}
                      pp
                    </div>
                  </div>

                  <p
                    style={{
                      margin:
                        "12px 0 0 0",
                      color:
                        "#4B5563",
                      lineHeight: 1.6,
                    }}
                  >
                    This skill is estimated
                    to increase your current
                    ESCO coverage by{" "}
                    <strong>
                      {(
                        item.improvement_esco *
                        100
                      ).toFixed(2)}{" "}
                      percentage points
                    </strong>
                    .
                  </p>

                  <details
                    style={{
                      marginTop:
                        "14px",
                    }}
                  >
                    <summary
                      style={
                        summaryStyle
                      }
                    >
                      Why this skill?
                    </summary>

                    <div
                      style={
                        detailBodyStyle
                      }
                    >
                      {item.current_coverage ===
                      0 ? (
                        <p>
                          This required skill
                          is currently not
                          covered by your
                          selected profile.
                        </p>
                      ) : (
                        <p>
                          Your current profile
                          provides{" "}
                          <strong>
                            {(
                              item.current_coverage *
                              100
                            ).toFixed(
                              1
                            )}
                            %
                          </strong>{" "}
                          estimated coverage
                          for this skill, so a
                          gap still remains.
                        </p>
                      )}

                      {item
                        .affected_esco_skill_count >
                        1 && (
                        <p>
                          Adding this skill
                          may also improve
                          coverage of{" "}
                          <strong>
                            {
                              item.affected_esco_skill_count
                            }
                          </strong>{" "}
                          ESCO skills in the
                          current matching
                          model.
                        </p>
                      )}

                      {topRelated && (
                        <p>
                          It also appears in
                          similar ESCO
                          occupational
                          contexts to{" "}
                          <strong>
                            {
                              topRelated.skill_name
                            }
                          </strong>
                          . This graph
                          information is
                          supporting context
                          only and does not
                          determine the
                          ranking.
                        </p>
                      )}
                    </div>
                  </details>
                </div>
              );
            }
          )}
        </div>

        {remainingPriorities.length >
          0 && (
          <details
            style={{
              marginTop: "18px",
            }}
          >
            <summary
              style={summaryStyle}
            >
              Show more recommended skills
            </summary>

            <div
              style={{
                marginTop: "12px",
                display: "grid",
                gap: "8px",
              }}
            >
              {remainingPriorities.map(
                (item) => (
                  <div
                    key={
                      item.skill_id
                    }
                    style={{
                      padding:
                        "12px 14px",
                      borderRadius:
                        "8px",
                      border:
                        "1px solid #E5E7EB",
                      display:
                        "flex",
                      justifyContent:
                        "space-between",
                      gap: "12px",
                    }}
                  >
                    <span>
                      {
                        item.skill_name
                      }
                    </span>

                    <strong>
                      +
                      {(
                        item.improvement_esco *
                        100
                      ).toFixed(2)}{" "}
                      pp
                    </strong>
                  </div>
                )
              )}
            </div>
          </details>
        )}
      </ResultCard>

      {/* STEP 3 */}

      <ResultCard>
        <SectionHeader
          eyebrow="Step 3"
          title="Your learning roadmap"
          description="A sequential simulation of how your ESCO coverage changes as each suggested skill is added."
        />

        {initialRoadmapMatch !== null &&
          finalRoadmapMatch !==
            null && (
            <div
              style={{
                marginTop: "24px",
                marginBottom: "24px",
                padding: "20px",
                borderRadius: "12px",
                background:
                  "#F0FDF4",
                border:
                  "1px solid #BBF7D0",
              }}
            >
              <div
                style={{
                  color:
                    "#166534",
                  fontSize:
                    "13px",
                  fontWeight:
                    700,
                  textTransform:
                    "uppercase",
                  letterSpacing:
                    "0.05em",
                }}
              >
                Simulated progression
              </div>

              <div
                style={{
                  marginTop: "8px",
                  fontSize:
                    "26px",
                  color:
                    "#15803D",
                }}
              >
                {initialRoadmapMatch.toFixed(
                  1
                )}
                %
                {" → "}
                <strong>
                  {finalRoadmapMatch.toFixed(
                    1
                  )}
                  %
                </strong>
              </div>

              <div
                style={{
                  marginTop: "5px",
                  color:
                    "#166534",
                  fontSize:
                    "14px",
                }}
              >
                after{" "}
                {
                  roadmapSteps.length
                }{" "}
                simulated learning
                steps
              </div>
            </div>
          )}

        <div
          style={{
            display: "grid",
            gap: "10px",
          }}
        >
          {roadmapSteps.map(
            (step) => {
              const before =
                toPercent(
                  step.match_esco_before
                );

              const after =
                toPercent(
                  step.match_esco_after
                );

              return (
                <div
                  key={step.step}
                  style={{
                    padding:
                      "16px 18px",
                    borderRadius:
                      "10px",
                    border:
                      "1px solid #E5E7EB",
                    display:
                      "flex",
                    alignItems:
                      "center",
                    gap: "16px",
                  }}
                >
                  <div
                    style={{
                      width: "30px",
                      height:
                        "30px",
                      borderRadius:
                        "50%",
                      background:
                        "#F3F4F6",
                      display:
                        "flex",
                      alignItems:
                        "center",
                      justifyContent:
                        "center",
                      fontWeight:
                        700,
                      fontSize:
                        "13px",
                      flexShrink: 0,
                    }}
                  >
                    {step.step}
                  </div>

                  <div
                    style={{
                      flexGrow: 1,
                    }}
                  >
                    <strong>
                      {
                        step.skill_name
                      }
                    </strong>
                  </div>

                  {before !== null &&
                    after !==
                      null && (
                      <div
                        style={{
                          color:
                            "#4B5563",
                          fontSize:
                            "14px",
                          whiteSpace:
                            "nowrap",
                        }}
                      >
                        {before.toFixed(
                          1
                        )}
                        %
                        {" → "}
                        <strong
                          style={{
                            color:
                              "#111827",
                          }}
                        >
                          {after.toFixed(
                            1
                          )}
                          %
                        </strong>
                      </div>
                    )}
                </div>
              );
            }
          )}
        </div>

        <div
          style={{
            marginTop: "18px",
            color: "#6B7280",
            fontSize: "13px",
            lineHeight: 1.55,
          }}
        >
          The roadmap is greedy and
          sequential: after each simulated
          skill acquisition, priorities are
          recalculated. It is not presented
          as a globally optimal learning
          path.
        </div>
      </ResultCard>

      {/* STEP 4 */}

      <ResultCard>
        <SectionHeader
          eyebrow="Step 4"
          title="Labor-market evidence"
          description="A separate view of the requirements for which labor-market evidence is available."
        />

        <div
          style={{
            marginTop: "24px",
          }}
        >
          {marketFit === null ? (
            <div
              style={{
                padding: "16px",
                background:
                  "#F9FAFB",
                borderRadius:
                  "10px",
                border:
                  "1px solid #E5E7EB",
                color:
                  "#4B5563",
              }}
            >
              <strong
                style={{
                  color:
                    "#111827",
                }}
              >
                Market score not
                available
              </strong>

              <div
                style={{
                  marginTop:
                    "6px",
                  lineHeight: 1.55,
                }}
              >
                {recommendation.market_reason ||
                  "There is not enough labor-market evidence available for this occupation."}
              </div>
            </div>
          ) : (
            <>
              <div
                style={{
                  fontSize:
                    "38px",
                  fontWeight:
                    750,
                  color:
                    "#111827",
                }}
              >
                {marketFit.toFixed(
                  1
                )}
                %
              </div>

              <CoverageBar
                percent={marketFit}
                variant="market"
              />

              <p
                style={{
                  marginTop: "10px",
                  marginBottom: 0,
                  color:
                    "#4B5563",
                  lineHeight: 1.65,
                  maxWidth:
                    "700px",
                }}
              >
                This score reflects how
                well your selected skills
                cover the requirements for
                which occupation-specific
                labor-market evidence is
                available.
              </p>

              {marketFit === 0 && (
                <div
                  style={{
                    marginTop:
                      "16px",
                    padding:
                      "14px",
                    background:
                      "#FFFBEB",
                    border:
                      "1px solid #FDE68A",
                    borderRadius:
                      "10px",
                    color:
                      "#92400E",
                    lineHeight:
                      1.55,
                  }}
                >
                  Market evaluation is
                  available, but your
                  selected skills currently
                  provide no measured
                  coverage of those
                  market-supported
                  requirements.
                </div>
              )}
            </>
          )}
        </div>

        <div
          style={{
            marginTop: "16px",
            color: "#6B7280",
            fontSize: "13px",
          }}
        >
          Labor-market evidence is
          supplementary and is not combined
          with the ESCO skill coverage
          score.
        </div>
      </ResultCard>

      {/* METHODOLOGY */}

      <details
        style={{
          marginTop: "28px",
          padding: "20px",
          background: "#F9FAFB",
          borderRadius: "12px",
          border:
            "1px solid #E5E7EB",
        }}
      >
        <summary
          style={{
            cursor: "pointer",
            fontWeight: 650,
            color: "#374151",
            fontSize: "16px",
          }}
        >
          How the recommendations were
          generated
        </summary>

        <div
          style={{
            marginTop: "20px",
            color: "#4B5563",
            fontSize: "14px",
            lineHeight: 1.65,
          }}
        >
          <p>
            Skills are ranked by their
            estimated{" "}
            <strong>
              ImprovementESCO
            </strong>
            : the increase in ESCO skill
            coverage expected if that skill
            is added to the user's profile.
          </p>

          <p>
            Labor-market evidence is shown
            separately and does not change
            the main recommendation ranking.
          </p>

          <p>
            Graph-based relatedness is used
            only as explanatory context. It
            does not determine which skill
            is ranked first.
          </p>

          <details
            style={{
              marginTop: "18px",
            }}
          >
            <summary
              style={summaryStyle}
            >
              View technical evidence
            </summary>

            <div
              style={{
                marginTop: "14px",
                display: "grid",
                gap: "12px",
              }}
            >
              {personalized.map(
                (item) => {
                  const topRelated =
                    item
                      .structurally_related_skills
                      ?.[0];

                  return (
                    <div
                      key={
                        item.skill_id
                      }
                      style={{
                        padding:
                          "14px",
                        background:
                          "#FFFFFF",
                        border:
                          "1px solid #E5E7EB",
                        borderRadius:
                          "8px",
                      }}
                    >
                      <strong
                        style={{
                          color:
                            "#111827",
                        }}
                      >
                        {
                          item.skill_name
                        }
                      </strong>

                      <div
                        style={{
                          marginTop:
                            "10px",
                          display:
                            "grid",
                          gap: "5px",
                        }}
                      >
                        <div>
                          ImprovementESCO:{" "}
                          <strong>
                            {(
                              item.improvement_esco *
                              100
                            ).toFixed(
                              4
                            )}
                            pp
                          </strong>
                        </div>

                        <div>
                          Direct
                          contribution:{" "}
                          {(
                            item.direct_improvement *
                            100
                          ).toFixed(
                            4
                          )}
                          pp
                        </div>

                        <div>
                          Semantic
                          spillover:{" "}
                          {(
                            item.semantic_spillover *
                            100
                          ).toFixed(
                            4
                          )}
                          pp
                        </div>

                        {item.rca !==
                          null && (
                          <div>
                            RCA:{" "}
                            {item.rca.toFixed(
                              4
                            )}
                          </div>
                        )}

                        {item.market_gap_severity !==
                          null && (
                          <div>
                            Market gap
                            severity:{" "}
                            {item.market_gap_severity.toFixed(
                              4
                            )}
                          </div>
                        )}

                        {topRelated && (
                          <>
                            <div>
                              Most
                              structurally
                              related skill:{" "}
                              {
                                topRelated.skill_name
                              }
                            </div>

                            <div>
                              Jaccard
                              similarity:{" "}
                              {(
                                topRelated.jaccard_similarity *
                                100
                              ).toFixed(
                                2
                              )}
                              %
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          </details>

          {missingSkills.length >
            0 && (
            <details
              style={{
                marginTop: "16px",
              }}
            >
              <summary
                style={summaryStyle}
              >
                View example missing
                skills
              </summary>

              <ul
                style={{
                  marginTop:
                    "12px",
                }}
              >
                {missingSkills.map(
                  (skill) => (
                    <li
                      key={
                        skill.skill_id
                      }
                      style={{
                        marginBottom:
                          "6px",
                      }}
                    >
                      {
                        skill.skill_name
                      }
                    </li>
                  )
                )}
              </ul>
            </details>
          )}
        </div>
      </details>
    </section>
  );
}

function CoverageBar({
  percent,
  variant
}: {
  percent: number;
  variant: "esco" | "market";
}) {
  const safePercent = Math.min(
    100,
    Math.max(0, percent)
  );

  const [displayedPercent, setDisplayedPercent] =
    useState(0);

  useEffect(() => {
    setDisplayedPercent(0);

    const frame = requestAnimationFrame(() => {
      setDisplayedPercent(safePercent);
    });

    return () => cancelAnimationFrame(frame);
  }, [safePercent]);

  const fillColor =
    variant === "esco"
      ? "#4F46E5"
      : "#0F766E";

  const trackColor =
    variant === "esco"
      ? "#E0E7FF"
      : "#CCFBF1";

  return (
    <div
      style={{
        width: "100%",
        height: "8px",
        background: trackColor,
        borderRadius: "999px",
        overflow: "hidden",
        marginTop: "10px"
      }}
      role="progressbar"
      aria-label={
        variant === "esco"
          ? "Current ESCO skill coverage"
          : "Market-supported skill coverage"
      }
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={safePercent}
    >
      <div
        style={{
          width: `${displayedPercent}%`,
          height: "100%",
          background: fillColor,
          borderRadius: "999px",
          transition:
            "width 650ms cubic-bezier(0.22, 1, 0.36, 1)"
        }}
      />
    </div>
  );
}

function ResultCard({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div
      style={{
        border:
          "1px solid #E5E7EB",
        borderRadius: "16px",
        padding: "30px",
        marginBottom: "24px",
        background: "#FFFFFF",
        boxShadow:
          "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      {children}
    </div>
  );
}

function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <div
        style={{
          fontSize: "13px",
          fontWeight: 700,
          color: "#6B7280",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginBottom: "8px",
        }}
      >
        {eyebrow}
      </div>

      <h3
        style={{
          margin: 0,
          fontSize: "24px",
          color: "#111827",
          fontWeight: 700,
        }}
      >
        {title}
      </h3>

      <p
        style={{
          marginTop: "8px",
          marginBottom: 0,
          lineHeight: 1.6,
          color: "#4B5563",
          fontSize: "15px",
          maxWidth: "720px",
        }}
      >
        {description}
      </p>
    </div>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div
      style={{
        padding: "16px",
        borderRadius: "12px",
        background: "#F9FAFB",
        border:
          "1px solid #E5E7EB",
      }}
    >
      <div
        style={{
          fontSize: "14px",
          color: "#4B5563",
          fontWeight: 500,
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop: "8px",
          fontSize: "24px",
          fontWeight: 700,
          color: "#111827",
        }}
      >
        {value}
      </div>
    </div>
  );
}

const summaryStyle = {
  cursor: "pointer",
  fontWeight: 600,
  color: "#374151",
  fontSize: "14px",
};

const detailBodyStyle = {
  marginTop: "12px",
  color: "#4B5563",
  lineHeight: 1.65,
  fontSize: "14px",
};