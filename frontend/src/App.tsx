import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import CareerDiscoveryResults from "./components/CareerDiscoveryResults";
import CareerTransitionResults from "./components/CareerTransitionResults";
import TargetOccupationResults from "./components/TargetOccupationResults";

type AnalysisMode = | "target" | "transition" | "discovery";

type Skill = {
  skill_id: string;
  skill_name: string;
};

type Occupation = {
  occupation_id: string;
  occupation_name: string;
  isco_group?: string | null;
};

const API_BASE_URL = "http://127.0.0.1:8001";

function containsGreekCharacters(text: string) {
  return /[\u0370-\u03FF\u1F00-\u1FFF]/.test(text);
}

function App() {
  const [mode, setMode] = useState<AnalysisMode>("target");

  const [skillQuery, setSkillQuery] = useState("");
  const [skillResults, setSkillResults] = useState<Skill[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<Skill[]>([]);
  const [skillsLoading, setSkillsLoading] = useState(false);
  const [skillActiveIndex, setSkillActiveIndex] = useState(-1);

  const [targetOccupationQuery, setTargetOccupationQuery] = useState("");
  const [targetOccupationResults, setTargetOccupationResults] = useState<Occupation[]>([]);
  const [selectedTargetOccupation, setSelectedTargetOccupation] = useState<Occupation | null>(null);
  const [targetOccupationActiveIndex, setTargetOccupationActiveIndex] = useState(-1);

  const [currentOccupationQuery, setCurrentOccupationQuery] = useState("");
  const [currentOccupationResults, setCurrentOccupationResults] = useState<Occupation[]>([]);
  const [selectedCurrentOccupation, setSelectedCurrentOccupation] = useState<Occupation | null>(null);
  const [currentOccupationActiveIndex, setCurrentOccupationActiveIndex] = useState(-1);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<unknown>(null);

  const skillQueryContainsGreek = containsGreekCharacters(skillQuery);
  const targetOccupationQueryContainsGreek = containsGreekCharacters(targetOccupationQuery);
  const currentOccupationQueryContainsGreek = containsGreekCharacters(currentOccupationQuery);

  useEffect(() => {
    const query = skillQuery.trim();

    if (query.length < 2 || containsGreekCharacters(query)) {
      setSkillResults([]);
      setSkillActiveIndex(-1);
      setSkillsLoading(false);
      return;
    }

    const controller = new AbortController();

    setSkillResults([]);
    setSkillActiveIndex(-1);
    setSkillsLoading(true);

    const timeout = setTimeout(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/skills?q=${encodeURIComponent(query)}&limit=10`,
          {
            signal: controller.signal
          }
        );

        if (!response.ok)
          throw new Error("Skill search request failed.");

        const data = await response.json();

        setSkillResults(data.skills ?? []);
        setSkillActiveIndex(-1);
      } 
      catch (error) {
        if (error instanceof DOMException && error.name === "AbortError")
          return;

        console.error("Skill search error:", error);
        setSkillResults([]);
      } 
      finally {
        if (!controller.signal.aborted) 
          setSkillsLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [skillQuery]);

  useEffect(() => {
    const query = targetOccupationQuery.trim();

    if (mode !== "target" || query.length < 2 || selectedTargetOccupation !== null || containsGreekCharacters(query)) {
      setTargetOccupationResults([]);
      setTargetOccupationActiveIndex(-1);
      return;
    }

    const timeout = setTimeout(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/occupations?q=${encodeURIComponent(query)}&limit=10`);

        if (!response.ok) 
          throw new Error("Target occupation search failed.");

        const data = await response.json();
        setTargetOccupationResults(data.occupations ?? []);
        setTargetOccupationActiveIndex(-1);
      } catch (error) {
        console.error("Target occupation search error:", error);
        setTargetOccupationResults([]);
      }
    }, 300);

    return () => clearTimeout(timeout);
  }, [targetOccupationQuery, mode, selectedTargetOccupation]);

  useEffect(() => {
    const query = currentOccupationQuery.trim();

    if (mode !== "transition" || query.length < 2 || selectedCurrentOccupation !== null || containsGreekCharacters(query)) {
      setCurrentOccupationResults([]);
      setCurrentOccupationActiveIndex(-1);
      return;
    }

    const timeout = setTimeout(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/current-occupations?q=${encodeURIComponent(query)}&limit=10`);

        if (!response.ok)
          throw new Error("Current occupation search failed.");
        
        const data = await response.json();
        setCurrentOccupationResults(data.occupations ?? []);
        setCurrentOccupationActiveIndex(-1);
      } catch (error) {
        console.error("Current occupation search error:", error);
        setCurrentOccupationResults([]);
      }
    }, 300);

    return () => clearTimeout(timeout);
  }, [currentOccupationQuery, mode, selectedCurrentOccupation]);

  const handleSelectSkill = (skill: Skill) => {
    const alreadySelected = selectedSkills.some((item) => item.skill_id === skill.skill_id);

    if (!alreadySelected) 
      setSelectedSkills([...selectedSkills, skill]);
    
    setSkillQuery("");
    setSkillResults([]);
    setSkillActiveIndex(-1);
  };

  const handleRemoveSkill = (skillId: string) => {
    setSelectedSkills(selectedSkills.filter((skill) => skill.skill_id !== skillId));
  };

  const handleModeChange = (newMode: AnalysisMode) => {
    setMode(newMode);

    setTargetOccupationQuery("");
    setTargetOccupationResults([]);
    setTargetOccupationActiveIndex(-1);
    setSelectedTargetOccupation(null);

    setCurrentOccupationQuery("");
    setCurrentOccupationResults([]);
    setCurrentOccupationActiveIndex(-1);
    setSelectedCurrentOccupation(null);

    setAnalysisResult(null);
    setAnalysisError(null);
  };

  const handleSkillSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (skillResults.length === 0) {
      if (event.key === "Escape") {
        setSkillResults([]);
        setSkillActiveIndex(-1);
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSkillActiveIndex((current) => current < skillResults.length - 1 ? current + 1 : 0);
    } 
    else if (event.key === "ArrowUp") {
      event.preventDefault();
      setSkillActiveIndex((current) => current > 0 ? current - 1 : skillResults.length - 1);
    } 
    else if (event.key === "Enter") {
      event.preventDefault();
      const selectedIndex = skillActiveIndex >= 0 ? skillActiveIndex : 0;
      handleSelectSkill(skillResults[selectedIndex]);
    } 
    else if (event.key === "Escape") {
      setSkillResults([]);
      setSkillActiveIndex(-1);
    }
  };

  const handleTargetOccupationKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (targetOccupationResults.length === 0) {
      if (event.key === "Escape") {
        setTargetOccupationResults([]);
        setTargetOccupationActiveIndex(-1);
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setTargetOccupationActiveIndex((current) => current < targetOccupationResults.length - 1 ? current + 1 : 0);
    } 
    else if (event.key === "ArrowUp") {
      event.preventDefault();
      setTargetOccupationActiveIndex((current) => current > 0 ? current - 1 : targetOccupationResults.length - 1);
    } 
    else if (event.key === "Enter") {
      event.preventDefault();
      const selectedIndex = targetOccupationActiveIndex >= 0 ? targetOccupationActiveIndex : 0;
      const occupation = targetOccupationResults[selectedIndex];
      setSelectedTargetOccupation(occupation);
      setTargetOccupationQuery(occupation.occupation_name);
      setTargetOccupationResults([]);
      setTargetOccupationActiveIndex(-1);
    } 
    else if (event.key === "Escape") {
      setTargetOccupationResults([]);
      setTargetOccupationActiveIndex(-1);
    }
  };

  const handleCurrentOccupationKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (currentOccupationResults.length === 0) {
      if (event.key === "Escape") {
        setCurrentOccupationResults([]);
        setCurrentOccupationActiveIndex(-1);
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setCurrentOccupationActiveIndex((current) => current < currentOccupationResults.length - 1 ? current + 1 : 0);
    } 
    else if (event.key === "ArrowUp") {
      event.preventDefault();
      setCurrentOccupationActiveIndex((current) => current > 0 ? current - 1 : currentOccupationResults.length - 1);
    } 
    else if (event.key === "Enter") {
      event.preventDefault();
      const selectedIndex = currentOccupationActiveIndex >= 0 ? currentOccupationActiveIndex : 0;
      const occupation = currentOccupationResults[selectedIndex];
      setSelectedCurrentOccupation(occupation);
      setCurrentOccupationQuery(occupation.occupation_name);
      setCurrentOccupationResults([]);
      setCurrentOccupationActiveIndex(-1);
    } 
    else if (event.key === "Escape") {
      setCurrentOccupationResults([]);
      setCurrentOccupationActiveIndex(-1);
    }
  };

  const handleAnalyze = async () => {
    const userSkillIds = selectedSkills.map((skill) => skill.skill_id);

    if (userSkillIds.length === 0) {
      alert("Please select at least one skill.");
      return;
    }

    if (mode === "target" && !selectedTargetOccupation) {
      alert("Please select a target occupation.");
      return;
    }

    if (mode === "transition" && !selectedCurrentOccupation) {
      alert("Please select your current occupation.");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      let endpoint: string;
      let payload: object;

      if (mode === "target") {
        endpoint = `${API_BASE_URL}/api/analyze-target-occupation`;

        payload = {
          occupation_id: selectedTargetOccupation!.occupation_id,
          occupation_name: selectedTargetOccupation!.occupation_name,
          user_skill_ids: userSkillIds,
          learning_priority_top_n: 5,
          graph_top_n: 3,
          roadmap_max_steps: 5
        };
      } else if (mode === "transition") {
        endpoint = `${API_BASE_URL}/api/analyze-career-paths`;

        payload = {
          user_skill_ids: userSkillIds,
          current_occupation_id: selectedCurrentOccupation!.occupation_id,
          structural_top_n: 10,
          recommendation_top_n: 5,
          min_shared_skills: 1
        };
      } else {
        endpoint = `${API_BASE_URL}/api/analyze-career-paths`;

        payload = {
          user_skill_ids: userSkillIds,
          current_occupation_id: null,
          structural_top_n: 10,
          recommendation_top_n: 5,
          min_shared_skills: 1
        };
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        let message = "Analysis request failed.";

        if (data && typeof data === "object" && "detail" in data) {
          message = String(data.detail);
        }

        throw new Error(message);
      }

      setAnalysisResult(data);
    } catch (error) {
      console.error("Analysis error:", error);

      if (error instanceof Error) {
        setAnalysisError(error.message);
      } else {
        setAnalysisError("An unexpected error occurred.");
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <>
      <style>{`
        @keyframes analysisSpin {
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes analysisResultsEnter {
          from {
            opacity: 0;
            transform: translateY(10px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .analysis-spinner {
          width: 16px;
          height: 16px;
          flex: 0 0 16px;
          border: 2px solid rgba(255, 255, 255, 0.45);
          border-top-color: currentColor;
          border-radius: 50%;
          animation: analysisSpin 700ms linear infinite;
        }

        .analysis-results-enter {
          animation: analysisResultsEnter 320ms ease-out both;
        }

        .interactive-card {
          transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease, background-color 150ms ease;
        }

        .interactive-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        }

        .interactive-card:active {
          transform: translateY(0);
        }

        .search-option {
          transition: background-color 120ms ease, color 120ms ease;
        }

        .search-option:hover {
          background: var(--primary-soft) !important;
        }

        .interactive-input {
          transition: border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
        }

        .interactive-input:hover {
          border-color: #A5B4FC !important;
        }

        .interactive-input:focus {
          border-color: var(--primary) !important;
          box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12) !important;
          outline: none;
        }

        .primary-action {
          transition: transform 150ms ease, box-shadow 150ms ease, filter 150ms ease;
        }

        .primary-action:not(:disabled):hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 14px rgba(79, 70, 229, 0.22);
          filter: brightness(1.03);
        }

        .primary-action:not(:disabled):active {
          transform: translateY(0);
          box-shadow: none;
        }

        .secondary-action,
        .text-action,
        .icon-action {
          transition: background-color 120ms ease, color 120ms ease, border-color 120ms ease, transform 120ms ease;
        }

        .secondary-action:hover {
          background: #EEF2FF !important;
          border-color: #A5B4FC !important;
        }

        .secondary-action:active,
        .text-action:active,
        .icon-action:active {
          transform: scale(0.97);
        }

        .text-action:hover {
          color: #4338CA !important;
          text-decoration: underline;
        }

        .icon-action:hover {
          color: #4338CA !important;
          background: #EEF2FF !important;
        }

        .skill-chip {
          transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
        }

        .skill-chip:hover {
          transform: translateY(-1px);
          border-color: #A5B4FC !important;
          box-shadow: 0 3px 8px rgba(79, 70, 229, 0.08);
        }

        @media (prefers-reduced-motion: reduce) {
          .analysis-spinner {
            animation-duration: 1.4s;
          }

          .analysis-results-enter {
            animation: none;
          }

          .interactive-card,
          .search-option,
          .interactive-input,
          .primary-action,
          .secondary-action,
          .text-action,
          .icon-action,
          .skill-chip {
            transition: none;
          }

          .interactive-card:hover,
          .primary-action:not(:disabled):hover,
          .skill-chip:hover {
            transform: none;
          }
        }
      `}</style>

      <div
      style={{
        maxWidth: "980px",
        margin: "0 auto",
        padding: "48px 24px 64px"
      }}
    >
      <header style={{ marginBottom: "32px" }}>
        <div
          style={{
            fontSize: "13px",
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "var(--primary)",
            marginBottom: "10px"
          }}
        >
          Undergraduate Thesis
        </div>
        

        <div
          style={{
            maxWidth: "820px",
            fontSize: "18px",
            lineHeight: 1.55,
            fontWeight: 650,
            color: "var(--text-primary)",
            marginBottom: "22px"
          }}
        >
          Development of an Explainable Career Path Recommendation System using Knowledge Graphs and Graph Algorithms
        </div>

        <h1 style={{ marginBottom: "12px" }}>
          Explore your career options
        </h1>

        <p
          style={{
            maxWidth: "720px",
            margin: 0,
            fontSize: "17px",
            lineHeight: 1.65,
            color: "var(--text-secondary)"
          }}
        >
          Select your current skills and choose what you want
          to explore. The system compares your profile with
          ESCO occupation requirements and supporting
          labor-market evidence.
        </p>
      </header>

      <section
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
          padding: "30px",
          boxShadow: "var(--shadow-md)",
          marginBottom: "36px"
        }}
      >
        <div style={{ marginBottom: "32px" }}>
          <div
            style={{
              fontSize: "13px",
              fontWeight: 700,
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              marginBottom: "8px"
            }}
          >
            What would you like to explore?
          </div>

          <p
            style={{
              marginTop: 0,
              marginBottom: "16px",
              color: "var(--text-secondary)"
            }}
          >
            Choose one analysis mode.
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(210px, 1fr))",
              gap: "12px"
            }}
          >
            <ModeCard
              title="Target Career"
              description="See how your current skills compare with a specific occupation."
              selected={mode === "target"}
              onClick={() => handleModeChange("target")}
            />

            <ModeCard
              title="Career Transition"
              description="Explore occupations structurally related to your current role."
              selected={mode === "transition"}
              onClick={() => handleModeChange("transition")}
            />

            <ModeCard
              title="Discover Careers"
              description="Find occupations that match your current skills without choosing a starting role."
              selected={mode === "discovery"}
              onClick={() => handleModeChange("discovery")}
            />
          </div>
        </div>

        <Divider />

        <div style={{ marginBottom: "30px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              gap: "12px",
              flexWrap: "wrap",
              marginBottom: "8px"
            }}
          >
            <div>
              <h2 style={{ margin: 0, fontSize: "21px" }}>
                Your skills
              </h2>

              <p
                style={{
                  marginTop: "6px",
                  marginBottom: 0,
                  color: "var(--text-secondary)"
                }}
              >
                Add the skills that best represent your current
                profile.
              </p>
            </div>

            {selectedSkills.length > 0 && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px"
                }}
              >
                <span
                  style={{
                    fontSize: "14px",
                    color: "var(--text-muted)"
                  }}
                >
                  {selectedSkills.length} selected
                </span>

                <button
                  className="text-action"
                  type="button"
                  onClick={() => {
                    setSelectedSkills([]);
                    setAnalysisResult(null);
                    setAnalysisError(null);
                  }}
                  style={{
                    border: "none",
                    background: "transparent",
                    color: "#6366F1",
                    cursor: "pointer",
                    fontSize: "13px",
                    fontWeight: 600,
                    padding: 0,
                    minHeight: "auto",
                    boxShadow: "none"
                  }}
                >
                  Clear all
                </button>
              </div>
            )}
          </div>

          {selectedSkills.length > 0 && (
            <div
              style={{
                display: "flex",
                gap: "8px",
                flexWrap: "wrap",
                marginTop: "16px",
                marginBottom: "14px"
              }}
            >
              {selectedSkills.map((skill) => (
                <div
                  className="skill-chip"
                  key={skill.skill_id}
                  style={{
                    border: "1px solid #C7D2FE",
                    borderRadius: "999px",
                    padding: "7px 10px 7px 13px",
                    display: "flex",
                    alignItems: "center",
                    gap: "7px",
                    background: "var(--primary-soft)",
                    color: "#3730A3"
                  }}
                >
                  <span
                    style={{
                      fontSize: "14px",
                      fontWeight: 600
                    }}
                  >
                    {formatLabel(skill.skill_name)}
                  </span>

                  <button
                    className="icon-action"
                    type="button"
                    onClick={() =>
                      handleRemoveSkill(skill.skill_id)
                    }
                    title="Remove skill"
                    aria-label={`Remove ${formatLabel(skill.skill_name)}`}
                    style={{
                      border: "none",
                      background: "transparent",
                      color: "#6366F1",
                      cursor: "pointer",
                      fontWeight: 700,
                      padding: "0 4px",
                      minHeight: "auto",
                      lineHeight: 1,
                      boxShadow: "none"
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          <div
            style={{
              position: "relative",
              marginTop: "16px"
            }}
          >
            <div
              style={{
                position: "relative"
              }}
            >
              <input
                className="interactive-input"
                type="text"
                value={skillQuery}
                onChange={(event) => {
                  setSkillQuery(event.target.value);
                  setSkillActiveIndex(-1);
                }}
                onKeyDown={handleSkillSearchKeyDown}
                placeholder="Search for a skill, e.g. Python, data analysis..."
                style={{
                  paddingRight: "46px"
                }}
              />

              {skillQuery.length > 0 && (
                <button
                  className="icon-action"
                  type="button"
                  onClick={() => {
                    setSkillQuery("");
                    setSkillResults([]);
                    setSkillActiveIndex(-1);
                  }}
                  aria-label="Clear skill search"
                  title="Clear search"
                  style={{
                    position: "absolute",
                    right: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    border: "none",
                    background: "transparent",
                    color: "#6B7280",
                    cursor: "pointer",
                    fontSize: "20px",
                    lineHeight: 1,
                    padding: "4px",
                    minHeight: "auto",
                    boxShadow: "none"
                  }}
                >
                  ×
                </button>
              )}
            </div>

            {skillQueryContainsGreek && (
              <div
                style={{
                  marginTop: "8px",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  background: "#FFFBEB",
                  border: "1px solid #FDE68A",
                  color: "#92400E",
                  fontSize: "13px",
                  lineHeight: 1.5
                }}
              >
                Please use English terms when searching for skills.
              </div>
            )}

            {skillsLoading && (
              <div
                style={{
                  fontSize: "14px",
                  color: "var(--text-muted)",
                  marginTop: "8px"
                }}
              >
                Searching...
              </div>
            )}

            {skillResults.length > 0 && (
              <SearchDropdown>
                {skillResults.map((skill, index) => (
                  <SearchOption
                    key={skill.skill_id}
                    active={index === skillActiveIndex}
                    onMouseEnter={() => setSkillActiveIndex(index)}
                    onClick={() =>
                      handleSelectSkill(skill)
                    }
                  >
                    {formatLabel(skill.skill_name)}
                  </SearchOption>
                ))}
              </SearchDropdown>
            )}
          </div>
        </div>

        {mode === "target" && (
          <>
            <Divider />

            <div style={{ marginBottom: "30px" }}>
              <h2 style={{ margin: 0, fontSize: "21px" }}>
                Target career
              </h2>

              <p
                style={{
                  marginTop: "6px",
                  color: "var(--text-secondary)"
                }}
              >
                Select the occupation you want to compare your
                current profile against.
              </p>

              {selectedTargetOccupation ? (
                <SelectedOccupationCard
                  occupation={selectedTargetOccupation}
                  onChange={() => {
                    setSelectedTargetOccupation(null);
                    setTargetOccupationQuery("");
                  }}
                />
              ) : (
                <div
                  style={{
                    position: "relative",
                    marginTop: "16px"
                  }}
                >
                  <input
                    className="interactive-input"
                    type="text"
                    value={targetOccupationQuery}
                    onChange={(event) => {
                      setTargetOccupationQuery(
                        event.target.value
                      );
                      setTargetOccupationActiveIndex(-1);
                    }}
                    onKeyDown={handleTargetOccupationKeyDown}
                    placeholder="Search target career..."
                  />

                  {targetOccupationQueryContainsGreek && (
                    <div
                      style={{
                        marginTop: "8px",
                        padding: "10px 12px",
                        borderRadius: "8px",
                        background: "#FFFBEB",
                        border: "1px solid #FDE68A",
                        color: "#92400E",
                        fontSize: "13px",
                        lineHeight: 1.5
                      }}
                    >
                      Please use English terms when searching for occupations.
                    </div>
                  )}

                  {targetOccupationResults.length > 0 && (
                    <SearchDropdown>
                      {targetOccupationResults.map(
                        (occupation, index) => (
                          <SearchOption
                            key={occupation.occupation_id}
                            active={index === targetOccupationActiveIndex}
                            onMouseEnter={() => setTargetOccupationActiveIndex(index)}
                            onClick={() => {
                              setSelectedTargetOccupation(
                                occupation
                              );
                              setTargetOccupationQuery(
                                occupation.occupation_name
                              );
                              setTargetOccupationResults([]);
                              setTargetOccupationActiveIndex(-1);
                            }}
                          >
                            <span>
                              {occupation.occupation_name}
                            </span>

                            {occupation.isco_group && (
                              <span
                                style={{
                                  marginLeft: "8px",
                                  color: "var(--text-muted)",
                                  fontSize: "13px"
                                }}
                              >
                                ISCO {occupation.isco_group}
                              </span>
                            )}
                          </SearchOption>
                        )
                      )}
                    </SearchDropdown>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {mode === "transition" && (
          <>
            <Divider />

            <div style={{ marginBottom: "30px" }}>
              <h2 style={{ margin: 0, fontSize: "21px" }}>
                Current career
              </h2>

              <p
                style={{
                  marginTop: "6px",
                  color: "var(--text-secondary)"
                }}
              >
                Select your current occupation to explore
                related career paths.
              </p>

              {selectedCurrentOccupation ? (
                <SelectedOccupationCard
                  occupation={selectedCurrentOccupation}
                  onChange={() => {
                    setSelectedCurrentOccupation(null);
                    setCurrentOccupationQuery("");
                  }}
                />
              ) : (
                <div
                  style={{
                    position: "relative",
                    marginTop: "16px"
                  }}
                >
                  <input
                    className="interactive-input"
                    type="text"
                    value={currentOccupationQuery}
                    onChange={(event) => {
                      setCurrentOccupationQuery(
                        event.target.value
                      );
                      setCurrentOccupationActiveIndex(-1);
                    }}
                    onKeyDown={handleCurrentOccupationKeyDown}
                    placeholder="Search current career..."
                  />

                  {currentOccupationQueryContainsGreek && (
                    <div
                      style={{
                        marginTop: "8px",
                        padding: "10px 12px",
                        borderRadius: "8px",
                        background: "#FFFBEB",
                        border: "1px solid #FDE68A",
                        color: "#92400E",
                        fontSize: "13px",
                        lineHeight: 1.5
                      }}
                    >
                      Please use English terms when searching for occupations.
                    </div>
                  )}
                  
                  {currentOccupationResults.length > 0 && (
                    <SearchDropdown>
                      {currentOccupationResults.map(
                        (occupation, index) => (
                          <SearchOption
                            key={occupation.occupation_id}
                            active={index === currentOccupationActiveIndex}
                            onMouseEnter={() => setCurrentOccupationActiveIndex(index)}
                            onClick={() => {
                              setSelectedCurrentOccupation(
                                occupation
                              );
                              setCurrentOccupationQuery(
                                occupation.occupation_name
                              );
                              setCurrentOccupationResults([]);
                              setCurrentOccupationActiveIndex(-1);
                            }}
                          >
                            <span>
                              {occupation.occupation_name}
                            </span>

                            {occupation.isco_group && (
                              <span
                                style={{
                                  marginLeft: "8px",
                                  color: "var(--text-muted)",
                                  fontSize: "13px"
                                }}
                              >
                                ISCO {occupation.isco_group}
                              </span>
                            )}
                          </SearchOption>
                        )
                      )}
                    </SearchDropdown>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {mode === "discovery" && (
          <>
            <Divider />

            <div
              style={{
                marginBottom: "30px",
                padding: "16px",
                borderRadius: "12px",
                background: "var(--surface-soft)",
                border: "1px solid var(--border)"
              }}
            >
              <strong>
                No occupation selection needed
              </strong>

              <p
                style={{
                  marginTop: "6px",
                  marginBottom: 0,
                  color: "var(--text-secondary)"
                }}
              >
                The system will compare your current skills
                directly with the analytical occupation set.
              </p>
            </div>
          </>
        )}

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end"
          }}
        >
          <button
            className="primary-action"
            type="button"
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            aria-busy={isAnalyzing}
            style={{
              padding: "13px 24px",
              minWidth: "170px",
              fontSize: "16px",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "9px",
              cursor: isAnalyzing ? "wait" : "pointer"
            }}
          >
            {isAnalyzing && (
              <span
                className="analysis-spinner"
                aria-hidden="true"
              />
            )}

            <span>
              {isAnalyzing
                ? "Analyzing..."
                : "Analyze profile"}
            </span>
          </button>
        </div>

        {analysisError && (
          <div
            style={{
              marginTop: "20px",
              padding: "14px 16px",
              border: "1px solid #FECACA",
              background: "var(--danger-soft)",
              borderRadius: "10px",
              color: "var(--danger)"
            }}
          >
            <strong>Analysis failed</strong>

            <div style={{ marginTop: "5px" }}>
              {analysisError}
            </div>
          </div>
        )}
      </section>

      {analysisResult !== null && (
        <div
          className="analysis-results-enter"
          aria-live="polite"
        >
          {mode === "target" && (
            <TargetOccupationResults
              data={analysisResult as any}
            />
          )}

          {mode === "transition" && (
            <CareerTransitionResults
              data={analysisResult as any}
            />
          )}

          {mode === "discovery" && (
            <CareerDiscoveryResults
              data={analysisResult as any}
            />
          )}
        </div>
      )}

      <footer
        style={{
          marginTop: "56px",
          padding: "28px 0 10px",
          borderTop: "1px solid var(--border)",
          color: "var(--text-secondary)",
          fontSize: "13px",
          lineHeight: 1.6
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "24px",
            flexWrap: "wrap"
          }}
        >
          <div>
            <div
              style={{
                fontWeight: 700,
                color: "var(--text-primary)",
                marginBottom: "4px"
              }}
            >
              © 2026 Career Recommendation System
            </div>

            <div>
              Undergraduate Thesis Project
            </div>
          </div>

          <div
            style={{
              textAlign: "right"
            }}
          >
            <div>
              In collaboration with{" "}
              <a
                href="https://skillab-project.eu/"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: "var(--text-primary)",
                  fontWeight: 700,
                  textDecoration: "none"
                }}
              >
                Skillab
              </a>
            </div>

            <div>
              Occupational and skills data based on{" "}
              <a
                href="https://esco.ec.europa.eu/en"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: "var(--text-primary)",
                  fontWeight: 700,
                  textDecoration: "none"
                }}
              >
                ESCO
              </a>
              {" "}· European Commission
            </div>
          </div>
        </div>

        <p
          style={{
            margin: "20px 0 0",
            paddingTop: "16px",
            borderTop: "1px solid var(--border)",
            color: "var(--text-muted)",
            fontSize: "12px"
          }}
        >
          This system provides explainable career recommendations
          for research and educational purposes. Results should not
          be interpreted as guaranteed career or employment outcomes.
        </p>
      </footer>
      </div>
    </>
  );
}

function ModeCard({
  title,
  description,
  selected,
  onClick
}: {
  title: string;
  description: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className="interactive-card"
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      style={{
        textAlign: "left",
        padding: "18px",
        borderRadius: "12px",
        border: selected
          ? "2px solid var(--primary)"
          : "1px solid var(--border)",
        background: selected
          ? "var(--primary-soft)"
          : "var(--surface)",
        color: "var(--text-primary)",
        boxShadow: selected
          ? "0 0 0 3px rgba(79,70,229,0.08)"
          : "none",
        minHeight: "130px",
        cursor: "pointer"
      }}
    >
      <strong
        style={{
          display: "block",
          fontSize: "16px",
          marginBottom: "7px",
          color: selected
            ? "#3730A3"
            : "var(--text-primary)"
        }}
      >
        {title}
      </strong>

      <span
        style={{
          display: "block",
          fontSize: "14px",
          lineHeight: 1.5,
          color: "var(--text-secondary)"
        }}
      >
        {description}
      </span>
    </button>
  );
}

function Divider() {
  return (
    <div
      style={{
        height: "1px",
        background: "var(--border)",
        marginBottom: "30px"
      }}
    />
  );
}

function SearchDropdown({
  children
}: {
  children: ReactNode;
}) {
  return (
    <div
      style={{
        position: "absolute",
        top: "calc(100% + 5px)",
        left: 0,
        width: "100%",
        zIndex: 20,
        maxHeight: "270px",
        overflowY: "auto",
        background: "#FFFFFF",
        border: "1px solid var(--border)",
        borderRadius: "10px",
        boxShadow: "var(--shadow-md)"
      }}
    >
      {children}
    </div>
  );
}

function SearchOption({
  children,
  onClick,
  active = false,
  onMouseEnter
}: {
  children: ReactNode;
  onClick: () => void;
  active?: boolean;
  onMouseEnter?: () => void;
}) {
  return (
    <button
      className="search-option"
      type="button"
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      style={{
        width: "100%",
        textAlign: "left",
        padding: "12px 14px",
        minHeight: "auto",
        border: "none",
        borderBottom: "1px solid var(--border)",
        borderRadius: 0,
        background: active ? "var(--primary-soft)" : "#FFFFFF",
        color: "var(--text-primary)",
        boxShadow: "none",
        cursor: "pointer"
      }}
    >
      {children}
    </button>
  );
}

function SelectedOccupationCard({
  occupation,
  onChange
}: {
  occupation: Occupation;
  onChange: () => void;
}) {
  return (
    <div
      style={{
        marginTop: "16px",
        padding: "15px 16px",
        border: "1px solid #C7D2FE",
        borderRadius: "12px",
        background: "var(--primary-soft)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "16px"
      }}
    >
      <div>
        <strong
          style={{
            display: "block",
            fontSize: "16px",
            color: "#312E81"
          }}
        >
          {occupation.occupation_name}
        </strong>

        {occupation.isco_group && (
          <span
            style={{
              fontSize: "13px",
              color: "#6366F1"
            }}
          >
            ISCO {occupation.isco_group}
          </span>
        )}
      </div>

      <button
        className="secondary-action"
        type="button"
        onClick={onChange}
        style={{
          minHeight: "auto",
          padding: "7px 12px",
          background: "#FFFFFF",
          color: "#4338CA",
          border: "1px solid #C7D2FE",
          boxShadow: "none",
          cursor: "pointer"
        }}
      >
        Change
      </button>
    </div>
  );
}


function formatLabel(text: string) {
  if (!text) {
    return text;
  }

  return text.charAt(0).toUpperCase() + text.slice(1);
}

export default App;
