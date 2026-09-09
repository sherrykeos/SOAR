"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

interface MarkdownMessageProps {
  content: string;
  className?: string;
}

export function MarkdownMessage({ content, className = "" }: MarkdownMessageProps) {
  if (!content) return null;

  // Split content by code blocks: ```lang ... ```
  const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    const textBefore = content.substring(lastIndex, match.index);
    if (textBefore) {
      parts.push(
        <div key={`text-${lastIndex}`} className="space-y-2">
          {renderFormattedText(textBefore)}
        </div>
      );
    }

    const language = match[1] || "text";
    const code = match[2] || "";
    parts.push(
      <CodeBlock key={`code-${match.index}`} language={language} code={code} />
    );

    lastIndex = match.index + match[0].length;
  }

  const textAfter = content.substring(lastIndex);
  if (textAfter) {
    parts.push(
      <div key={`text-${lastIndex}`} className="space-y-2">
        {renderFormattedText(textAfter)}
      </div>
    );
  }

  return (
    <div className={`space-y-3 leading-relaxed text-sm text-[#F1F5ED] font-sans ${className}`}>
      {parts}
    </div>
  );
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl overflow-hidden border border-[#202A22] bg-[#070A08] font-mono text-xs my-3 shadow-lg">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#0D120F] border-b border-[#202A22] text-[#9BA79D]">
        <span className="text-[11px] font-semibold text-[#B8F23D] uppercase">
          {language}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] text-[#9BA79D] hover:text-[#F1F5ED] hover:bg-[#121812] transition cursor-pointer"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-[#22C55E]" />
              <span className="text-[#22C55E]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-4 overflow-x-auto text-[#F1F5ED] leading-relaxed whitespace-pre font-mono selection:bg-[#B8F23D] selection:text-[#070A08]">
        <code>{code.trim()}</code>
      </div>
    </div>
  );
}

function renderFormattedText(raw: string): React.ReactNode[] {
  const paragraphs = raw.split(/\n\n+/);

  return paragraphs.map((para, pIdx) => {
    const lines = para.split("\n");

    // Check if it's a bullet list
    const isList = lines.every((line) => line.trim().startsWith("- ") || line.trim().startsWith("* "));
    if (isList) {
      return (
        <ul key={pIdx} className="list-disc list-inside space-y-1 my-2 pl-2">
          {lines.map((line, lIdx) => (
            <li key={lIdx} className="text-[#F1F5ED]">
              {renderInlineFormatting(line.trim().replace(/^[-*]\s+/, ""))}
            </li>
          ))}
        </ul>
      );
    }

    // Check if it's a header
    if (para.startsWith("### ")) {
      return (
        <h3 key={pIdx} className="text-base font-bold text-[#D5FF78] mt-4 mb-1 font-sans">
          {renderInlineFormatting(para.replace(/^###\s+/, ""))}
        </h3>
      );
    }
    if (para.startsWith("## ")) {
      return (
        <h2 key={pIdx} className="text-lg font-bold text-[#F1F5ED] mt-4 mb-1 font-sans">
          {renderInlineFormatting(para.replace(/^##\s+/, ""))}
        </h2>
      );
    }
    if (para.startsWith("# ")) {
      return (
        <h1 key={pIdx} className="text-xl font-bold text-[#F1F5ED] mt-4 mb-1 font-sans">
          {renderInlineFormatting(para.replace(/^#\s+/, ""))}
        </h1>
      );
    }

    return (
      <p key={pIdx} className="text-[#F1F5ED] leading-relaxed whitespace-pre-wrap">
        {renderInlineFormatting(para)}
      </p>
    );
  });
}

function renderInlineFormatting(text: string): React.ReactNode {
  // Inline code: `code`
  const parts: React.ReactNode[] = [];
  const inlineCodeRegex = /`([^`]+)`/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = inlineCodeRegex.exec(text)) !== null) {
    const before = text.substring(lastIndex, match.index);
    if (before) parts.push(renderBold(before));
    parts.push(
      <code
        key={`inline-${match.index}`}
        className="px-1.5 py-0.5 rounded bg-[#121812] border border-[#202A22] text-[#D5FF78] font-mono text-xs"
      >
        {match[1]}
      </code>
    );
    lastIndex = match.index + match[0].length;
  }

  const after = text.substring(lastIndex);
  if (after) parts.push(renderBold(after));

  return parts;
}

function renderBold(text: string): React.ReactNode {
  // Bold: **text**
  const boldRegex = /\*\*([^*]+)\*\*/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = boldRegex.exec(text)) !== null) {
    const before = text.substring(lastIndex, match.index);
    if (before) parts.push(before);
    parts.push(
      <strong key={`bold-${match.index}`} className="font-semibold text-white">
        {match[1]}
      </strong>
    );
    lastIndex = match.index + match[0].length;
  }

  const after = text.substring(lastIndex);
  if (after) parts.push(after);

  return parts;
}
