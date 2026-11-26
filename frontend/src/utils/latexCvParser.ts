import type {
  UserProfilePayload,
  Education,
  ExperienceHighlight,
  FeaturedProject,
  Certification,
  LanguageProficiency,
  SkillsAndTools,
  CustomSection,
  CustomSectionItem,
} from '../services/profileApi';

export interface LatexParseStats {
  has_name: boolean;
  has_email: boolean;
  has_phone: boolean;
  links_count: number;
  experience_count: number;
  education_count: number;
  skills_count: number;
  projects_count: number;
  certifications_count: number;
  custom_sections_count?: number;
  custom_sections_titles?: string[];
}

export interface LatexParseResult {
  profile: Partial<UserProfilePayload>;
  stats: LatexParseStats;
}

export function stripLatexComments(tex: string): string {
  if (!tex) return '';
  return tex.replace(/(?<!\\)%[^\n]*/g, '');
}

export function extractDocumentBody(tex: string): string {
  const cleanTex = stripLatexComments(tex);
  const beginMatch = /\\begin\{document\}/.exec(cleanTex);
  const endMatch = /\\end\{document\}/.exec(cleanTex);
  if (beginMatch && endMatch && beginMatch.index + beginMatch[0].length < endMatch.index) {
    return cleanTex.slice(beginMatch.index + beginMatch[0].length, endMatch.index);
  }
  if (beginMatch) {
    return cleanTex.slice(beginMatch.index + beginMatch[0].length);
  }
  return cleanTex;
}

interface MacroCallMatch {
  args: string[];
  start: number;
  end: number;
}

function extractMacroCalls(tex: string, macroName: string, numArgs: number): MacroCallMatch[] {
  const results: MacroCallMatch[] = [];
  const pattern = new RegExp(`\\\\${macroName}\\b`, 'g');
  let m: RegExpExecArray | null;

  while ((m = pattern.exec(tex)) !== null) {
    const startIdx = m.index;
    let pos = pattern.lastIndex;
    const args: string[] = [];
    let valid = true;

    for (let a = 0; a < numArgs; a++) {
      while (pos < tex.length && /\s/.test(tex[pos])) {
        pos++;
      }
      if (pos >= tex.length || tex[pos] !== '{') {
        valid = false;
        break;
      }
      let depth = 0;
      const argStart = pos + 1;
      let closed = false;
      while (pos < tex.length) {
        const ch = tex[pos];
        if (ch === '\\' && pos + 1 < tex.length) {
          pos += 2;
          continue;
        }
        if (ch === '{') {
          depth++;
        } else if (ch === '}') {
          depth--;
          if (depth === 0) {
            args.push(tex.slice(argStart, pos));
            pos++;
            closed = true;
            break;
          }
        }
        pos++;
      }
      if (!closed) {
        valid = false;
        break;
      }
    }

    if (valid && args.length === numArgs) {
      results.push({ args, start: startIdx, end: pos });
    }
  }

  return results;
}

export function cleanLatex(text: string): string {
  if (!text) return '';
  let s = stripLatexComments(text);
  // Remove environments and brackets
  s = s.replace(/\\(?:begin|end)\{[^}]*\}/g, '');
  s = s.replace(/\\(?:item|newline|titlerule|relax)\b/g, '');
  s = s.replace(/\[[^\]]*\]/g, '');

  // Remove inline Link icons like {\href{...}{Link {\scriptsize\faLink}}}
  s = s.replace(/\{\\href\{[^{}]*\}\{Link\s*(?:\{[^{}]*\})?\}\}/g, '');

  // Escaped characters
  s = s
    .replace(/\\&/g, '&')
    .replace(/\\%/g, '%')
    .replace(/\\\$/g, '$')
    .replace(/\\#/g, '#')
    .replace(/\\_/g, '_')
    .replace(/\\\{/g, '{')
    .replace(/\\\}/g, '}');
  s = s.replace(/\$\|\$/g, '|').replace(/\$/g, '');
  s = s.replace(/\\textbackslash\{\}/g, '\\').replace(/\\textasciitilde\{\}/g, '~');
  s = s.replace(/---/g, '-').replace(/--/g, '-').replace(/~/g, ' ');

  // Href conversion \href{url}{label} -> label
  for (let i = 0; i < 3; i++) {
    s = s.replace(/\\href\{[^{}]*\}\{([^{}]*)\}/g, '$1');
  }
  s = s.replace(/\\(?:raisebox|vspace|needspace|hspace)\{[^}]*\}/g, '');
  s = s.replace(/\\fa[A-Za-z0-9]+\b\s*\\?/g, '');

  // Formatting macros (run multiple times for nested macros)
  for (let i = 0; i < 5; i++) {
    s = s.replace(
      /\\(?:textbf|textit|emph|underline|text|textnormal|small|large|Large|LARGE|huge|Huge|scriptsize|footnotesize|normalsize|scshape|bfseries)\{([^{}]*)\}/g,
      '$1'
    );
  }
  s = s.replace(
    /\\(?:textbf|textit|emph|underline|text|textnormal|centering|scshape|bfseries|raggedright|large|Large|LARGE|small|huge|Huge|scriptsize|footnotesize|normalsize)\b/g,
    ''
  );
  s = s.replace(/\\\\(?:\[[^\]]*\])?/g, ' ');
  s = s.replace(/\{/g, '').replace(/\}/g, '');
  return s.replace(/\s+/g, ' ').trim();
}

