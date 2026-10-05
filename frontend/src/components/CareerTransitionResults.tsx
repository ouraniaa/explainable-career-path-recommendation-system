import { useEffect, useState } from "react";
import type { ReactNode } from "react";

type SkillGap = {
  skill_id: string;
  skill_name: string;
  relation_type: string;
  match_type: string;
  best_user_skill_id: string | null;
  best_user_skill_name: string | null;
  coverage: number;
  gap: number;
};

type MarketDetail = {
  skill_id: string;
  skill_name: string;
  rca: number;
  coverage: number;
  weighted_coverage: number;
};

type CareerTransitionRecommendation = {
  rank: number;

  occupation_id: string;
  occupation_name: string;
  isco_group?: string | null;

  structural_rank: number;
  occupation_similarity: number;
  shared_skill_count: number;
  union_skill_count: number;
  candidate_skill_count: number;

  match_esco: number;
  match_market: number | null;
  market_reason?: string | null;
  market_details?: MarketDetail[];

  canonical_skill_count: number;
  exact_match_count: number;
  semantic_match_count: number;
  missing_skill_count: number;

  average_gap: number;

  skill_gaps: SkillGap[];
};

type CareerTransitionResult = {
  mode: "career_transition";

  current_occupation_id: string;
  current_occupation_name: string;
  current_occupation_isco_group?: string | null;

  candidate_pool_definition: string;
  structural_similarity_method: string;
  structural_filtering_role: string;

  final_ranking_criterion: string;

  structural_top_n: number;
  recommendation_top_n: number;
  evaluated_candidate_count: number;

  recommendations: CareerTransitionRecommendation[];
};

type CareerTransitionResponse = {
  analysis_type: "career_paths";
  mode: "career_transition";

  current_occupation_id: string;
  user_skill_count: number;

  career_result: CareerTransitionResult;

  explanation?: unknown;
};

