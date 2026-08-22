const ACTIONS = [
  { label: "Find a doctor", prompt: "I'd like help finding the right doctor for a health concern." },
  { label: "Check my symptoms", prompt: "I want to describe my symptoms and see what it might be." },
  { label: "Find a pharmacy", prompt: "I'm looking for a nearby pharmacy." },
  { label: "Book an appointment", prompt: "I'd like to book an appointment." },
];

export default function QuickActions({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {ACTIONS.map((a) => (
        <button
          key={a.label}
          onClick={() => onPick(a.prompt)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-left text-sm font-medium text-slate-700 shadow-sm transition hover:border-teal-300 hover:bg-teal-50 hover:text-teal-700"
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}