function splitSections(tex: string): Record<string, string> {
  const body = extractDocumentBody(tex);
  const pattern = /\\section\*?\{([^}]+)\}/g;
  const sections: Record<string, string> = {};
  const matches: { title: string; index: number; end: number }[] = [];

  let m: RegExpExecArray | null;
  while ((m = pattern.exec(body)) !== null) {
    matches.push({
      title: cleanLatex(m[1]).toLowerCase(),
      index: m.index,
      end: pattern.lastIndex,
    });
  }

  if (matches.length > 0) {
    sections['__header__'] = body.slice(0, matches[0].index);
    for (let i = 0; i < matches.length; i++) {
      const start = matches[i].end;
      const end = i + 1 < matches.length ? matches[i + 1].index : body.length;
      sections[matches[i].title] = body.slice(start, end);
    }
  } else {
    sections['__header__'] = body;
  }

  return sections;
}

function extractBulletItems(text: string): string[] {
  const bullets: string[] = [];
  const macroItems = extractMacroCalls(text, 'resumeItem', 1);
  if (macroItems.length > 0) {
    for (const item of macroItems) {
      const cleaned = cleanLatex(item.args[0]);
      if (cleaned && cleaned.length > 10) {
        bullets.push(cleaned);
      }
    }
  } else {
    const lines = text.split('\n');
    for (const line of lines) {
      if (line.includes('\\item')) {
        const cleaned = cleanLatex(line.replace('\\item', ''));
        if (cleaned && cleaned.length > 10) {
          bullets.push(cleaned);
        }
      }
    }
  }
  return bullets;
}