type Props = {
  data: CareerTransitionResponse;
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

function formatLabel(text: string) {
  if (!text) {
    return text;
  }

  return text.charAt(0).toUpperCase() + text.slice(1);
}

export default function CareerTransitionResults({
  data
}: Props) {
  const result = data.career_result;

  return (
    <section
      style={{
        marginTop: "32px",
        width: "100%",
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        color: "#111827"
      }}
    >
      {/* HEADER */}

      <div
        style={{
          marginBottom: "32px"
        }}
      >
        <div
          style={{
            fontSize: "13px",
            color: "#6B7280",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: "8px"
          }}
        >
          Career transition
        </div>

        <h2
          style={{
            margin: 0,
            fontSize: "34px",
            lineHeight: 1.2,
            color: "#111827"
          }}
        >
          Possible next career directions
        </h2>

        <p
          style={{
            marginTop: "12px",
            marginBottom: 0,
            maxWidth: "720px",
            color: "#4B5563",
            lineHeight: 1.65,
            fontSize: "16px"
          }}
        >
          Starting from your current occupation,
          the system first identifies structurally
          related occupations and then compares
          them with your current skill profile.
        </p>
      </div>

      {/* CURRENT OCCUPATION */}

      <ResultCard>
        <SectionHeader
          eyebrow="Starting point"
          title="Your current occupation"
          description="This role is used to identify structurally related career directions."
        />

        <div
          style={{
            marginTop: "20px",
            padding: "18px",
            borderRadius: "12px",
            background: "var(--primary-soft)",
            border: "1px solid #C7D2FE"
          }}
        >
          <strong
            style={{
              display: "block",
              fontSize: "18px",
              color: "#312E81",
              textTransform: "capitalize"
            }}
          >
            {result.current_occupation_name}
          </strong>

          {result.current_occupation_isco_group && (
            <div
              style={{
                marginTop: "5px",
                fontSize: "13px",
                color: "#6366F1"
              }}
            >
              ISCO {result.current_occupation_isco_group}
            </div>
          )}
        </div>
      </ResultCard>

      {/* RECOMMENDATIONS */}

      <div
        style={{
          marginTop: "24px",
          marginBottom: "14px"
        }}
      >
        <div
          style={{
            fontSize: "13px",
            color: "#6B7280",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            marginBottom: "6px"
          }}
        >
          Suggested directions
        </div>

        <h3
          style={{
            margin: 0,
            fontSize: "24px"
          }}
        >
          Careers that fit your current skills
        </h3>

        <p
          style={{
            marginTop: "8px",
            color: "#4B5563",
            lineHeight: 1.6
          }}
        >
          These occupations come from the
          structural candidate set and are
          displayed in order of current ESCO
          skill fit.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gap: "20px"
        }}
      >
        {result.recommendations.map(
          (recommendation) => {
            const currentFit =
              toPercent(
                recommendation.match_esco
              ) ?? 0;

            const marketFit =
              toPercent(
                recommendation.match_market
              );

            const marketDetails =
              recommendation.market_details ?? [];

            const coveredMarketSkills =
              marketDetails.filter(
                (skill) => skill.coverage > 0
              );

            const uncoveredMarketSkills =
              marketDetails.filter(
                (skill) => skill.coverage <= 0
              );

            const structuralPercent =
              toPercent(
                recommendation.occupation_similarity
              ) ?? 0;

            const relatedMatches =
              recommendation.skill_gaps
                .filter(
                  (skill) =>
                    skill.match_type === "semantic"
                )
                .sort(
                  (a, b) =>
                    b.coverage - a.coverage
                );

            const visibleRelatedMatches =
              relatedMatches.slice(0, 5);

            const topMissingSkills =
              recommendation.skill_gaps
                .filter(
                  (skill) =>
                    skill.match_type === "none"
                )
                .slice(0, 5);

            return (
              <ResultCard
                key={recommendation.occupation_id}
              >
                {/* TOP ROW */}

                <div
                  style={{
                    display: "flex",
                    justifyContent:
                      "space-between",
                    alignItems:
                      "flex-start",
                    gap: "20px",
                    flexWrap: "wrap"
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: "13px",
                        fontWeight: 700,
                        color: "#6B7280",
                        textTransform:
                          "uppercase",
                        letterSpacing:
                          "0.05em",
                        marginBottom: "6px"
                      }}
                    >
                      Recommendation #
                      {recommendation.rank}
                    </div>

                    <h3
                      style={{
                        margin: 0,
                        fontSize: "24px",
                        textTransform:
                          "capitalize"
                      }}
                    >
                      {formatLabel(
                        recommendation.occupation_name
                      )}
                    </h3>

                    {recommendation.isco_group && (
                      <div
                        style={{
                          marginTop: "6px",
                          fontSize: "13px",
                          color: "#6B7280"
                        }}
                      >
                        ISCO{" "}
                        {
                          recommendation.isco_group
                        }
                      </div>
                    )}
                  </div>

                  <div
                    style={{
                      textAlign: "right"
                    }}
                  >
                    <div
                      style={{
                        fontSize: "13px",
                        color: "#6B7280",
                        fontWeight: 600,
                        marginBottom: "4px"
                      }}
                    >
                      Current fit
                    </div>

                    <div
                      style={{
                        fontSize: "34px",
                        fontWeight: 750,
                        color: "#111827",
                        lineHeight: 1
                      }}
                    >
                      {currentFit.toFixed(1)}%
                    </div>

                    <CoverageBar
                      percent={currentFit}
                      variant="esco"
                    />
                  </div>
                </div>

                {/* MATCH METRICS */}

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(auto-fit, minmax(150px, 1fr))",
                    gap: "14px",
                    marginTop: "24px"
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

                {/* WHY THIS TRANSITION */}

                <details
                  style={{
                    marginTop: "20px"
                  }}
                >
                  <summary
                    style={summaryStyle}
                  >
                    Why does this career appear?
                  </summary>

                  <div
                    style={detailBodyStyle}
                  >
                    <p>
                      This occupation was first
                      included because its ESCO
                      skill profile has structural
                      overlap with your current
                      occupation.
                    </p>

                    <p>
                      It is then positioned in the
                      displayed recommendation list
                      according to your{" "}
                      <strong>
                        current ESCO skill fit
                      </strong>
                      .
                    </p>

                    <p>
                      Structural similarity helps
                      generate candidates, but it
                      does not decide the final
                      recommendation order.
                    </p>
                  </div>
                </details>

                {/* MARKET */}

                <div
                  style={{
                    marginTop: "20px",
                    padding: "18px",
                    borderRadius: "12px",
                    background: "#F9FAFB",
                    border:
                      "1px solid #E5E7EB"
                  }}
                >
                  <div
                    style={{
                      fontSize: "13px",
                      fontWeight: 700,
                      color: "#6B7280",
                      textTransform:
                        "uppercase",
                      letterSpacing:
                        "0.05em",
                      marginBottom: "8px"
                    }}
                  >
                    Labor-market evidence
                  </div>

                  {marketFit === null ? (
                    <div
                      style={{
                        color: "#4B5563",
                        lineHeight: 1.6
                      }}
                    >
                      <strong
                        style={{
                          display: "block",
                          color: "#111827",
                          marginBottom: "5px"
                        }}
                      >
                        Market score not available
                      </strong>

                      {recommendation.market_reason ||
                        "There is not enough occupation-specific market evidence to calculate this score."}
                    </div>
                  ) : (
                    <>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "baseline",
                          gap: "10px",
                          flexWrap: "wrap"
                        }}
                      >
                        <div
                          style={{
                            fontSize: "30px",
                            fontWeight: 750,
                            color: "#111827"
                          }}
                        >
                          {marketFit.toFixed(1)}%
                        </div>

                        <div
                          style={{
                            color:
                              marketFit === 0
                                ? "#92400E"
                                : "#4B5563",
                            fontSize: "14px",
                            fontWeight: 600
                          }}
                        >
                          {marketFit === 0
                            ? "No current market-supported overlap"
                            : "Market-supported skill coverage"}
                        </div>
                      </div>

                      <CoverageBar
                        percent={marketFit}
                        variant="market"
                      />

                      <p
                        style={{
                          marginTop: "8px",
                          marginBottom: 0,
                          color: "#4B5563",
                          lineHeight: 1.6
                        }}
                      >
                        This score reflects how
                        well your selected skills
                        cover the occupation
                        requirements for which
                        labor-market evidence is
                        available. It is separate
                        from the main ESCO fit and
                        does not change the final
                        transition ranking.
                      </p>

                      {marketFit === 0 && (
                        <div
                          style={{
                            marginTop: "14px",
                            padding: "12px 14px",
                            background:
                              "#FFFBEB",
                            border:
                              "1px solid #FDE68A",
                            borderRadius:
                              "8px",
                            color: "#92400E",
                            fontSize: "14px",
                            lineHeight: 1.55
                          }}
                        >
                          Your selected skills
                          currently provide no
                          measured coverage of
                          the market-supported
                          requirements below.
                          This does not mean that
                          the occupation has no
                          labor-market demand.
                        </div>
                      )}

                      {marketDetails.length > 0 && (
                        <details
                          style={{
                            marginTop: "16px"
                          }}
                        >
                          <summary
                            style={summaryStyle}
                          >
                            See the market-supported
                            skills behind this score
                          </summary>

                          <div
                            style={{
                              marginTop: "14px"
                            }}
                          >
                            <div
                              style={{
                                display: "grid",
                                gridTemplateColumns:
                                  "repeat(auto-fit, minmax(150px, 1fr))",
                                gap: "10px",
                                marginBottom: "14px"
                              }}
                            >
                              <SmallMetric
                                label="Market-supported skills"
                                value={marketDetails.length}
                              />

                              <SmallMetric
                                label="With measured coverage"
                                value={
                                  coveredMarketSkills.length
                                }
                              />

                              <SmallMetric
                                label="With no measured coverage"
                                value={
                                  uncoveredMarketSkills.length
                                }
                              />
                            </div>

                            <div
                              style={{
                                display: "grid",
                                gap: "10px"
                              }}
                            >
                              {marketDetails.map(
                                (skill) => {
                                  const coverage =
                                    toPercent(
                                      skill.coverage
                                    ) ?? 0;

                                  const isCovered =
                                    skill.coverage > 0;

                                  return (
                                    <div
                                      key={
                                        skill.skill_id
                                      }
                                      style={{
                                        padding:
                                          "14px 16px",
                                        borderRadius:
                                          "10px",
                                        background:
                                          "#FFFFFF",
                                        border:
                                          "1px solid #E5E7EB"
                                      }}
                                    >
                                      <div
                                        style={{
                                          display:
                                            "flex",
                                          justifyContent:
                                            "space-between",
                                          alignItems:
                                            "flex-start",
                                          gap: "14px",
                                          flexWrap:
                                            "wrap"
                                        }}
                                      >
                                        <strong
                                          style={{
                                            fontSize:
                                              "15px"
                                          }}
                                        >
                                          {formatLabel(
                                            skill.skill_name
                                          )}
                                        </strong>

                                        <span
                                          style={{
                                            display:
                                              "inline-flex",
                                            padding:
                                              "4px 9px",
                                            borderRadius:
                                              "999px",
                                            fontSize:
                                              "12px",
                                            fontWeight:
                                              700,
                                            background:
                                              isCovered
                                                ? "#F0FDF4"
                                                : "#F3F4F6",
                                            color:
                                              isCovered
                                                ? "#166534"
                                                : "#4B5563",
                                            border:
                                              isCovered
                                                ? "1px solid #BBF7D0"
                                                : "1px solid #E5E7EB"
                                          }}
                                        >
                                          {isCovered
                                            ? `${coverage.toFixed(
                                                1
                                              )}% coverage`
                                            : "No current coverage"}
                                        </span>
                                      </div>

                                      <p
                                        style={{
                                          margin:
                                            "9px 0 0",
                                          color:
                                            "#4B5563",
                                          fontSize:
                                            "14px",
                                          lineHeight:
                                            1.55
                                        }}
                                      >
                                        {isCovered
                                          ? "Your selected profile contributes measurable coverage to this market-supported requirement."
                                          : "Your selected profile currently provides no measured coverage for this market-supported requirement."}
                                      </p>

                                      <details
                                        style={{
                                          marginTop:
                                            "9px"
                                        }}
                                      >
                                        <summary
                                          style={{
                                            ...summaryStyle,
                                            fontSize:
                                              "13px"
                                          }}
                                        >
                                          Technical evidence
                                        </summary>

                                        <div
                                          style={{
                                            marginTop:
                                              "8px",
                                            padding:
                                              "10px 12px",
                                            borderRadius:
                                              "8px",
                                            background:
                                              "#F8FAFC",
                                            color:
                                              "#4B5563",
                                            fontSize:
                                              "13px",
                                            lineHeight:
                                              1.55
                                          }}
                                        >
                                          <div>
                                            RCA:{" "}
                                            <strong>
                                              {skill.rca.toFixed(
                                                4
                                              )}
                                            </strong>
                                          </div>

                                          <div
                                            style={{
                                              marginTop:
                                                "4px"
                                            }}
                                          >
                                            Weighted contribution:{" "}
                                            <strong>
                                              {skill.weighted_coverage.toFixed(
                                                4
                                              )}
                                            </strong>
                                          </div>

                                          <p
                                            style={{
                                              margin:
                                                "8px 0 0"
                                            }}
                                          >
                                            RCA is the
                                            occupation-specific
                                            market weight used
                                            by the model. It
                                            reflects the
                                            relative
                                            concentration of
                                            this skill in the
                                            available postings
                                            for this occupation;
                                            it is not a direct
                                            measure of total
                                            job demand.
                                          </p>
                                        </div>
                                      </details>
                                    </div>
                                  );
                                }
                              )}
                            </div>
                          </div>
                        </details>
                      )}
                    </>
                  )}
                </div>

                {/* SEMANTIC / RELATED MATCHES */}

                {visibleRelatedMatches.length >
                  0 && (
                  <details
                    style={{
                      marginTop: "18px"
                    }}
                  >
                    <summary
                      style={summaryStyle}
                    >
                      See how your existing skills
                      contribute
                    </summary>

                    <div
                      style={{
                        display: "grid",
                        gap: "10px",
                        marginTop: "14px"
                      }}
                    >
                      {visibleRelatedMatches.map(
                        (skill) => {
                          const coverage =
                            toPercent(
                              skill.coverage
                            ) ?? 0;

                          return (
                            <div
                              key={
                                skill.skill_id
                              }
                              style={{
                                padding:
                                  "14px 16px",
                                borderRadius:
                                  "10px",
                                background:
                                  "#F8FAFC",
                                border:
                                  "1px solid #E2E8F0"
                              }}
                            >
                              <div
                                style={{
                                  display:
                                    "flex",
                                  justifyContent:
                                    "space-between",
                                  alignItems:
                                    "flex-start",
                                  gap: "14px",
                                  flexWrap:
                                    "wrap"
                                }}
                              >
                                <strong
                                  style={{
                                    fontSize:
                                      "15px"
                                  }}
                                >
                                  {formatLabel(
                                    skill.skill_name
                                  )}
                                </strong>

                                <span
                                  style={{
                                    padding:
                                      "4px 9px",
                                    borderRadius:
                                      "999px",
                                    background:
                                      "#EEF2FF",
                                    color:
                                      "#4338CA",
                                    fontSize:
                                      "12px",
                                    fontWeight:
                                      700
                                  }}
                                >
                                  {coverage.toFixed(
                                    1
                                  )}
                                  % partial
                                  coverage
                                </span>
                              </div>

                              {skill.best_user_skill_name ? (
                                <p
                                  style={{
                                    margin:
                                      "9px 0 0",
                                    color:
                                      "#4B5563",
                                    fontSize:
                                      "14px",
                                    lineHeight:
                                      1.55
                                  }}
                                >
                                  Your selected
                                  skill{" "}
                                  <strong>
                                    {formatLabel(
                                      skill.best_user_skill_name
                                    )}
                                  </strong>{" "}
                                  is the closest
                                  semantic match
                                  found for this
                                  required skill.
                                </p>
                              ) : (
                                <p
                                  style={{
                                    margin:
                                      "9px 0 0",
                                    color:
                                      "#4B5563",
                                    fontSize:
                                      "14px",
                                    lineHeight:
                                      1.55
                                  }}
                                >
                                  This required
                                  skill receives
                                  partial semantic
                                  coverage from
                                  your selected
                                  profile.
                                </p>
                              )}

                              <p
                                style={{
                                  margin:
                                    "8px 0 0",
                                  color:
                                    "#6B7280",
                                  fontSize:
                                    "13px",
                                  lineHeight:
                                    1.5
                                }}
                              >
                                Partial semantic
                                coverage contributes
                                to the ESCO fit, but
                                it does not mean that
                                you already possess
                                this required skill.
                              </p>
                            </div>
                          );
                        }
                      )}

                      {relatedMatches.length >
                        visibleRelatedMatches.length && (
                        <div
                          style={{
                            color:
                              "#6B7280",
                            fontSize:
                              "13px"
                          }}
                        >
                          Showing{" "}
                          {
                            visibleRelatedMatches.length
                          }{" "}
                          of{" "}
                          {
                            relatedMatches.length
                          }{" "}
                          related matches.
                        </div>
                      )}
                    </div>
                  </details>
                )}

                {/* MISSING SKILLS */}

                {topMissingSkills.length >
                  0 && (
                  <details
                    style={{
                      marginTop: "20px"
                    }}
                  >
                    <summary
                      style={summaryStyle}
                    >
                      Skills you may still need
                    </summary>

                    <div
                      style={{
                        marginTop: "12px"
                      }}
                    >
                      <ul
                        style={{
                          margin: 0
                        }}
                      >
                        {topMissingSkills.map(
                          (skill) => (
                            <li
                              key={
                                skill.skill_id
                              }
                              style={{
                                marginBottom:
                                  "6px"
                              }}
                            >
                              {
                                skill.skill_name
                              }
                            </li>
                          )
                        )}
                      </ul>

                      {recommendation.missing_skill_count >
                        topMissingSkills.length && (
                        <p
                          style={{
                            marginBottom: 0,
                            marginTop:
                              "10px",
                            color:
                              "#6B7280",
                            fontSize:
                              "13px"
                          }}
                        >
                          Showing{" "}
                          {
                            topMissingSkills.length
                          }{" "}
                          of{" "}
                          {
                            recommendation.missing_skill_count
                          }{" "}
                          skills with no
                          current match.
                        </p>
                      )}
                    </div>
                  </details>
                )}

                {/* TECHNICAL DETAILS */}

                <details
                  style={{
                    marginTop: "18px"
                  }}
                >
                  <summary
                    style={summaryStyle}
                  >
                    View structural evidence
                  </summary>

                  <div
                    style={{
                      marginTop: "14px",
                      padding: "16px",
                      borderRadius: "10px",
                      background: "#F9FAFB",
                      border:
                        "1px solid #E5E7EB"
                    }}
                  >
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns:
                          "repeat(auto-fit, minmax(145px, 1fr))",
                        gap: "12px"
                      }}
                    >
                      <Metric
                        label="Structural rank"
                        value={
                          recommendation.structural_rank
                        }
                      />

                      <Metric
                        label="Jaccard similarity"
                        value={`${structuralPercent.toFixed(
                          2
                        )}%`}
                      />

                      <Metric
                        label="Shared skills"
                        value={
                          recommendation.shared_skill_count
                        }
                      />

                      <Metric
                        label="Candidate skills"
                        value={
                          recommendation.candidate_skill_count
                        }
                      />
                    </div>

                    <p
                      style={{
                        marginTop: "14px",
                        marginBottom: 0,
                        color: "#6B7280",
                        fontSize: "13px",
                        lineHeight: 1.55
                      }}
                    >
                      Jaccard similarity measures
                      overlap between the canonical
                      ESCO skill sets of the two
                      occupations. It is used only
                      to identify structurally
                      related candidates.
                    </p>
                  </div>
                </details>
              </ResultCard>
            );
          }
        )}
      </div>

      {/* METHODOLOGY */}

      <details
        style={{
          marginTop: "28px",
          padding: "20px",
          background: "#F9FAFB",
          borderRadius: "12px",
          border:
            "1px solid #E5E7EB"
        }}
      >
        <summary
          style={{
            cursor: "pointer",
            fontWeight: 650,
            color: "#374151",
            fontSize: "16px"
          }}
        >
          How Career Transition works
        </summary>

        <div
          style={{
            marginTop: "18px",
            color: "#4B5563",
            fontSize: "14px",
            lineHeight: 1.65
          }}
        >
          <p>
            Career Transition first generates
            structurally related occupation
            candidates using Jaccard similarity
            over canonical ESCO skill sets.
          </p>

          <p>
            That graph-based similarity is used
            only for{" "}
            <strong>
              candidate generation
            </strong>
            .
          </p>

          <p>
            The final displayed order is based
            on <strong>MatchESCO</strong>, which
            measures how well your selected
            skills cover the ESCO requirements
            of each candidate occupation.
          </p>

          <p>
            Labor-market evidence is shown
            separately and does not change the
            ranking.
          </p>

          <p>
            These results describe structural
            relatedness and current skill
            alignment. They are not predictions
            of employment outcomes and do not
            claim that one career path is
            objectively better than another.
          </p>
        </div>
      </details>
    </section>
  );
}

