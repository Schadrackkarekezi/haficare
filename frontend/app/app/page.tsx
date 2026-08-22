import { redirect } from "next/navigation";

export default function PatientAppRoot() {
  redirect("/app/chat");
}
