import { EmailTable } from "@/components/EmailTable";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <main className="flex-1 flex flex-col items-center justify-start w-full">
          <EmailTable />
      </main>
    </div>
  );
}
