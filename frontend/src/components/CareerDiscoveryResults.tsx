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

type CareerRecommendation = {
  rank: number;

  occupation_id: string;
  occupation_name: string;
  description?: string | null;
  isco_group?: string | null;

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

type CareerDiscoveryResult = {
  mode: "career_discovery";

  candidate_pool: string;
  candidate_count: number;

  final_ranking_criterion: string;
  recommendation_top_n: number;

  recommendation_status: "matches_found" | "no_match";
  recommendation_message: string | null;

  recommendations: CareerRecommendation[];
};

type CareerPathComparisonExplanation = {
  explanation_type: "career_path_comparison";
  explanation_text: string;
};

type CareerDiscoveryResponse = {
  analysis_type: "career_paths";
  mode: "career_discovery";
  current_occupation_id: null;
  user_skill_count: number;
  career_result: CareerDiscoveryResult;
  explanation?: unknown;
  comparison_explanation?: CareerPathComparisonExplanation | null;
};

type Props = {
  data: CareerDiscoveryResponse;
};

function toPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
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

function formatRelationType(value: string) {
  if (!value) {
    return "Required";
  }

  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function relationBadgeStyle(relationType: string) {
  const normalized = relationType.toLowerCase();

  if (normalized.includes("essential")) {
    return {
      background: "#FEF2F2",
      color: "#991B1B",
      border: "1px solid #FECACA"
    };
  }

  if (normalized.includes("optional")) {
    return {
      background: "#F3F4F6",
      color: "#4B5563",
      border: "1px solid #E5E7EB"
    };
  }

  return {
    background: "#F8FAFC",
    color: "#475569",
    border: "1px solid #E2E8F0"
  };
}

export default function CareerDiscoveryResults({
  data
}: Props) {
  const result = data.career_result;
  const comparisonExplanation = data.comparison_explanation;

  return (
    <section
      style={{
        marginTop: "32px",
        width: "100%",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        color: "#111827"
      }}
    >
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
          Career discovery
        </div>

        <h2
          style={{
            margin: 0,
            fontSize: "34px",
            lineHeight: 1.2,
            color: "#111827"
          }}
        >
          {result.recommendation_status === "no_match" ? "Career discovery result" : "Careers that match your skills"}
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
          {result.recommendation_status === "no_match"
            ? "Your selected skills were compared with the supported analytical occupations, but no ESCO skill coverage was found."
            : "Your selected skills were compared with the supported analytical occupations. The careers below are ordered by their current ESCO skill fit."}
        </p>

        <div
          style={{
            marginTop: "16px",
            fontSize: "14px",
            color: "#6B7280"
          }}
        >
          {result.candidate_count} occupations evaluated
        </div>
      </div>
      
      {result.recommendation_status === "no_match" && (
        <ResultCard>
          <div
            style={{
              padding: "4px 0"
            }}
          >
            <div
              style={{
                fontSize: "13px",
                fontWeight: 700,
                color: "#92400E",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "8px"
              }}
            >
              No matching career found
            </div>

            <h3
              style={{
                margin: 0,
                fontSize: "24px",
                color: "#111827"
              }}
            >
              No meaningful career match was found
            </h3>

            <p
              style={{
                marginTop: "10px",
                marginBottom: 0,
                color: "#4B5563",
                fontSize: "15px",
                lineHeight: 1.65,
                maxWidth: "760px"
              }}
            >
              {result.recommendation_message || "Your selected skills currently provide no ESCO skill coverage for the supported occupations. Try adding more skills that better represent your current profile."}
            </p>
          </div>
        </ResultCard>
      )}

      {result.recommendation_status === "matches_found" && (
      <div
        style={{
          display: "grid",
          gap: "20px"
        }}
      >
        {result.recommendations.map((recommendation) => {
            const currentFit = toPercent(recommendation.match_esco) ?? 0;
            const marketFit = toPercent(recommendation.match_market);
            const marketDetails = recommendation.market_details ?? [];
            const coveredMarketSkills = marketDetails.filter((skill) => skill.coverage > 0);
            const uncoveredMarketSkills = marketDetails.filter((skill) => skill.coverage <= 0);
            const missingSkills = recommendation.skill_gaps.filter((skill) => skill.match_type === "none")
                .sort((a, b) => {
                  const aEssential = a.relation_type.toLowerCase().includes("essential") ? 0 : 1;
                  const bEssential = b.relation_type.toLowerCase().includes("essential") ? 0 : 1;

                  if (aEssential !== bEssential) {
                    return (aEssential - bEssential);
                  }

                  return (b.gap - a.gap);
                });

            const relatedMatches = recommendation.skill_gaps.filter((skill) => skill.match_type === "semantic")
                .sort((a, b) => b.coverage - a.coverage);
            const visibleMissingSkills = missingSkills.slice(0, 5);
            const visibleRelatedMatches = relatedMatches.slice(0, 5);

            return (
              <ResultCard
                key={
                  recommendation.occupation_id
                }
              >

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
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
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        marginBottom: "6px"
                      }}
                    >
                      Recommendation #
                      {recommendation.rank}
                    </div>

                    <h3
                      style={{
                        margin: 0,
                        fontSize: "24px"
                      }}
                    >
                      {formatLabel(recommendation.occupation_name)}
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

                    {recommendation.description && (
                      <p
                        style={{
                          margin: "10px 0 0",
                          maxWidth: "680px",
                          color: "#4B5563",
                          fontSize: "14px",
                          lineHeight: 1.6
                        }}
                      >
                        {recommendation.description}
                      </p>
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

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
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

                <details
                  style={{
                    marginTop: "20px"
                  }}
                >
                  <summary
                    style={summaryStyle}
                  >
                    Why does this career fit my profile?
                  </summary>

                  <div
                    style={detailBodyStyle}
                  >
                    <p
                      style={{
                        marginTop: 0
                      }}
                    >
                      Your current fit combines
                      direct skill matches with
                      partial semantic coverage of
                      related ESCO skills.
                    </p>

                    {recommendation.exact_match_count >
                      0 && (
                      <p>
                        You have{" "}
                        <strong>
                          {
                            recommendation.exact_match_count
                          }
                        </strong>{" "}
                        exact skill{" "}
                        {recommendation.exact_match_count ===
                        1
                          ? "match"
                          : "matches"}{" "}
                        for this occupation.
                      </p>
                    )}

                    {relatedMatches.length > 0 && (
                      <p>
                        You also have{" "}
                        <strong>
                          {
                            relatedMatches.length
                          }
                        </strong>{" "}
                        partially related skill{" "}
                        {relatedMatches.length === 1 ? "match" : "matches"}{" "}
                        that contribute to your
                        current fit.
                      </p>
                    )}

                    <p
                      style={{
                        marginBottom: 0
                      }}
                    >
                      Partial matches increase
                      estimated coverage, but they
                      do not mean that you already
                      possess the required ESCO
                      skill.
                    </p>
                  </div>
                </details>

                {visibleRelatedMatches.length > 0 && (
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
                          const coverage = toPercent(skill.coverage) ?? 0;

                          return (
                            <div
                              key={
                                skill.skill_id
                              }
                              style={{
                                padding: "14px 16px",
                                borderRadius: "10px",
                                background: "#F8FAFC",
                                border: "1px solid #E2E8F0"
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "flex-start",
                                  gap: "14px",
                                  flexWrap: "wrap"
                                }}
                              >
                                <strong
                                  style={{
                                    fontSize: "15px"
                                  }}
                                >
                                  {formatLabel(skill.skill_name)}
                                </strong>

                                <span
                                  style={{
                                    padding: "4px 9px",
                                    borderRadius: "999px",
                                    background: "#EEF2FF",
                                    color: "#4338CA",
                                    fontSize: "12px",
                                    fontWeight: 700
                                  }}
                                >
                                  {coverage.toFixed(
                                    1
                                  )}
                                  % partial coverage
                                </span>
                              </div>

                              {skill.best_user_skill_name && (
                                <p
                                  style={{
                                    margin: "9px 0 0",
                                    color: "#4B5563",
                                    fontSize: "14px",
                                    lineHeight: 1.55
                                  }}
                                >
                                  Your selected skill{" "}
                                  <strong>
                                    {formatLabel(
                                      skill.best_user_skill_name
                                    )}
                                  </strong>{" "}
                                  is the closest semantic match found for this required skill.
                                </p>
                              )}

                              <div
                                style={{
                                  marginTop: "9px"
                                }}
                              >
                                <RelationBadge
                                  relationType={
                                    skill.relation_type
                                  }
                                />
                              </div>
                            </div>
                          );
                        }
                      )}

                      {relatedMatches.length >
                        visibleRelatedMatches.length && (
                        <div
                          style={{
                            color: "#6B7280",
                            fontSize: "13px"
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

                {visibleMissingSkills.length > 0 && (
                  <details
                    style={{
                      marginTop: "18px"
                    }}
                  >
                    <summary
                      style={summaryStyle}
                    >
                      Skills you may still need
                    </summary>

                    <div
                      style={{
                        display: "grid",
                        gap: "10px",
                        marginTop: "14px"
                      }}
                    >
                      {visibleMissingSkills.map(
                        (skill) => {
                          const gap = toPercent(skill.gap) ?? 0;

                          return (
                            <div
                              key={
                                skill.skill_id
                              }
                              style={{
                                padding: "14px 16px",
                                borderRadius: "10px",
                                border: "1px solid #E5E7EB",
                                background: "#FFFFFF"
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "flex-start",
                                  justifyContent: "space-between",
                                  gap: "14px",
                                  flexWrap: "wrap"
                                }}
                              >
                                <strong
                                  style={{
                                    fontSize: "15px"
                                  }}
                                >
                                  {formatLabel(
                                    skill.skill_name
                                  )}
                                </strong>

                                <RelationBadge
                                  relationType={
                                    skill.relation_type
                                  }
                                />
                              </div>

                              <p
                                style={{
                                  margin: "9px 0 0",
                                  color: "#4B5563",
                                  fontSize: "14px",
                                  lineHeight: 1.55
                                }}
                              >
                                No current match
                                was found for this
                                required skill.
                                Its remaining
                                coverage gap is{" "}
                                <strong>
                                  {gap.toFixed(
                                    1
                                  )}
                                  %
                                </strong>
                                .
                              </p>
                            </div>
                          );
                        }
                      )}

                      {missingSkills.length >
                        visibleMissingSkills.length && (
                        <div
                          style={{
                            color: "#6B7280",
                            fontSize: "13px"
                          }}
                        >
                          Showing{" "}
                          {
                            visibleMissingSkills.length
                          }{" "}
                          of{" "}
                          {
                            missingSkills.length
                          }{" "}
                          skills with no
                          current match.
                        </div>
                      )}
                    </div>
                  </details>
                )}

                <div
                  style={{
                    marginTop: "22px",
                    padding: "18px",
                    borderRadius: "12px",
                    background: "#F9FAFB",
                    border: "1px solid #E5E7EB"
                  }}
                >
                  <div
                    style={{
                      fontSize: "13px",
                      fontWeight: 700,
                      color: "#6B7280",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
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

                      {recommendation.market_reason || "There is not enough occupation-specific market evidence to calculate this score."}
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
                              marketFit === 0 ? "#92400E" : "#4B5563",
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
                        does not change the career
                        ranking.
                      </p>

                      {marketFit === 0 && (
                        <div
                          style={{
                            marginTop: "14px",
                            padding: "12px 14px",
                            background: "#FFFBEB",
                            border: "1px solid #FDE68A",
                            borderRadius: "8px",
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
                                gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
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
                                  const coverage = toPercent(skill.coverage) ?? 0;
                                  const isCovered = skill.coverage > 0;

                                  return (
                                    <div
                                      key={
                                        skill.skill_id
                                      }
                                      style={{
                                        padding: "14px 16px",
                                        borderRadius: "10px",
                                        background: "#FFFFFF",
                                        border: "1px solid #E5E7EB"
                                      }}
                                    >
                                      <div
                                        style={{
                                          display: "flex",
                                          justifyContent: "space-between",
                                          alignItems: "flex-start",
                                          gap: "14px",
                                          flexWrap: "wrap"
                                        }}
                                      >
                                        <strong
                                          style={{
                                            fontSize: "15px"
                                          }}
                                        >
                                          {formatLabel(
                                            skill.skill_name
                                          )}
                                        </strong>

                                        <span
                                          style={{
                                            display: "inline-flex",
                                            padding: "4px 9px",
                                            borderRadius: "999px",
                                            fontSize: "12px",
                                            fontWeight: 700,
                                            background: isCovered ? "#F0FDF4" : "#F3F4F6",
                                            color: isCovered ? "#166534" : "#4B5563",
                                            border: isCovered ? "1px solid #BBF7D0" : "1px solid #E5E7EB"
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
                                          margin: "9px 0 0",
                                          color: "#4B5563",
                                          fontSize: "14px",
                                          lineHeight: 1.55
                                        }}
                                      >
                                        {isCovered
                                          ? "Your selected profile contributes measurable coverage to this market-supported requirement."
                                          : "Your selected profile currently provides no measured coverage for this market-supported requirement."}
                                      </p>

                                      <details
                                        style={{
                                          marginTop: "9px"
                                        }}
                                      >
                                        <summary
                                          style={{
                                            ...summaryStyle,
                                            fontSize: "13px"
                                          }}
                                        >
                                          Technical evidence
                                        </summary>

                                        <div
                                          style={{
                                            marginTop: "8px",
                                            padding: "10px 12px",
                                            borderRadius: "8px",
                                            background: "#F8FAFC",
                                            color: "#4B5563",
                                            fontSize: "13px",
                                            lineHeight: 1.55
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
                                              marginTop: "4px"
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
                                              margin: "8px 0 0"
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


                <details
                  style={{
                    marginTop: "18px"
                  }}
                >
                  <summary
                    style={summaryStyle}
                  >
                    How should I interpret
                    this result?
                  </summary>

                  <div
                    style={detailBodyStyle}
                  >
                    <p>
                      <strong>
                        Current fit
                      </strong>{" "}
                      measures ESCO skill
                      coverage for this
                      occupation.
                    </p>

                    <p>
                      <strong>
                        Exact matches
                      </strong>{" "}
                      are direct matches between
                      your selected skills and
                      required ESCO skills.
                    </p>

                    <p>
                      <strong>
                        Related matches
                      </strong>{" "}
                      are semantic similarities that provide partial coverage. They should not
                      be interpreted as proof that you possess the required skill.
                    </p>

                    <p>
                      <strong>
                        Missing skills
                      </strong>{" "}
                      are requirements for which the system found no current
                      match.
                    </p>

                    <p>
                      Labor-market evidence is supplementary and does not change the career ranking.
                    </p>
                  </div>
                </details>
              </ResultCard>
            );
          }
        )}
      </div>
      )}

        {result.recommendation_status === "matches_found" && comparisonExplanation && (
          <ResultCard>
            <div
              style={{
                fontSize: "13px",
                color: "#6B7280",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "8px"
              }}
            >
              Why this path?
            </div>

            <h3
              style={{
                margin: 0,
                fontSize: "24px",
                color: "#111827"
              }}
            >
              Why the first recommendation appears above the next alternative
            </h3>

            <p
              style={{
                marginTop: "10px",
                marginBottom: 0,
                color: "#4B5563",
                lineHeight: 1.65,
                fontSize: "14px"
              }}
            >
              {comparisonExplanation.explanation_text}
            </p>
          </ResultCard>
        )}

      <details
        style={{
          marginTop: "28px",
          padding: "20px",
          background: "#F9FAFB",
          borderRadius: "12px",
          border: "1px solid #E5E7EB"
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
          How these careers were selected
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
            Career Discovery evaluates the
            supported occupation set directly
            against your selected skills.
          </p>

          <p>
            The displayed order is based on{" "}
            <strong>MatchESCO</strong>, which
            measures ESCO skill coverage.
          </p>

          <p>
            Exact matches provide full direct
            coverage. Semantic matches can
            provide partial coverage when a
            selected user skill is sufficiently
            similar to a required ESCO skill.
          </p>

          <p>
            The semantic explanation shown in
            each card identifies the selected
            user skill that produced the
            strongest semantic match for that
            requirement.
          </p>

          <p>
            Relation-type badges come directly
            from the occupation-skill relation
            supplied by the backend. They are
            shown as contextual information and
            do not create a separate ranking.
          </p>

          <p>
            Labor-market evidence is shown
            separately as supplementary
            information and is not combined
            with the ESCO score.
          </p>

          <p>
            The recommendations describe
            current skill alignment only.
            They are not predictions of
            employment outcomes or claims
            that one career is objectively
            better than another.
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
        border: "1px solid #E5E7EB",
        borderRadius: "16px",
        padding: "28px",
        background: "#FFFFFF",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)"
      }}
    >
      {children}
    </article>
  );
}

function Metric({
  label,
  value
}: {
  label: string;
  value: number;
}) {
  return (
    <div
      style={{
        padding: "16px",
        borderRadius: "12px",
        background: "#F9FAFB",
        border: "1px solid #E5E7EB"
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
  const safePercent = Math.min(100, Math.max(0, percent));
  const [displayedPercent, setDisplayedPercent] = useState(0);

  useEffect(() => {
    setDisplayedPercent(0);

    const frame = requestAnimationFrame(() => {
      setDisplayedPercent(safePercent);
    });

    return () => cancelAnimationFrame(frame);
  }, [safePercent]);

  const fillColor = variant === "esco" ? "#4F46E5" : "#0F766E";

  const trackColor = variant === "esco" ? "#E0E7FF" : "#CCFBF1";

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
        variant === "esco" ? "Current ESCO skill coverage" : "Market-supported skill coverage"
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
          transition: "width 650ms cubic-bezier(0.22, 1, 0.36, 1)"
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

function RelationBadge({
  relationType
}: {
  relationType: string;
}) {
  const style = relationBadgeStyle(relationType);

  return (
    <span
      style={{
        ...style,
        display: "inline-flex",
        alignItems: "center",
        padding: "4px 9px",
        borderRadius: "999px",
        fontSize: "12px",
        fontWeight: 700,
        whiteSpace: "nowrap"
      }}
    >
      {formatRelationType(
        relationType
      )}
    </span>
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
