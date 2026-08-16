"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface MarkdownRendererProps {
  content: string;
}

const entityMap: Record<string, string> = {
  "&": "&",
  "<": "<",
  ">": ">",
  "\"": "\"",
  "'": "'",
  "`": "&#96;",
};

function parseMarkdown(content: string): React.ReactNode {
  const lines = content.split("\n");
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code blocks
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // Skip closing ```

      result.push(
        <pre key={result.length} className="bg-[var(--axiom-bg-base)] border border-[var(--axiom-border)]/50 rounded-xl overflow-x-auto p-4 my-3">
          <code className={cn("text-[12px] font-mono text-[var(--axiom-text-primary)]", lang)}>
            {codeLines.join("\n")}
          </code>
        </pre>
      );
      continue;
    }

    // Headers
    const headerMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const text = headerMatch[2];
      const Tag = level === 1 ? "h1" : level === 2 ? "h2" : "h3";
      result.push(
        <Tag key={result.length} className={cn(
          "font-light text-[var(--axiom-text-primary)] mb-2 mt-4",
          level === 1 && "text-2xl md:text-3xl",
          level === 2 && "text-xl md:text-2xl",
          level === 3 && "text-lg md:text-xl"
        )}>
          {parseInline(text)}
        </Tag>
      );
      i++;
      continue;
    }

    // Horizontal rule
    if (line.match(/^[-*_]{3,}$/)) {
      result.push(
        <hr key={result.length} className="border-[var(--axiom-border)]/30 my-4" />
      );
      i++;
      continue;
    }

    // Lists
    if (line.match(/^[\s]*[-*+]\s/)) {
      const listItems: string[] = [];
      while (i < lines.length && lines[i].match(/^[\s]*[-*+]\s/)) {
        listItems.push(lines[i].replace(/^[\s]*[-*+]\s/, ""));
        i++;
      }
      result.push(
        <ul key={result.length} className="list-disc list-inside space-y-1 ml-4 mb-3 text-[var(--axiom-text-primary)]">
          {listItems.map((item, idx) => (
            <li key={idx} className="text-[var(--axiom-text-primary)]">
              {parseInline(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Numbered lists
    if (line.match(/^[\s]*\d+\.\s/)) {
      const listItems: string[] = [];
      while (i < lines.length && lines[i].match(/^[\s]*\d+\.\s/)) {
        listItems.push(lines[i].replace(/^[\s]*\d+\.\s/, ""));
        i++;
      }
      result.push(
        <ol key={result.length} className="list-decimal list-inside space-y-1 ml-4 mb-3 text-[var(--axiom-text-primary)]">
          {listItems.map((item, idx) => (
            <li key={idx} className="text-[var(--axiom-text-primary)]">
              {parseInline(item)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Blockquotes
    if (line.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith(">")) {
        quoteLines.push(lines[i].slice(1).trim());
        i++;
      }
      result.push(
        <blockquote key={result.length} className="border-l-2 border-[var(--axiom-accent)]/50 pl-4 italic text-[var(--axiom-text-secondary)] my-3">
          {quoteLines.map((ql, idx) => (
            <p key={idx}>{parseInline(ql)}</p>
          ))}
        </blockquote>
      );
      continue;
    }

    // Empty line - paragraph break
    if (!line.trim()) {
      i++;
      // Check if next line is also empty to avoid multiple breaks
      if (i < lines.length && !lines[i].trim()) {
        i++;
      }
      continue;
    }

    // Regular paragraph
    const paragraphLines: string[] = [line];
    i++;
    while (i < lines.length && lines[i].trim() && !lines[i].startsWith("```") && !lines[i].match(/^#{1,3}\s/) && !lines[i].match(/^[-*+]\s/) && !lines[i].match(/^\d+\.\s/) && !lines[i].startsWith(">") && !lines[i].match(/^[-*_]{3,}$/)) {
      paragraphLines.push(lines[i]);
      i++;
    }
    result.push(
      <p key={result.length} className="text-[var(--axiom-text-primary)] leading-relaxed mb-3">
        {parseInline(paragraphLines.join(" "))}
      </p>
    );
  }

  return <div>{result}</div>;
}

function parseInline(text: string): React.ReactNode {
  // Handle inline code, bold, italic, links
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/);
  return (
    <span>
      {parts.map((part, idx) => {
        // Inline code
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code key={idx} className="bg-[var(--axiom-bg-base)] border border-[var(--axiom-border)]/30 px-1.5 py-0.5 rounded text-[11px] font-mono text-[var(--axiom-accent)]">
              {part.slice(1, -1)}
            </code>
          );
        }
        // Bold
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={idx} className="font-semibold text-[var(--axiom-text-primary)]">{part.slice(2, -2)}</strong>;
        }
        // Italic
        if (part.startsWith("*") && part.endsWith("*") && !part.startsWith("**")) {
          return <em key={idx} className="italic">{part.slice(1, -1)}</em>;
        }
        // Links
        const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (linkMatch) {
          return (
            <a key={idx} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className="text-[var(--axiom-accent)] hover:underline underline-offset-2">
              {linkMatch[1]}
            </a>
          );
        }
        return <span key={idx}>{part}</span>;
      })}
    </span>
  );
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return <div className="prose prose-invert max-w-none">{parseMarkdown(content)}</div>;
}