export function parseLatexCvClient(texContent: string): LatexParseResult {
  const cleanFullTex = stripLatexComments(texContent);
  const bodyTex = extractDocumentBody(texContent);
  const sections = splitSections(texContent);
  const header = sections['__header__'] || '';

  // 1. Personal Info
  let fullName = '';
  const namePatterns = [
    /\\(?:huge|Huge|LARGE|Large)\b\s*([^|\\}\n]+?)(?:\s*\|\s*[^}\n]+)?(?=\}|\s*\\\\|\n)/,
    /\{\s*\\(?:huge|Huge|LARGE|Large)\b\s*([^|}]+?)(?:\s*\|\s*[^}]+)?\}/,
    /\\textbf\{\s*\\(?:huge|Huge|LARGE|Large)\b([^|}]+?)(?:\s*\|\s*[^}]+)?\}/,
  ];
  for (const pat of namePatterns) {
    const m = header.match(pat);
    if (m) {
      const candidate = cleanLatex(m[1]).split('|')[0].trim();
      if (candidate && candidate.length >= 2) {
        fullName = candidate;
        break;
      }
    }
  }

  if (!fullName) {
    const fnMatch = cleanFullTex.match(/\\(?:firstname|givenname)\{([^}]+)\}/);
    const lnMatch = cleanFullTex.match(/\\(?:lastname|familyname)\{([^}]+)\}/);
    if (fnMatch && lnMatch) {
      fullName = `${cleanLatex(fnMatch[1])} ${cleanLatex(lnMatch[1])}`.trim();
    } else {
      const nameEnv = cleanFullTex.match(/\\(?:name|author)\{([^}]+)\}/);
      if (nameEnv) fullName = cleanLatex(nameEnv[1]);
    }
  }

  if (!fullName && header.trim()) {
    for (const rawLine of header.split('\n')) {
      const cleanedLine = cleanLatex(rawLine).split('|')[0].trim();
      const wordCount = cleanedLine.split(/\s+/).filter(Boolean).length;
      if (
        cleanedLine &&
        wordCount >= 2 &&
        wordCount <= 5 &&
        !cleanedLine.includes('@') &&
        !/\d/.test(cleanedLine)
      ) {
        fullName = cleanedLine;
        break;
      }
    }
  }

  const headerNormEmail = header.replace(/\\_/g, '_');
  const bodyNormEmail = bodyTex.replace(/\\_/g, '_');
  let email = '';
  const emailHref =
    headerNormEmail.match(/\\href\{(?:mailto:)?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\}/) ||
    bodyNormEmail.match(/\\href\{(?:mailto:)?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\}/);
  if (emailHref) {
    email = emailHref[1].trim().replace(/\.$/, '');
  } else {
    const emailMatch =
      headerNormEmail.match(/\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b/) ||
      bodyNormEmail.match(/\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b/);
    if (emailMatch) email = emailMatch[1].trim().replace(/\.$/, '');
  }

  let phone = '';
  let dialCode = '+20';
  let countryCode = 'EG';
  const phoneMatch = header.match(
    /(?:\\faPhone\b\s*\\?\s*|\\faMobile\b\s*\\?\s*)?(\+[0-9]{1,4}[\s-]?[0-9]{2,4}[\s-]?[0-9]{3,5}[\s-]?[0-9]{3,5}|\b01[0125][0-9]{8}\b)/
  );
  if (phoneMatch) {
    const raw = phoneMatch[1].trim();
    if (raw.startsWith('+20')) {
      dialCode = '+20';
      countryCode = 'EG';
      phone = raw.slice(3).replace(/[\s-]/g, '');
    } else if (raw.startsWith('+966')) {
      dialCode = '+966';
      countryCode = 'SA';
      phone = raw.slice(4).replace(/[\s-]/g, '');
    } else if (raw.startsWith('+971')) {
      dialCode = '+971';
      countryCode = 'AE';
      phone = raw.slice(4).replace(/[\s-]/g, '');
    } else if (raw.startsWith('+974')) {
      dialCode = '+974';
      countryCode = 'QA';
      phone = raw.slice(4).replace(/[\s-]/g, '');
    } else if (raw.startsWith('+1')) {
      dialCode = '+1';
      countryCode = 'US';
      phone = raw.slice(2).replace(/[\s-]/g, '');
    } else if (raw.startsWith('01') && raw.length === 11) {
      dialCode = '+20';
      countryCode = 'EG';
      phone = raw.slice(1);
    } else {
      phone = raw.replace(/[\s-]/g, '');
    }
  }

  const links: Record<string, string> = {};
  const headerLinks = Array.from(header.matchAll(/\\href\{(https?:\/\/[^{}]+)\}/g)).map((m) => m[1]);
  const bodyLinks = Array.from(bodyTex.matchAll(/\\href\{(https?:\/\/[^{}]+)\}/g)).map((m) => m[1]);
  for (const url of [...headerLinks, ...bodyLinks]) {
    const low = url.toLowerCase();
    if (low.includes('linkedin.com/in/') && !links.linkedin) {
      links.linkedin = url;
    } else if (low.includes('github.com/') && !links.github) {
      links.github = url;
    }
  }
  for (const url of headerLinks) {
    const low = url.toLowerCase();
    if (!low.includes('linkedin.com') && !low.includes('github.com') && !low.includes('mailto:') && !links.portfolio) {
      links.portfolio = url;
    }
  }

  // 2. Residence
  let city = 'Cairo';
  let country = 'Egypt';
  if (/new cairo\s*,\s*egypt/i.test(header)) {
    city = 'New Cairo';
    country = 'Egypt';
  } else if (/cairo\s*,\s*egypt/i.test(header)) {
    city = 'Cairo';
    country = 'Egypt';
  } else if (/giza\s*,\s*egypt/i.test(header)) {
    city = 'Giza';
    country = 'Egypt';
  } else if (/alexandria\s*,\s*egypt/i.test(header)) {
    city = 'Alexandria';
    country = 'Egypt';
  } else if (/riyadh\s*,\s*saudi/i.test(header)) {
    city = 'Riyadh';
    country = 'Saudi Arabia';
  } else if (/dubai\s*,\s*(?:uae|united arab emirates)/i.test(header)) {
    city = 'Dubai';
    country = 'United Arab Emirates';
  } else {
    for (const line of header.split('\n')) {
      const cleanedLine = cleanLatex(line);
      if (!cleanedLine || cleanedLine.includes('@') || cleanedLine.includes('|')) continue;
      const parts = cleanedLine.split(',').map((p) => p.trim()).filter(Boolean);
      if (parts.length >= 2) {
        const pCity = parts[parts.length - 2];
        const pCountry = parts[parts.length - 1];
        if (pCity.length > 2 && pCity.length <= 30 && pCountry.length > 2 && pCountry.length <= 30 && !/\d/.test(pCountry)) {
          city = pCity;
          country = pCountry;
          break;
        }
      }
    }
  }

  // 3. Target Title & Bio
  let targetTitle = '';
  const titleHeaderMatch = header.match(/\\(?:huge|Huge|LARGE|Large)\b[^|}\n]+?\|\s*([^}\n\\]+)/);
  if (titleHeaderMatch) {
    targetTitle = cleanLatex(titleHeaderMatch[1]);
  }

  let summaryBio = '';
  for (const [secName, content] of Object.entries(sections)) {
    if (['profile', 'summary', 'objective', 'about'].some((k) => secName.includes(k))) {
      let cleaned = cleanLatex(content);
      if (targetTitle && cleaned.toLowerCase().startsWith(targetTitle.toLowerCase())) {
        const remainder = cleaned.slice(targetTitle.length).trim();
        if (/^[:\-–—|]/.test(remainder)) {
          cleaned = remainder.replace(/^[:\-–—|\s]+/, '').trim();
        }
      }
      summaryBio = cleaned.slice(0, 800);
      break;
    }
  }

  // 4. Experiences
  const experiences: ExperienceHighlight[] = [];
  let expText = '';
  for (const [secName, content] of Object.entries(sections)) {
    if (['experience', 'employment', 'work', 'career'].some((k) => secName.includes(k))) {
      expText = content;
      break;
    }
  }

  if (expText) {
    const subheadings = extractMacroCalls(expText, 'resumeSubheading', 4);
    if (subheadings.length > 0) {
      for (let i = 0; i < subheadings.length; i++) {
        const match = subheadings[i];
        const arg1 = cleanLatex(match.args[0]);
        const arg2 = cleanLatex(match.args[1]);
        const arg3 = cleanLatex(match.args[2]);
        const arg4 = cleanLatex(match.args[3]);

        const blockStart = match.end;
        const blockEnd = i + 1 < subheadings.length ? subheadings[i + 1].start : expText.length;
        const bullets = extractBulletItems(expText.slice(blockStart, blockEnd));

        let role = arg1;
        let company = arg3 || 'Company';
        if (arg1.includes(',')) {
          const idx = arg1.indexOf(',');
          role = arg1.slice(0, idx).trim();
          company = arg1.slice(idx + 1).trim();
        }

        const dateParts = (arg2 || arg4).split(/\s*(?:--|—|–|\bto\b|-)\s*/i);
        const startDate = dateParts[0]?.trim() || '2022-01';
        const endDate = dateParts[1]?.trim() || 'Present';

        experiences.push({
          role: role || 'Engineer',
          company: company || 'Company',
          start_date: startDate,
          end_date: endDate,
          location: arg3 && company !== arg3 ? arg3 : arg4 || 'Cairo, Egypt',
          achievements: bullets,
        });
      }
    } else {
      // Fallback \textbf{Role} -- Company
      const blocks = expText.split(/\\textbf\{/);
      for (const block of blocks.slice(1)) {
        const headerPart = block.split('\n')[0];
        const roleCompany = cleanLatex(headerPart);
        const bullets = extractBulletItems(block);
        const parts = roleCompany.split(/\s*(?:--|—|–|\||@|\\hfill)\s*/);
        const role = parts[0]?.trim() || 'Software Engineer';
        const company = parts[1]?.trim() || 'Company';

        experiences.push({
          role,
          company,
          start_date: '2021-01',
          end_date: 'Present',
          location: 'Cairo, Egypt',
          achievements: bullets,
        });
      }
    }
  }

  // 5. Education
  const education: Education[] = [];
  let eduText = '';
  for (const [secName, content] of Object.entries(sections)) {
    if (['education', 'academic', 'university'].some((k) => secName.includes(k))) {
      eduText = content;
      break;
    }
  }

  if (eduText) {
    const subheadings = extractMacroCalls(eduText, 'resumeSubheading', 4);
    if (subheadings.length > 0) {
      for (const s of subheadings) {
        const c1 = cleanLatex(s.args[0]);
        const c2 = cleanLatex(s.args[1]);
        const c3 = cleanLatex(s.args[2]);
        const c4 = cleanLatex(s.args[3]);

        const degree = ['b.s', 'b.a', 'bachelor', 'm.s', 'master', 'phd', 'science', 'engineering', 'degree'].some(
          (w) => c1.toLowerCase().includes(w)
        )
          ? c1
          : c3;
        const institution = degree === c1 ? c3 : c1;

        const yearMatches = Array.from(`${c2} ${c4}`.matchAll(/\b(20\d{2}|19\d{2})\b/g));
        const gradYear = yearMatches.length > 0 ? parseInt(yearMatches[yearMatches.length - 1][1], 10) : 2023;

        const gradeMatch = eduText.match(/(?:Grade|GPA|Honors?):\s*([^\n\\}]+)/i);
        const gpa = gradeMatch ? cleanLatex(gradeMatch[1]) : '';

        let fieldOfStudy = 'Computer Science';
        if (degree.includes(' - ')) {
          fieldOfStudy = degree.split(' - ')[1].trim();
        } else {
          const inMatch = degree.match(/\b(?:in|of)\s+(.+)$/i);
          if (inMatch) fieldOfStudy = inMatch[1].trim();
        }

        education.push({
          institution: institution || 'University',
          degree: degree || "Bachelor's Degree",
          field_of_study: fieldOfStudy,
          graduation_year: gradYear,
          grade_or_gpa: gpa,
        });
      }
    } else {
      const yearMatches = Array.from(eduText.matchAll(/\b(20\d{2}|19\d{2})\b/g));
      const gradYear = yearMatches.length > 0 ? parseInt(yearMatches[yearMatches.length - 1][1], 10) : 2023;
      education.push({
        institution: 'University',
        degree: 'B.S. in Computer Science',
        field_of_study: 'Computer Science',
        graduation_year: gradYear,
        grade_or_gpa: '',
      });
    }
  }

  // 6. Skills
  let skillsText = '';
  for (const [secName, content] of Object.entries(sections)) {
    if (['skill', 'technologies', 'competencies'].some((k) => secName.includes(k))) {
      skillsText = content;
      break;
    }
  }

  const coreSkills: string[] = [];
  const programmingLanguages: string[] = [];
  const frameworks: string[] = [];
  const tools: string[] = [];

  if (skillsText) {
    const lines = skillsText.split('\n');
    for (const line of lines) {
      const cleaned = cleanLatex(line);
      if (!cleaned || cleaned.length < 2) continue;
      if (['beginitemize', 'enditemize', 'resumeitem'].some((w) => cleaned.toLowerCase().includes(w))) {
        continue;
      }

      if (cleaned.includes(':')) {
        const idx = cleaned.indexOf(':');
        const cat = cleaned.slice(0, idx);
        const vals = cleaned.slice(idx + 1);
        const catLower = cat.toLowerCase();
        const rawItems = vals
          .split(/,\s*(?![^()]*\))/)
          .map((item) => cleanLatex(item).trim())
          .filter(Boolean);
        const valid = rawItems.filter(
          (item) => !['begin', 'end', 'margin', 'label', 'samepage'].some((w) => item.toLowerCase().includes(w))
        );

        if (catLower.includes('language') || catLower.includes('programming')) {
          programmingLanguages.push(...valid);
        } else if (
          ['framework', 'librar', 'ai', 'machine learning', 'analytics', 'visualization'].some((w) =>
            catLower.includes(w)
          )
        ) {
          frameworks.push(...valid);
          coreSkills.push(...valid.slice(0, 4));
        } else if (['data engineering', 'core', 'competenc'].some((w) => catLower.includes(w))) {
          coreSkills.push(...valid);
          tools.push(...valid);
        } else if (['tool', 'cloud', 'devops', 'mlops', 'platform', 'database', 'vector'].some((w) => catLower.includes(w))) {
          tools.push(...valid);
        } else {
          coreSkills.push(...valid);
        }
      } else {
        const items = cleaned
          .split(/,\s*(?![^()]*\))/)
          .map((item) => cleanLatex(item).trim())
          .filter(Boolean);
        if (items.length > 1) {
          coreSkills.push(...items);
        }
      }
    }
  }

  const dedup = (arr: string[]) => Array.from(new Set(arr.filter((s) => s.length > 1)));

  const cleanCore = dedup(
    coreSkills.length > 0 ? coreSkills : programmingLanguages.length > 0 ? programmingLanguages.slice(0, 4) : tools.slice(0, 6)
  );
  const cleanLangs = dedup(programmingLanguages);
  const cleanFrames = dedup(frameworks);
  const cleanTools = dedup(tools);

  const skillsAndTools: SkillsAndTools = {
    core_skills: cleanCore,
    programming_languages: cleanLangs,
    frameworks_and_libraries: cleanFrames,
    tools_and_platforms: cleanTools,
  };

  // 7. Projects
  const featuredProjects: FeaturedProject[] = [];
  const candidateProjTexts: string[] = [];
  for (const [secName, content] of Object.entries(sections)) {
    if (secName.includes('project')) {
      candidateProjTexts.push(content);
    }
  }
  for (const [secName, content] of Object.entries(sections)) {
    if (!secName.includes('project') && content.includes('\\resumeProjectHeading')) {
      candidateProjTexts.push(content);
    }
  }

  for (const projText of candidateProjTexts) {
    const headings = extractMacroCalls(projText, 'resumeProjectHeading', 2);
    for (let i = 0; i < headings.length; i++) {
      const match = headings[i];
      const headerText = cleanLatex(match.args[0]);
      const parts = headerText.split('|');
      const name = parts[0]?.trim() || 'Software Project';
      let stack = parts[1]
        ? parts[1]
            .split(/,\s*(?![^()]*\))/)
            .map((s) => s.trim())
            .filter((s) => Boolean(s) && !s.toLowerCase().startsWith('grade'))
        : [];

      const blockStart = match.end;
      const blockEnd = i + 1 < headings.length ? headings[i + 1].start : projText.length;
      const bullets = extractBulletItems(projText.slice(blockStart, blockEnd));

      const filteredBullets: string[] = [];
      for (const b of bullets) {
        if (/^(?:tech stack|stack):/i.test(b)) {
          const extracted = b
            .split(':')[1]
            ?.split(/,\s*(?![^()]*\))/)
            .map((s) => s.trim())
            .filter(Boolean);
          if (extracted && extracted.length > 0 && stack.length === 0) {
            stack = extracted;
          }
        } else {
          filteredBullets.push(b);
        }
      }

      featuredProjects.push({
        name,
        tech_stack: stack.length > 0 ? stack : ['Python'],
        summary: filteredBullets.length > 0 ? filteredBullets.join(' ') : `Engineered ${name}.`,
        link: '',
      });
    }
  }

  // 8. Certifications
  const certifications: Certification[] = [];
  let certText = '';
  for (const [secName, content] of Object.entries(sections)) {
    if (['certificat', 'licens'].some((w) => secName.includes(w))) {
      certText = content;
      break;
    }
  }

  if (certText) {
    const certSubheadings = extractMacroCalls(certText, 'resumeSubheading', 4);
    for (const s of certSubheadings) {
      const c1 = cleanLatex(s.args[0]);
      const c2 = cleanLatex(s.args[1]);
      const c3 = cleanLatex(s.args[2]);
      const c4 = cleanLatex(s.args[3]);
      const name = c3 || c1;
      const issuer = name === c3 ? c1 : c3 || 'Verified Issuer';
      certifications.push({
        name,
        issuer,
        issue_date: c4 || c2 || '',
      });
    }
  }

  // 9. Languages
  let languages: LanguageProficiency[] = [
    { language: 'Arabic', proficiency: 'Native' },
    { language: 'English', proficiency: 'Fluent' },
  ];
  let langText = '';
  for (const [secName, content] of Object.entries(sections)) {
    if (secName.includes('language')) {
      langText = content;
      break;
    }
  }
  if (langText) {
    const preSplit = langText.replace(/\\newline\b|\\\\/g, '\n');
    const foundLangs: LanguageProficiency[] = [];
    for (const rawChunk of preSplit.split(/[,•|\n]+/)) {
      let item = cleanLatex(rawChunk).trim();
      if (!item) continue;
      let prof = 'Fluent';
      for (const p of ['Native', 'Fluent', 'Professional Working', 'Professional', 'Intermediate', 'Conversational']) {
        if (item.toLowerCase().includes(p.toLowerCase())) {
          prof = p;
          item = item.replace(new RegExp(`\\(${p}\\)|${p}`, 'gi'), '').trim();
          break;
        }
      }
      item = item.replace(/^[:\-–—\s]+|[:\-–—\s]+$/g, '').trim();
      if (item) {
        foundLangs.push({ language: item, proficiency: prof });
      }
    }
    if (foundLangs.length > 0) {
      languages = foundLangs;
    }
  }

  // 10. Custom & Additional Sections (Publications, Awards, Volunteering, Patents, etc.)
  const customSections = parseCustomSections(bodyTex);

  if (!targetTitle && experiences.length > 0) {
    targetTitle = experiences[0].role;
  }

  const stats: LatexParseStats = {
    has_name: Boolean(fullName),
    has_email: Boolean(email),
    has_phone: Boolean(phone),
    links_count: Object.keys(links).length,
    experience_count: experiences.length,
    education_count: education.length,
    skills_count: cleanCore.length + cleanLangs.length + cleanFrames.length + cleanTools.length,
    projects_count: featuredProjects.length,
    certifications_count: certifications.length,
    custom_sections_count: customSections.length,
    custom_sections_titles: customSections.map((s) => s.section_title),
  };

  const parsedProfile: Partial<UserProfilePayload> = {
    personal_info: {
      full_name: fullName,
      primary_email: email,
      contact_numbers: phone
        ? [
            {
              country_code: countryCode,
              dial_code: dialCode,
              phone_number: phone,
              is_primary: true,
              label: 'Primary Contact',
            },
          ]
        : [],
      links,
    },
    residence_and_mobility: {
      current_residence: { city, country },
      willing_to_relocate: true,
      target_locations: [
        {
          location_id: `loc_${city.toLowerCase().replace(/\s+/g, '_')}`,
          city,
          country,
          work_modes: ['Hybrid', 'Remote'],
          is_active_for_search: true,
        },
      ],
    },
    education,
    languages,
    custom_sections: customSections,
    career_personas: [
      {
        persona_id: 'persona_primary',
        target_title: targetTitle || 'Software Engineer',
        alternative_titles: [],
        is_primary: true,
        seniority_level: ['senior', 'lead', 'principal', 'staff', 'manager'].some((w) =>
          (targetTitle || '').toLowerCase().includes(w)
        )
          ? 'Senior'
          : 'Mid-Level',
        years_of_experience: Math.max(experiences.length * 2, 2),
        summary_bio:
          summaryBio ||
          `Experienced ${targetTitle || 'Engineer'} with expertise in ${skillsAndTools.core_skills.slice(0, 4).join(', ')}.`,
        skills_and_tools: skillsAndTools,
        experience_highlights: experiences,
        featured_projects: featuredProjects,
        certifications,
      },
    ],
  };

  return {
    profile: parsedProfile,
    stats,
  };
}