function ResultCard({
  children
}: {
  children: ReactNode;
}) {
  return (
    <article
      style={{
        border:
          "1px solid #E5E7EB",
        borderRadius: "16px",
        padding: "28px",
        background: "#FFFFFF",
        boxShadow:
          "0 1px 3px rgba(0,0,0,0.05)"
      }}
    >
      {children}
    </article>
  );
}

function SectionHeader({
  eyebrow,
  title,
  description
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
          marginBottom: "8px"
        }}
      >
        {eyebrow}
      </div>

      <h3
        style={{
          margin: 0,
          fontSize: "24px",
          color: "#111827",
          fontWeight: 700
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
          maxWidth: "720px"
        }}
      >
        {description}
      </p>
    </div>
  );
}

function Metric({
  label,
  value
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
          "1px solid #E5E7EB"
      }}
    >
      <div
        style={{
          fontSize: "14px",
          color: "#4B5563",
          fontWeight: 500
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop: "8px",
          fontSize: "24px",
          fontWeight: 700,
          color: "#111827"
        }}
      >
        {value}
      </div>
    </div>
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

function SmallMetric({
  label,
  value
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div
      style={{
        padding: "12px 14px",
        borderRadius: "10px",
        background: "#FFFFFF",
        border: "1px solid #E5E7EB"
      }}
    >
      <div
        style={{
          fontSize: "12px",
          color: "#6B7280",
          fontWeight: 600,
          lineHeight: 1.4
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop: "6px",
          fontSize: "19px",
          fontWeight: 700,
          color: "#111827"
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
  fontSize: "14px"
};

const detailBodyStyle = {
  marginTop: "12px",
  color: "#4B5563",
  lineHeight: 1.65,
  fontSize: "14px"
};