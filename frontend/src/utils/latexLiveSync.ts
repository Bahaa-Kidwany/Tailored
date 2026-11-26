import type { CareerPersona, UserProfilePayload } from '../services/profileApi';

export interface ParsedLatexSkillRow {
  label: string;
  value: string;
}

export interface ParsedLatexExperience {
  role: string;
  company: string;
  dates: string;
  location: string;
  bullets: string[];
}

export interface ParsedLatexProject {
  name: string;
  tech?: string;
  summary: string;
}

export interface ParsedLatexEducation {
  title: string;
  subtitle: string;
}

export interface LatexSyntaxWarning {
  line: number;
  message: string;
}

export interface ParsedLatexCv {
  fullName: string;
  headlineLine: string;
  contactLine: string;
  summary: string;
  skillRows: ParsedLatexSkillRow[];
  experiences: ParsedLatexExperience[];
  flatBullets: string[];
  projects: ParsedLatexProject[];
  education: ParsedLatexEducation[];
  certs: string[];
  languages: string;
  warnings: LatexSyntaxWarning[];
}

export interface LatexLineDiff {
  lineNumber: number;
  kind: 'added' | 'modified' | 'removed';
  oldLine?: string;
  newLine?: string;
}

export interface BuildCanonicalLatexParams {
  profile: UserProfilePayload;
  activePersona?: CareerPersona;
  phoneDisplay: string;
  locationLabel: string;
  summaryText: string;
  bullets: string[];
}

