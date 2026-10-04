import { useState, type FormEvent, type KeyboardEvent } from "react";
import { DiveIcon } from "../icons";
import type { ResearchDepth } from "../types";

const DEPTHS: { value: ResearchDepth; label: string; hint: string }[] = [
  { value: "auto", label: "Auto", hint: "Choose from the question" },
  { value: "shallow", label: "Shallow", hint: "One quick, cited answer" },
  { value: "deep", label: "Deep", hint: "Plan, gather and write a full report" }
];

const SAMPLES = [
  "Compare Kubernetes deployment strategies for AI research agents and recommend a production architecture.",
  "How should research workers autoscale on a Redis queue?",
  "What is KEDA?",
  "Evaluate how to secure and observe an LLM agent platform on Kubernetes."
];

interface AskBarProps {
  busy: boolean;
  onDive: (query: string, depth: ResearchDepth) => Promise<boolean>;
}

export function AskBar({ busy, onDive }: AskBarProps) {
  const [query, setQuery] = useState("");
  const [depth, setDepth] = useState<ResearchDepth>("auto");
  const ready = query.trim().length >= 4 && !busy;

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (ready && (await onDive(query.trim(), depth))) setQuery("");
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <form className="ask" onSubmit={submit}>
      <label className="ask-field">
        <span className="visually-hidden">Research question</span>
        <textarea
          value={query}
          rows={2}
          maxLength={4000}
          placeholder="Ask a research question"
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={onKeyDown}
        />
      </label>
      <fieldset className="depth-choice">
        <legend className="visually-hidden">Depth</legend>
        {DEPTHS.map((option) => (
          <label key={option.value} title={option.hint}>
            <input
              type="radio"
              name="depth"
              value={option.value}
              checked={depth === option.value}
              onChange={() => setDepth(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </fieldset>
      <button className="button dive" type="submit" disabled={!ready}>
        <DiveIcon /> {busy ? "Sending" : "Dive"}
      </button>
      {query === "" ? (
        <div className="samples">
          <span>Try</span>
          {SAMPLES.map((sample) => (
            <button key={sample} type="button" onClick={() => setQuery(sample)}>
              {sample}
            </button>
          ))}
        </div>
      ) : null}
    </form>
  );
}
