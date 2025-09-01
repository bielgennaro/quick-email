
import React, { useRef } from "react";
import { XIcon, PaperPlaneTiltIcon, PaperclipIcon } from "@phosphor-icons/react";
import { Button } from "./button";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  onSend: (data: { to: string; subject: string; content: string; file: File | null }) => void;
}

export function ModalEscreverEmail({ open, onClose, onSend }: ModalProps) {
  const formRef = useRef<HTMLFormElement>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const form = formRef.current;
    if (!form) return;
    const data = new FormData(form);
    const fileInput = form.querySelector('input[name="file"]') as HTMLInputElement | null;
    const file = fileInput && fileInput.files && fileInput.files.length > 0 ? fileInput.files[0] : null;
    onSend({
      to: data.get("to") as string,
      subject: data.get("subject") as string,
      content: data.get("content") as string,
      file,
    });
    onClose();
  }

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-2xl relative animate-fade-in flex flex-col gap-8">
        <Button
          className="absolute top-4 right-4 text-neutral-400 hover:text-neutral-900 transition-colors"
          onClick={onClose}
          aria-label="Fechar"
          variant="outline"
        >
          <XIcon size={24} />
        </Button>
        <h2 className="text-2xl font-bold text-neutral-900 flex items-center gap-2 mb-2">
          Escrever email
        </h2>
        <form ref={formRef} onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            name="to"
            type="email"
            required
            placeholder="Para (email)"
            className="border border-neutral-200 rounded-lg px-4 py-2 text-base focus:ring-2 ring-blue-600"
          />
          <input
            name="subject"
            type="text"
            required
            placeholder="Assunto"
            className="border border-neutral-200 rounded-lg px-4 py-2 text-base focus:ring-2 ring-blue-600"
          />
          <textarea
            name="content"
            required
            placeholder="Conteúdo do email"
            rows={4}
            className="border border-neutral-200 rounded-lg px-4 py-2 text-base focus:ring-2 ring-blue-600 resize-none"
          />
          <label className="flex items-center gap-2 cursor-pointer text-blue-700 hover:text-blue-900">
            <PaperclipIcon size={20} />
            <span className="text-base">Anexar arquivo (.txt, .pdf)</span>
            <input
              name="file"
              type="file"
              accept=".txt,application/pdf"
              className="hidden"
            />
          </label>
          <button
            type="submit"
            className="mt-2 bg-neutral-900 text-white rounded-lg px-6 py-2 font-semibold flex items-center gap-2 justify-center hover:bg-neutral-800 transition-colors"
          >
            <PaperPlaneTiltIcon size={20} />
            Enviar
          </button>
        </form>
      </div>
    </div>
  );
}