export function escapeLatex(raw: string): string {
  return (raw || '')
    .replace(/\\/g, '\\textbackslash{}')
    .replace(/&/g, '\\&')
    .replace(/%/g, '\\%')
    .replace(/\$/g, '\\$')
    .replace(/#/g, '\\#')
    .replace(/_/g, '\\_')
    .replace(/\{/g, '\\{')
    .replace(/\}/g, '\\}');
}

function stripUnescapedComment(line: string): string {
  for (let i = 0; i < line.length; i += 1) {
    if (line[i] === '%' && (i === 0 || line[i - 1] !== '\\')) {
      return line.slice(0, i);
    }
  }
  return line;
}

function readBracedArg(source: string, startIndex: number): { value: string; nextIndex: number } | null {
  let i = startIndex;
  while (i < source.length && /\s/.test(source[i])) i += 1;
  if (source[i] !== '{') return null;

  let depth = 0;
  const contentStart = i + 1;
  while (i < source.length) {
    const ch = source[i];
    if (ch === '\\' && i + 1 < source.length) {
      i += 2;
      continue;
    }
    if (ch === '{') depth += 1;
    else if (ch === '}') {
      depth -= 1;
      if (depth === 0) {
        return {
          value: source.slice(contentStart, i),
          nextIndex: i + 1,
        };
      }
    }
    i += 1;
  }
  return null;
}

function unwrapCommand(source: string, command: string, argIndex: number = 0): string {
  let out = source;
  const needle = `\\${command}`;
  let safety = 0;

  while (safety < 60) {
    safety += 1;
    const idx = out.indexOf(needle);
    if (idx === -1) break;
    const afterCmd = idx + needle.length;
    if (afterCmd < out.length && /[a-zA-Z]/.test(out[afterCmd])) {
      // Command prefix matched a longer macro name; skip safely by temporarily breaking out
      break;
    }

    let cursor = afterCmd;
    const args: string[] = [];
    let failed = false;
    for (let a = 0; a <= argIndex; a += 1) {
      const parsed = readBracedArg(out, cursor);
      if (!parsed) {
        failed = true;
        break;
      }
      args.push(parsed.value);
      cursor = parsed.nextIndex;
    }
    if (failed) break;

    const chosen = args[argIndex] ?? '';
    out = out.slice(0, idx) + chosen + out.slice(cursor);
  }
  return out;
}

export function unescapeLatex(raw: string): string {
  if (!raw) return '';
  let text = raw
    .replace(/\\textbackslash\{\}/g, '\\')
    .replace(/\\vspace\*?\{[^}]*\}/g, '')
    .replace(/\\hspace\*?\{[^}]*\}/g, ' ')
    .replace(/\\needspace\{[^}]*\}/g, '')
    .replace(/\\raisebox\{[^}]*\}(?:\{[^}]*\}|\\[a-zA-Z]+\*?)?/g, '')
    .replace(/\\raisebox[^\s\\{}]+\\height\\?/g, '')
    .replace(/\\fa[A-Za-z]+\*?\\?/g, '')
    .replace(/\\(resumeSubHeadingListStart|resumeSubHeadingListEnd|resumeItemListStart|resumeItemListEnd|resumeSubheading|resumeProjectHeading|newline)\b/g, ' ')
    .replace(/\\(begin|end)\{samepage\}/g, '')
    .replace(/\$\|\$/g, '|')
    .replace(/\\cdot\b/g, '·');

  text = unwrapCommand(text, 'href', 1);
  for (const cmd of ['textbf', 'emph', 'underline', 'textit', 'textrm', 'texttt', 'small', 'normalsize', 'huge', 'Huge', 'text']) {
    text = unwrapCommand(text, cmd, 0);
  }

  return text
    .replace(/\\(Huge|huge|large|Large|small|normalsize|footnotesize|scshape|bfseries|itshape|raggedright|centering)\b/g, '')
    .replace(/\\&/g, '&')
    .replace(/\\%/g, '%')
    .replace(/\\_/g, '_')
    .replace(/\\\$/g, '$')
    .replace(/\\#/g, '#')
    .replace(/\\\{/g, '{')
    .replace(/\\\}/g, '}')
    .replace(/---/g, '—')
    .replace(/--/g, '–')
    .replace(/\\\\/g, ' ')
    .replace(/\\(?=\s|$)/g, ' ')
    .replace(/~/g, ' ')
    .replace(/[{}]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function wrapProseLines(text: string, maxLen = 78): string[] {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = '';
  for (const w of words) {
    if (current && current.length + 1 + w.length > maxLen) {
      lines.push(current);
      current = w;
    } else {
      current = current ? `${current} ${w}` : w;
    }
  }
  if (current) lines.push(current);
  return lines.length > 0 ? lines : [''];
}

export function buildCanonicalCvLatex({
  profile,
  activePersona,
  phoneDisplay,
  locationLabel,
  summaryText,
  bullets,
}: BuildCanonicalLatexParams): string {
  const fullName = escapeLatex(profile.personal_info.full_name || 'Candidate');
  const email = escapeLatex(profile.personal_info.primary_email || '');
  const linkedin = escapeLatex(
    (profile.personal_info.links.linkedin || 'linkedin.com/in/candidate').replace(/^https?:\/\//, '')
  );
  const github = escapeLatex(
    (profile.personal_info.links.github || 'github.com/candidate').replace(/^https?:\/\//, '')
  );
  const headline = `${escapeLatex(activePersona?.target_title || 'AI & Data Engineer')} \\cdot ${escapeLatex(locationLabel)}`;
  const contact = `${escapeLatex(phoneDisplay)} \\cdot ${email} \\cdot ${linkedin} \\cdot ${github}`;

  const skills = activePersona?.skills_and_tools;
  const skillLines: string[] = [];
  if (skills) {
    if (skills.core_skills.length > 0) {
      skillLines.push(`\\textbf{Core Disciplines:} ${escapeLatex(skills.core_skills.join(' · '))} \\\\`);
    }
    if (skills.programming_languages.length > 0) {
      skillLines.push(`\\textbf{Languages \\& Data:} ${escapeLatex(skills.programming_languages.join(' · '))} \\\\`);
    }
    if (skills.frameworks_and_libraries.length > 0) {
      skillLines.push(`\\textbf{Frameworks \\& AI:} ${escapeLatex(skills.frameworks_and_libraries.join(' · '))} \\\\`);
    }
    if (skills.tools_and_platforms.length > 0) {
      skillLines.push(`\\textbf{Cloud \\& MLOps:} ${escapeLatex(skills.tools_and_platforms.join(' · '))}`);
    }
  }

  const exps = activePersona?.experience_highlights || [];
  const expBlocks = exps.map((exp, expIdx) => {
    const roleBullets =
      exps.length === 1
        ? bullets.length >= exp.achievements.length
          ? bullets
          : [...bullets, ...exp.achievements.slice(bullets.length)]
        : [
            bullets[expIdx] ?? exp.achievements[0],
            ...exp.achievements.slice(1),
          ].filter(Boolean);
    const items = (roleBullets.length > 0 ? roleBullets : exp.achievements)
      .map((b) => `  \\item ${escapeLatex(b)}`)
      .join('\n');
    return `\\resumeSubheading{${escapeLatex(exp.role)}}{${escapeLatex(exp.company)}}{${escapeLatex(exp.start_date)} -- ${escapeLatex(exp.end_date)}}{${escapeLatex(exp.location || locationLabel)}}
\\begin{itemize}
${items}
\\end{itemize}`;
  });

  const projects = (activePersona?.featured_projects || []).map(
    (pr) =>
      `\\resumeProjectHeading{${escapeLatex(pr.name)}}{${escapeLatex(pr.tech_stack.join(', '))}}
\\begin{itemize}
  \\item ${escapeLatex(pr.summary)}
\\end{itemize}`
  );

  const eduLines = (profile.education || []).map(
    (ed) =>
      `\\resumeSubheading{${escapeLatex(ed.degree)}}{${escapeLatex(ed.institution)}}{${escapeLatex(String(ed.graduation_year || ''))}}{${escapeLatex(ed.grade_or_gpa || '')}}`
  );

  const certLines = (activePersona?.certifications || [])
    .slice(0, 2)
    .map((c) => `${escapeLatex(c.name)} · ${escapeLatex(c.issuer)} \\\\`);

  const langLine =
    profile.languages.length > 0
      ? `Languages: ${escapeLatex(profile.languages.map((l) => `${l.language} (${l.proficiency})`).join(', '))}`
      : '';

  const wrappedSummaryLines = wrapProseLines(escapeLatex(summaryText), 78);

  return [
    '\\documentclass[10pt,letterpaper]{article}',
    '\\begin{document}',
    '',
    '\\begin{center}',
    `  {\\Huge \\scshape ${fullName}} \\\\`,
    `  ${headline} \\\\`,
    `  ${contact}`,
    '\\end{center}',
    '',
    '\\section{Summary}',
    ...wrappedSummaryLines,
    '',
    ...(skillLines.length > 0 ? ['\\section{Technical Skills}', ...skillLines, ''] : []),
    ...(expBlocks.length > 0 ? ['\\section{Experience}', ...expBlocks, ''] : []),
    ...(projects.length > 0 ? ['\\section{Projects}', ...projects, ''] : []),
    ...(eduLines.length > 0 ? ['\\section{Education}', ...eduLines, ''] : []),
    ...(certLines.length > 0 || langLine
      ? ['\\section{Certificates \\& Languages}', ...certLines, ...(langLine ? [langLine] : []), '']
      : []),
    '\\end{document}',
  ].join('\n');
}

export function lintLatexSource(tex: string): LatexSyntaxWarning[] {
  const warnings: LatexSyntaxWarning[] = [];
  const lines = tex.split('\n');
  let braceBalance = 0;
  const envStack: Array<{ name: string; line: number }> = [];

  lines.forEach((rawLine, idx) => {
    const lineNo = idx + 1;
    const line = stripUnescapedComment(rawLine);

    for (let i = 0; i < line.length; i += 1) {
      const ch = line[i];
      if (ch === '\\' && i + 1 < line.length) {
        i += 1;
        continue;
      }
      if (ch === '{') braceBalance += 1;
      else if (ch === '}') {
        braceBalance -= 1;
        if (braceBalance < 0) {
          warnings.push({ line: lineNo, message: 'Unexpected closing brace }' });
          braceBalance = 0;
        }
      } else if (ch === '&' && !/\\(begin|end)\{(tabular|array|align)/.test(line)) {
        warnings.push({ line: lineNo, message: 'Unescaped & — write \\& in LaTeX text' });
        break;
      }
    }

    const beginMatch = line.match(/\\begin\{([a-zA-Z*]+)\}/g);
    if (beginMatch) {
      beginMatch.forEach((m) => {
        const name = m.slice(7, -1);
        envStack.push({ name, line: lineNo });
      });
    }

    const endMatch = line.match(/\\end\{([a-zA-Z*]+)\}/g);
    if (endMatch) {
      endMatch.forEach((m) => {
        const name = m.slice(5, -1);
        const last = envStack[envStack.length - 1];
        if (!last || last.name !== name) {
          warnings.push({ line: lineNo, message: `\\end{${name}} does not match open environment` });
        } else {
          envStack.pop();
        }
      });
    }
  });

  if (braceBalance > 0) {
    warnings.push({ line: lines.length, message: `${braceBalance} unclosed { brace(s)` });
  }
  if (envStack.length > 0) {
    const top = envStack[envStack.length - 1];
    warnings.push({ line: top.line, message: `Unclosed \\begin{${top.name}}` });
  }

  return warnings.slice(0, 4);
}

function splitLatexSections(tex: string): Map<string, string> {
  const sections = new Map<string, string>();
  const lines = tex.split('\n');
  let activeKey = '__preamble__';
  let buffer: string[] = [];

  for (const rawLine of lines) {
    const clean = stripUnescapedComment(rawLine)
      .replace(/\\begin\{document\}|\\end\{document\}/g, '')
      .trimEnd();
    const secIdx = clean.indexOf('\\section');
    if (secIdx !== -1 && (secIdx === 0 || /\s/.test(clean[secIdx - 1]))) {
      const arg = readBracedArg(clean, secIdx + '\\section'.length);
      if (arg) {
        sections.set(activeKey, buffer.join('\n').trim());
        activeKey = unescapeLatex(arg.value).toLowerCase();
        const trailing = clean.slice(arg.nextIndex).trim();
        buffer = trailing ? [trailing] : [];
        continue;
      }
    }
    buffer.push(clean);
  }
  sections.set(activeKey, buffer.join('\n').trim());
  return sections;
}

function findSectionBody(sections: Map<string, string>, keywords: string[]): string | null {
  for (const [key, body] of sections.entries()) {
    if (key === '__preamble__') continue;
    if (keywords.some((kw) => key.includes(kw))) {
      return body;
    }
  }
  return null;
}

function extractItemsFromBlock(block: string): string[] {
  const items: string[] = [];
  const lines = block.split('\n');

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].trim();
    if (!line) continue;

    if (line.includes('\\resumeItem')) {
      const idx = line.indexOf('\\resumeItem');
      const arg = readBracedArg(line, idx + '\\resumeItem'.length);
      if (arg) {
        const txt = unescapeLatex(arg.value);
        if (txt) items.push(txt);
        continue;
      }
    }

    const itemMatch = line.match(/^\\item(?:\[[^\]]*\])?\s+(.+)$/);
    if (itemMatch) {
      const txt = unescapeLatex(itemMatch[1]);
      if (txt) items.push(txt);
    }
  }
  return items;
}

function extractMacroFourArgs(line: string, macro: string): string[] | null {
  const idx = line.indexOf(`\\${macro}`);
  if (idx === -1) return null;
  let cursor = idx + macro.length + 1;
  const args: string[] = [];
  for (let a = 0; a < 4; a += 1) {
    const parsed = readBracedArg(line, cursor);
    if (!parsed) break;
    args.push(unescapeLatex(parsed.value));
    cursor = parsed.nextIndex;
  }
  return args.length >= 2 ? args : null;
}

export function parseLatexToCv(tex: string, fallback: ParsedLatexCv): ParsedLatexCv {
  const warnings = lintLatexSource(tex);
  const sections = splitLatexSections(tex);

  // Header parsing
  let fullName = fallback.fullName;
  let headlineLine = fallback.headlineLine;
  let contactLine = fallback.contactLine;
  const centerMatch = tex.match(/\\begin\{center\}([\s\S]*?)\\end\{center\}/);
  if (centerMatch) {
    const centerLines = centerMatch[1]
      .split('\n')
      .map((l) => unescapeLatex(stripUnescapedComment(l)))
      .filter(Boolean);
    if (centerLines[0]) fullName = centerLines[0];
    if (centerLines[1]) headlineLine = centerLines[1];
    if (centerLines[2]) contactLine = centerLines[2];
  }

  // Summary parsing
  const sumRaw = findSectionBody(sections, ['summary', 'profile', 'about']);
  const summary = sumRaw
    ? sumRaw
        .replace(/\\begin\{justify\}|\\end\{justify\}|\\begin\{samepage\}|\\end\{samepage\}/g, '')
        .split('\n')
        .map((l) => unescapeLatex(l))
        .filter(Boolean)
        .join(' ') || fallback.summary
    : fallback.summary;

  // Technical Skills parsing
  const skillRaw = findSectionBody(sections, ['skill', 'competenc']);
  let skillRows = fallback.skillRows;
  if (skillRaw) {
    const parsedRows: ParsedLatexSkillRow[] = [];
    for (const rawLine of skillRaw.split('\n')) {
      const trimmed = rawLine.trim();
      const boldMatch = trimmed.match(/\\textbf\{([^}]+)\}\s*(.+)/);
      if (boldMatch) {
        const label = unescapeLatex(boldMatch[1]).replace(/:$/, '').trim();
        const value = unescapeLatex(boldMatch[2]).replace(/^[:\s]+/, '').trim();
        if (label && value) parsedRows.push({ label, value });
      }
    }
    if (parsedRows.length > 0) skillRows = parsedRows;
  }

  // Experience parsing
  const expRaw = findSectionBody(sections, ['experience', 'work', 'career']);
  let experiences = fallback.experiences;
  if (expRaw) {
    const lines = expRaw.split('\n');
    const collected: ParsedLatexExperience[] = [];
    let current: ParsedLatexExperience | null = null;

    for (let i = 0; i < lines.length; i += 1) {
      const trimmed = lines[i].trim();
      if (!trimmed) continue;

      if (trimmed.includes('\\resumeSubheading')) {
        // Handle multi-line \resumeSubheading by joining up to 3 lines ahead if needed
        const windowStr = lines.slice(i, i + 4).join(' ');
        const args = extractMacroFourArgs(windowStr, 'resumeSubheading');
        if (args) {
          if (current) collected.push(current);
          // Support both canonical {Role}{Company}{Dates}{Location} and cvFitApi {Role, Company}{Dates}{Location}{}
          if (args[0].includes(',') && (!args[3] || args[3] === '')) {
            const parts = args[0].split(',');
            current = {
              role: parts[0]?.trim() || 'Engineer',
              company: parts.slice(1).join(',').trim() || 'Company',
              dates: args[1] || '',
              location: args[2] || '',
              bullets: [],
            };
          } else {
            current = {
              role: args[0] || 'Engineer',
              company: args[1] || 'Company',
              dates: args[2] || '',
              location: args[3] || '',
              bullets: [],
            };
          }
          continue;
        }
      }

      const items = extractItemsFromBlock(trimmed);
      if (items.length > 0) {
        if (!current) {
          current = {
            role: fallback.experiences[0]?.role || 'Experience',
            company: fallback.experiences[0]?.company || '',
            dates: fallback.experiences[0]?.dates || '',
            location: fallback.experiences[0]?.location || '',
            bullets: [],
          };
        }
        current.bullets.push(...items);
      }
    }
    if (current) collected.push(current);
    if (collected.length > 0) {
      experiences = collected;
    }
  }

  const flatBullets = experiences.flatMap((e) => e.bullets).filter(Boolean);

  // Projects parsing
  const projRaw = findSectionBody(sections, ['project']);
  let projects = fallback.projects;
  if (projRaw) {
    const parsedProjects: ParsedLatexProject[] = [];
    const lines = projRaw.split('\n');
    let activeProj: ParsedLatexProject | null = null;

    for (const rawLine of lines) {
      const trimmed = rawLine.trim();
      if (trimmed.includes('\\resumeProjectHeading')) {
        const args = extractMacroFourArgs(trimmed, 'resumeProjectHeading');
        if (args) {
          if (activeProj) parsedProjects.push(activeProj);
          const nameParts = args[0].split('|').map((s) => s.trim());
          activeProj = {
            name: nameParts[0] || args[0],
            tech: nameParts[1] || args[1] || undefined,
            summary: '',
          };
          continue;
        }
      }
      const items = extractItemsFromBlock(trimmed);
      if (items.length > 0 && activeProj) {
        activeProj.summary = activeProj.summary ? `${activeProj.summary} ${items[0]}` : items[0];
      }
    }
    if (activeProj) parsedProjects.push(activeProj);
    if (parsedProjects.length > 0) projects = parsedProjects;
  }

  // Education parsing
  const eduRaw = findSectionBody(sections, ['education']);
  let education = fallback.education;
  if (eduRaw) {
    const parsedEdu: ParsedLatexEducation[] = [];
    const lines = eduRaw.split('\n');
    for (let i = 0; i < lines.length; i += 1) {
      if (lines[i].includes('\\resumeSubheading')) {
        const args = extractMacroFourArgs(lines.slice(i, i + 4).join(' '), 'resumeSubheading');
        if (args) {
          const rightPart = [args[2], args[3]].filter(Boolean).join(' · ');
          parsedEdu.push({
            title: args[0],
            subtitle: [args[1], rightPart].filter(Boolean).join(' · '),
          });
        }
      }
    }
    if (parsedEdu.length > 0) education = parsedEdu;
  }

  // Certificates & Languages parsing (handles both combined and separate sections)
  const certRaw = findSectionBody(sections, ['certif']);
  const langRaw = findSectionBody(sections, ['language']);
  let certs = fallback.certs;
  let languages = fallback.languages;

  if (certRaw) {
    const rawLines = certRaw.split('\n');
    const nextCerts: string[] = [];
    for (let i = 0; i < rawLines.length; i += 1) {
      const trimmed = rawLines[i].trim();
      if (!trimmed || /^\\(resumeSubHeadingListStart|resumeSubHeadingListEnd|begin|end)\b/.test(trimmed)) {
        continue;
      }
      if (trimmed.includes('\\resumeSubheading')) {
        const args = extractMacroFourArgs(rawLines.slice(i, i + 4).join(' '), 'resumeSubheading');
        while (i + 1 < rawLines.length && rawLines[i + 1].trim().startsWith('{')) {
          i += 1;
        }
        if (args) {
          const entry = [args[2] || args[0], args[2] && args[0] ? args[0] : '', args[3]]
            .filter(Boolean)
            .join(' · ');
          if (entry) nextCerts.push(entry);
          continue;
        }
      }
      const cleanLine = unescapeLatex(trimmed);
      if (cleanLine && !/^languages\s*:/i.test(cleanLine)) {
        nextCerts.push(cleanLine);
      } else if (/^languages\s*:/i.test(cleanLine)) {
        languages = cleanLine.replace(/^languages\s*:/i, '').trim();
      }
    }
    if (nextCerts.length > 0) certs = nextCerts;
  }

  if (langRaw && langRaw !== certRaw) {
    const cleanedLangs = langRaw
      .split('\n')
      .map((l) => unescapeLatex(l))
      .filter((l) => Boolean(l) && !/^(begin|end|needspace)\b/i.test(l))
      .map((l) => l.replace(/^languages\s*:\s*/i, '').trim())
      .filter(Boolean);
    if (cleanedLangs.length > 0) {
      languages = cleanedLangs.join(', ');
    }
  }

  return {
    fullName,
    headlineLine,
    contactLine,
    summary,
    skillRows,
    experiences,
    flatBullets: flatBullets.length > 0 ? flatBullets : fallback.flatBullets,
    projects,
    education,
    certs,
    languages,
    warnings,
  };
}

export function computeLatexLineDiff(
  baseTex: string,
  currentTex: string
): { diffs: LatexLineDiff[]; modifiedLineNumbers: Set<number>; changedCount: number } {
  const baseLines = baseTex.split('\n');
  const currLines = currentTex.split('\n');
  const maxLen = Math.max(baseLines.length, currLines.length);
  const diffs: LatexLineDiff[] = [];
  const modifiedLineNumbers = new Set<number>();

  for (let i = 0; i < maxLen; i += 1) {
    const oldLine = baseLines[i];
    const newLine = currLines[i];
    if (oldLine === undefined && newLine !== undefined) {
      if (newLine.trim().length > 0) {
        diffs.push({ lineNumber: i + 1, kind: 'added', newLine });
        modifiedLineNumbers.add(i + 1);
      }
    } else if (oldLine !== undefined && newLine === undefined) {
      if (oldLine.trim().length > 0) {
        diffs.push({ lineNumber: i + 1, kind: 'removed', oldLine });
      }
    } else if (oldLine !== undefined && newLine !== undefined && oldLine.trimEnd() !== newLine.trimEnd()) {
      diffs.push({ lineNumber: i + 1, kind: 'modified', oldLine, newLine });
      modifiedLineNumbers.add(i + 1);
    }
  }

  return {
    diffs,
    modifiedLineNumbers,
    changedCount: diffs.length,
  };
}
