import Link from "next/link";

export default function HomePage() {
  return (
    <div className="home">
      <h1>Viber Coding Pro Max</h1>
      <p>AI Agent xây bằng LangGraph, phục vụ qua FastAPI.</p>
      <Link className="btn btn-primary" href="/chat">
        Mở Chat
      </Link>
    </div>
  );
}
