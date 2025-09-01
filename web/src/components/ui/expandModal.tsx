

import React from "react";
import { XIcon } from "@phosphor-icons/react";
import type { Email } from "@/types/email";
import { Button } from "./button";

interface ExpandModalProps {
  open: boolean;
  onClose: () => void;
  email: Email | null;
}

export const ExpandModal: React.FC<ExpandModalProps> = ({ open, onClose, email }) => {
  if (!open || !email) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-lg relative animate-fade-in flex flex-col gap-8">
        <Button
          className="absolute top-4 right-4 text-neutral-400 hover:text-neutral-900 transition-colors"
          onClick={onClose}
          aria-label="Fechar"
          variant={"outline"}
        >
          <XIcon size={24} />
        </Button>
        <h2 className="text-2xl font-bold text-neutral-900 flex items-center gap-2 mb-2">
          Detalhes do Email
        </h2>
        <div className="flex flex-col gap-3 mt-2">
          <div>
            <span className="font-semibold">Remetente:</span> {email.email}
          </div>
          <div>
            <span className="font-semibold">Assunto:</span> {email.snippet}
          </div>
          <div>
            <span className="font-semibold">Conteúdo:</span> {email.content}
          </div>
          <div>
            <span className="font-semibold">Categoria:</span> {email.category}
          </div>
          <div>
            <span className="font-semibold">Resposta sugerida:</span> {email.suggested_reply || "N/A"}
          </div>
        </div>
      </div>
    </div>
  );
};
