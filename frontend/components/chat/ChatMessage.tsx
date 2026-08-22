import DoctorCard, { DoctorRecommendation } from "@/components/doctors/DoctorCard";

export type Message = {
  role: "user" | "assistant";
  content: string;
  doctorRecommendations?: DoctorRecommendation[];
};

export default function ChatMessage({ message, onBooked }: { message: Message; onBooked?: () => void }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
          isUser ? "bg-slate-900 text-white" : "bg-teal-600 text-white"
        }`}
      >
        {isUser ? "You" : "H"}
      </div>
      <div className={`max-w-[80%] ${isUser ? "" : "w-full"}`}>
        <div
          className={`whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm ${
            isUser ? "rounded-tr-sm bg-slate-900 text-white" : "rounded-tl-sm bg-white text-slate-800 ring-1 ring-slate-200"
          }`}
        >
          {message.content}
        </div>
        {message.doctorRecommendations && message.doctorRecommendations.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.doctorRecommendations.map((d) => (
              <DoctorCard key={d.doctor_id} doctor={d} onBooked={onBooked} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
