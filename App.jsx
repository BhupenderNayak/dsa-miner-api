import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function formatNumber(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 1,
  }).format(Number(value ?? 0));
}

function formatAcceptance(value) {
  if (value === null || value === undefined) return "NA";
  const numeric = Number(value);
  const percent = numeric <= 1 ? numeric * 100 : numeric;
  return `${percent.toFixed(1)}%`;
}

function difficultyClass(difficulty) {
  if (difficulty === "Hard") return "border-rose-200 bg-rose-50 text-rose-700";
  if (difficulty === "Medium") return "border-amber-200 bg-amber-50 text-amber-700";
  if (difficulty === "Easy") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json();
}

function LoadingBar() {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
      <div className="h-full w-1/3 animate-pulse rounded-full bg-sky-500" />
    </div>
  );
}

function CompanyControlPanel({ companies, selectedCompany, onCompanyChange, loading }) {
  return (
    <section className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-end lg:justify-between lg:px-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">DSA Pattern Miner</h1>
          <p className="mt-1 text-sm text-slate-500">Company signals, pattern frequency, and prep sequencing</p>
        </div>

        <label className="flex w-full flex-col gap-1.5 lg:w-80">
          <span className="text-sm font-medium text-slate-700">Company</span>
          <select
            value={selectedCompany}
            onChange={(event) => onCompanyChange(event.target.value)}
            disabled={loading || companies.length === 0}
            className="h-11 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-900 shadow-sm outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100 disabled:cursor-not-allowed disabled:bg-slate-100"
          >
            <option value="">Select company</option>
            {companies.map((company) => (
              <option key={company.company_id} value={company.company_name}>
                {company.company_name}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}

function PatternChart({ patterns, loading, selectedCompany }) {
  const maxFrequency = useMemo(
    () => Math.max(...patterns.map((pattern) => Number(pattern.total_frequency)), 1),
    [patterns],
  );

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Top Patterns</h2>
          <p className="mt-1 text-sm text-slate-500">{selectedCompany || "No company selected"}</p>
        </div>
        <span className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-600">
          {patterns.length} shown
        </span>
      </div>

      <div className="mt-5 min-h-80">
        {loading ? (
          <LoadingBar />
        ) : patterns.length === 0 ? (
          <div className="flex h-72 items-center justify-center rounded-md border border-dashed border-slate-200 text-sm text-slate-500">
            Select a company to load pattern frequency.
          </div>
        ) : (
          <div className="space-y-4">
            {patterns.map((pattern, index) => {
              const width = `${Math.max((Number(pattern.total_frequency) / maxFrequency) * 100, 4)}%`;
              return (
                <div key={pattern.pattern_name} className="grid gap-2">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-slate-100 text-xs font-semibold text-slate-700">
                        {index + 1}
                      </span>
                      <span className="truncate font-medium text-slate-900">{pattern.pattern_name}</span>
                    </div>
                    <div className="shrink-0 text-right text-xs text-slate-500">
                      <span className="font-semibold text-slate-800">{formatNumber(pattern.total_frequency)}</span>
                      <span className="ml-1">freq</span>
                    </div>
                  </div>
                  <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full bg-sky-500" style={{ width }} />
                  </div>
                  <div className="text-xs text-slate-500">
                    {pattern.problem_count} problems, avg {formatNumber(pattern.avg_frequency)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

function RoadmapGenerator({ selectedCompany }) {
  const [daysToPrep, setDaysToPrep] = useState(30);
  const [dailyTarget, setDailyTarget] = useState(5);
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generateRoadmap(event) {
    event.preventDefault();
    if (!selectedCompany) return;

    const params = new URLSearchParams({
      company_name: selectedCompany,
      days_to_prep: String(daysToPrep),
      daily_target: String(dailyTarget),
    });

    setLoading(true);
    setError("");
    try {
      const data = await fetchJson(`/roadmap/generate?${params.toString()}`);
      setRoadmap(data);
    } catch (requestError) {
      setRoadmap(null);
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Roadmap Generator</h2>
          <p className="mt-1 text-sm text-slate-500">{selectedCompany || "Choose a company first"}</p>
        </div>

        <form onSubmit={generateRoadmap} className="grid gap-3 sm:grid-cols-[130px_130px_auto]">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">Days</span>
            <input
              type="number"
              min="1"
              max="365"
              value={daysToPrep}
              onChange={(event) => setDaysToPrep(event.target.value)}
              className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
            />
          </label>

          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">Daily Target</span>
            <input
              type="number"
              min="1"
              max="20"
              value={dailyTarget}
              onChange={(event) => setDailyTarget(event.target.value)}
              className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
            />
          </label>

          <button
            type="submit"
            disabled={!selectedCompany || loading}
            className="h-10 self-end rounded-md bg-slate-950 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {loading ? "Generating" : "Generate"}
          </button>
        </form>
      </div>

      {error && (
        <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </div>
      )}

      <div className="mt-5">
        {loading ? (
          <LoadingBar />
        ) : roadmap ? (
          <ProblemTable roadmap={roadmap} />
        ) : (
          <div className="flex h-72 items-center justify-center rounded-md border border-dashed border-slate-200 text-sm text-slate-500">
            Generate a roadmap to see prioritized questions.
          </div>
        )}
      </div>
    </section>
  );
}

function ProblemTable({ roadmap }) {
  return (
    <div>
      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <Metric label="Questions" value={roadmap.total_questions} />
        <Metric label="Days" value={roadmap.days_to_prep} />
        <Metric label="Daily Target" value={roadmap.daily_target} />
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200">
        <div className="max-h-[640px] overflow-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="sticky top-0 bg-slate-50 text-left text-xs font-semibold uppercase tracking-normal text-slate-500">
              <tr>
                <th className="w-16 px-4 py-3">Rank</th>
                <th className="min-w-[18rem] px-4 py-3">Problem</th>
                <th className="px-4 py-3">Difficulty</th>
                <th className="px-4 py-3">Frequency</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Acceptance</th>
                <th className="min-w-[18rem] px-4 py-3">Patterns</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {roadmap.questions.map((problem) => (
                <tr key={`${problem.rank}-${problem.title}`} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-semibold text-slate-700">{problem.rank}</td>
                  <td className="px-4 py-3">
                    {problem.url ? (
                      <a
                        href={problem.url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-sky-700 hover:text-sky-900"
                      >
                        {problem.title}
                      </a>
                    ) : (
                      <span className="font-medium text-slate-900">{problem.title}</span>
                    )}
                    {problem.leetcode_id && (
                      <div className="mt-1 text-xs text-slate-500">#{problem.leetcode_id}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${difficultyClass(problem.difficulty)}`}>
                      {problem.difficulty ?? "NA"}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-800">{formatNumber(problem.frequency_count)}</td>
                  <td className="px-4 py-3 font-medium text-slate-800">{formatNumber(problem.importance_score)}</td>
                  <td className="px-4 py-3 text-slate-600">{formatAcceptance(problem.acceptance_rate)}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {problem.patterns.slice(0, 4).map((pattern) => (
                        <span key={pattern} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                          {pattern}
                        </span>
                      ))}
                      {problem.patterns.length > 4 && (
                        <span className="rounded-md bg-slate-900 px-2 py-1 text-xs font-medium text-white">
                          +{problem.patterns.length - 4}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
      <div className="text-xs font-medium uppercase tracking-normal text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-slate-950">{value}</div>
    </div>
  );
}

export default function App() {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState("");
  const [patterns, setPatterns] = useState([]);
  const [companiesLoading, setCompaniesLoading] = useState(true);
  const [patternsLoading, setPatternsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadCompanies() {
      setCompaniesLoading(true);
      setError("");
      try {
        const data = await fetchJson("/companies/");
        setCompanies(data);
        if (data.length > 0) setSelectedCompany(data[0].company_name);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setCompaniesLoading(false);
      }
    }

    loadCompanies();
  }, []);

  useEffect(() => {
    async function loadPatterns() {
      if (!selectedCompany) {
        setPatterns([]);
        return;
      }

      setPatternsLoading(true);
      setError("");
      try {
        const encodedCompany = encodeURIComponent(selectedCompany);
        const data = await fetchJson(`/companies/${encodedCompany}/top-patterns?limit=12`);
        setPatterns(data);
      } catch (requestError) {
        setPatterns([]);
        setError(requestError.message);
      } finally {
        setPatternsLoading(false);
      }
    }

    loadPatterns();
  }, [selectedCompany]);

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <CompanyControlPanel
        companies={companies}
        selectedCompany={selectedCompany}
        onCompanyChange={setSelectedCompany}
        loading={companiesLoading}
      />

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(320px,420px)_1fr] lg:px-8">
        <div className="grid content-start gap-6">
          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}
          <PatternChart patterns={patterns} loading={patternsLoading} selectedCompany={selectedCompany} />
        </div>

        <RoadmapGenerator selectedCompany={selectedCompany} />
      </div>
    </main>
  );
}