function parseCustomSections(bodyTex: string): CustomSection[] {
  const standardKeywords = [
    'education',
    'academic',
    'university',
    'school',
    'experience',
    'employment',
    'work',
    'history',
    'career',
    'skill',
    'technical',
    'technologies',
    'competenc',
    'tools',
    'project',
    'certificat',
    'license',
    'credential',
    'language',
    'summary',
    'objective',
    'about',
    'profile',
    'bio',
  ];

  const pattern = /\\section\*?\{([^}]+)\}/g;
  const matches: { title: string; rawTitle: string; index: number; end: number }[] = [];
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(bodyTex)) !== null) {
    matches.push({
      title: cleanLatex(m[1]).toLowerCase(),
      rawTitle: cleanLatex(m[1]),
      index: m.index,
      end: pattern.lastIndex,
    });
  }

  const customSections: CustomSection[] = [];

  for (let i = 0; i < matches.length; i++) {
    const { title, rawTitle, end } = matches[i];
    if (standardKeywords.some((k) => title.includes(k))) {
      continue;
    }

    const nextStart = i + 1 < matches.length ? matches[i + 1].index : bodyTex.length;
    const rawSection = bodyTex.slice(end, nextStart);
    if (!rawSection.trim()) continue;

    const items: CustomSectionItem[] = [];

    const shMatches = extractMacroCalls(rawSection, 'resumeSubheading', 4);
    if (shMatches.length > 0) {
      for (let j = 0; j < shMatches.length; j++) {
        const sh = shMatches[j];
        const nextIdx = j + 1 < shMatches.length ? shMatches[j + 1].start : rawSection.length;
        const block = rawSection.slice(sh.end, nextIdx);
        const bullets = extractBulletItems(block);
        items.push({
          id: `item_${j + 1}`,
          title: cleanLatex(sh.args[0]) || 'Entry',
          date: cleanLatex(sh.args[1]),
          subtitle: cleanLatex(sh.args[2]),
          location_or_link: cleanLatex(sh.args[3]),
          description: '',
          bullet_points: bullets,
        });
      }
    } else if (rawSection.includes('\\resumeProjectHeading')) {
      const pMatches = extractMacroCalls(rawSection, 'resumeProjectHeading', 2);
      for (let idx = 0; idx < pMatches.length; idx++) {
        const pm = pMatches[idx];
        const header = cleanLatex(pm.args[0]);
        const dateVal = cleanLatex(pm.args[1]);
        const parts = header.split('|');
        const nextIdx = idx + 1 < pMatches.length ? pMatches[idx + 1].start : rawSection.length;
        const bullets = extractBulletItems(rawSection.slice(pm.end, nextIdx));
        items.push({
          id: `item_${idx + 1}`,
          title: parts[0]?.trim() || 'Entry',
          subtitle: parts[1]?.trim() || '',
          date: dateVal,
          location_or_link: '',
          description: '',
          bullet_points: bullets,
        });
      }
    } else if (rawSection.includes('\\item')) {
      const splitItems = rawSection.split(/\\item\b/).slice(1);
      splitItems.forEach((it, idx) => {
        const cleaned = cleanLatex(it);
        if (!cleaned) return;

        const dateMatch = cleaned.match(/\b(19\d{2}|20\d{2})(?:\s*[-–—]\s*(?:Present|19\d{2}|20\d{2}))?\b/);
        const dateStr = dateMatch ? dateMatch[0] : '';

        const linkMatch = it.match(/\\href\{([^}]+)\}/);
        const linkStr = linkMatch ? linkMatch[1] : '';

        const parts = cleaned.split('|').map((p) => p.trim()).filter(Boolean);
        const titleStr = parts[0] || cleaned;
        const subStr = parts.length > 1 ? parts[1] : '';

        items.push({
          id: `item_${idx + 1}`,
          title: titleStr,
          subtitle: subStr,
          date: dateStr,
          location_or_link: linkStr,
          description: '',
          bullet_points: [],
        });
      });
    } else {
      const cleaned = cleanLatex(rawSection);
      if (cleaned) {
        items.push({
          id: 'item_1',
          title: rawTitle,
          subtitle: '',
          date: '',
          location_or_link: '',
          description: cleaned,
          bullet_points: [],
        });
      }
    }

    customSections.push({
      id: `sec_${title.replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')}`,
      section_title: rawTitle,
      section_type: 'items',
      content_text: cleanLatex(rawSection),
      items,
    });
  }

  return customSections;
}
