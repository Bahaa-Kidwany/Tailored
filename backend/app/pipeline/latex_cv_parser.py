import re
from typing import Dict, List, Any, Optional, Tuple


def strip_latex_comments(tex: str) -> str:
    """Removes unescaped LaTeX % comments while preserving escaped \\% characters."""
    if not tex:
        return ""
    return re.sub(r"(?<!\\)%[^\n]*", "", tex)


def extract_document_body(tex: str) -> str:
    """
    Extracts the LaTeX body between \\begin{document} and \\end{document}
    so preamble macro definitions (\\newcommand, \\titleformat, etc.) are never
    mistaken for candidate content.
    """
    clean_tex = strip_latex_comments(tex)
    begin_match = re.search(r"\\begin\{document\}", clean_tex)
    end_match = re.search(r"\\end\{document\}", clean_tex)
    if begin_match and end_match and begin_match.end() < end_match.start():
        return clean_tex[begin_match.end():end_match.start()]
    if begin_match:
        return clean_tex[begin_match.end():]
    return clean_tex


def extract_macro_calls(tex: str, macro_name: str, num_args: int) -> List[Tuple[List[str], int, int]]:
    """
    Finds all occurrences of `\\macro_name{arg1}...{argN}` using balanced brace matching,
    correctly handling arbitrarily nested braces like `{\\href{...}{Link {\\scriptsize\\faLink}}}`.
    Returns a list of (args_list, match_start_index, match_end_index).
    """
    results: List[Tuple[List[str], int, int]] = []
    pattern = re.compile(rf"\\{ re.escape(macro_name) }\b")

    for m in pattern.finditer(tex):
        start_idx = m.start()
        pos = m.end()
        args: List[str] = []
        valid = True

        for _ in range(num_args):
            while pos < len(tex) and tex[pos].isspace():
                pos += 1
            if pos >= len(tex) or tex[pos] != "{":
                valid = False
                break
            depth = 0
            arg_start = pos + 1
            while pos < len(tex):
                ch = tex[pos]
                if ch == "\\" and pos + 1 < len(tex):
                    pos += 2
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        args.append(tex[arg_start:pos])
                        pos += 1
                        break
                pos += 1
            else:
                valid = False
                break

        if valid and len(args) == num_args:
            results.append((args, start_idx, pos))

    return results


def clean_latex(text: str) -> str:
    """Strips LaTeX formatting commands and normalizes characters into clean text."""
    if not text:
        return ""
    s = strip_latex_comments(text)
    # Remove environments and brackets
    s = re.sub(r"\\(?:begin|end)\{[^}]*\}", "", s)
    s = re.sub(r"\\(?:item|newline|titlerule|relax)\b", "", s)
    s = re.sub(r"\[[^\]]*\]", "", s)

    # Remove inline Link icons like {\href{...}{Link {\scriptsize\faLink}}}
    s = re.sub(r"\{\\href\{[^{}]*\}\{Link\s*(?:\{[^{}]*\})?\}\}", "", s)

    # Escaped characters
    s = s.replace(r"\&", "&").replace(r"\%", "%").replace(r"\$", "$").replace(r"\#", "#").replace(r"\_", "_")
    s = s.replace("$|$", "|").replace("$", "")
    s = s.replace(r"\{", "{").replace(r"\}", "}")
    s = s.replace(r"\textbackslash{}", "\\").replace(r"\textasciitilde{}", "~").replace(r"\textasciicircum{}", "^")
    s = s.replace("---", "-").replace("--", "-").replace("~", " ")

    # Href conversion \href{url}{label} -> label
    for _ in range(3):
        s = re.sub(r"\\href\{[^{}]*\}\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\(?:raisebox|vspace|needspace|hspace)\{[^}]*\}", "", s)
    s = re.sub(r"\\fa[A-Za-z0-9]+\b\s*\\?", "", s)
    for _ in range(5):
        s = re.sub(
            r"\\(?:textbf|textit|emph|underline|text|textnormal|small|large|Large|LARGE|huge|Huge|scriptsize|footnotesize|normalsize|scshape|bfseries)\{([^{}]*)\}",
            r"\1",
            s,
        )
    s = re.sub(
        r"\\(?:textbf|textit|emph|underline|text|textnormal|centering|scshape|bfseries|raggedright|large|Large|LARGE|small|huge|Huge|scriptsize|footnotesize|normalsize)\b",
        "",
        s,
    )
    s = re.sub(r"\\\\(?:\[[^\]]*\])?", " ", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def split_sections(tex: str) -> Dict[str, str]:
    """Splits a LaTeX document body by its \\section or \\section* headings."""
    body = extract_document_body(tex)
    pattern = r"\\section\*?\{([^}]+)\}"
    matches = list(re.finditer(pattern, body))
    sections: Dict[str, str] = {}

    # Text before the first section in the document body is the header / contact block
    if matches:
        header_text = body[:matches[0].start()]
        sections["__header__"] = header_text
        for i, match in enumerate(matches):
            title = clean_latex(match.group(1)).lower()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            sections[title] = body[start:end]
    else:
        sections["__header__"] = body

    return sections


class LatexCvParser:
    """
    Parses LaTeX CV / Resume source code (including Jake Gutierrez format, ModernCV,
    and standard article CV formats) into a structured UserProfile representation.
    """

    def parse(self, tex_content: str) -> Dict[str, Any]:
        clean_full_tex = strip_latex_comments(tex_content)
        body_tex = extract_document_body(tex_content)
        sections = split_sections(tex_content)
        header_text = sections.get("__header__", "")

        # 1. Parse Personal Info from Header
        personal_info = self._parse_personal_info(header_text, body_tex, clean_full_tex)

        # 2. Parse Residence and Target Locations
        residence = self._parse_residence(header_text)

        # 3. Parse Career Summary / Persona Bio
        target_title, summary_bio = self._parse_summary(sections, header_text)

        # 4. Parse Education
        education = self._parse_education(sections)

        # 5. Parse Work Experience
        experiences = self._parse_experiences(sections)

        # 6. Parse Technical Skills
        skills = self._parse_skills(sections)

        # 7. Parse Projects (including any graduation projects under Education)
        projects = self._parse_projects(sections)

        # 8. Parse Certifications
        certifications = self._parse_certifications(sections)

        # 9. Parse Languages
        languages = self._parse_languages(sections)

        # 10. Parse Custom & Additional Sections (Publications, Awards, Volunteering, Patents, etc.)
        custom_sections = self._parse_custom_sections(body_tex)

        # If target title wasn't in header, try first experience role
        if not target_title and experiences:
            target_title = experiences[0]["role"]

        # Assemble Career Persona
        career_persona = {
            "persona_id": "persona_primary",
            "target_title": target_title or "Software Engineer",
            "alternative_titles": [],
            "is_primary": True,
            "seniority_level": (
                "Senior"
                if any(w in (target_title or "").lower() for w in ["senior", "lead", "staff", "principal", "manager"])
                else "Mid-Level"
            ),
            "years_of_experience": max(len(experiences) * 2, 2) if experiences else 2,
            "summary_bio": (
                summary_bio
                or f"Experienced {target_title or 'Engineer'} with expertise in {', '.join(skills['core_skills'][:4]) if skills['core_skills'] else 'software engineering'}."
            ),
            "skills_and_tools": skills,
            "experience_highlights": experiences,
            "featured_projects": projects,
            "certifications": certifications,
        }

        stats = {
            "has_name": bool(personal_info["full_name"]),
            "has_email": bool(personal_info["primary_email"]),
            "has_phone": bool(personal_info["contact_numbers"] and personal_info["contact_numbers"][0]["phone_number"]),
            "links_count": len(personal_info["links"]),
            "experience_count": len(experiences),
            "education_count": len(education),
            "skills_count": (
                len(skills["core_skills"])
                + len(skills["programming_languages"])
                + len(skills["frameworks_and_libraries"])
                + len(skills["tools_and_platforms"])
            ),
            "projects_count": len(projects),
            "certifications_count": len(certifications),
            "custom_sections_count": len(custom_sections),
            "custom_sections_titles": [s["section_title"] for s in custom_sections],
        }

        return {
            "personal_info": personal_info,
            "residence_and_mobility": residence,
            "education": education,
            "languages": languages,
            "career_personas": [career_persona],
            "custom_sections": custom_sections,
            "stats": stats,
        }

    def _parse_personal_info(self, header: str, body_tex: str, clean_full_tex: str) -> Dict[str, Any]:
        # 1. Name
        full_name = ""
        # Match {\huge Name | Title}, \textbf{\Huge \scshape Name}, {\LARGE Name}, etc. in the body header
        name_patterns = [
            r"\\(?:huge|Huge|LARGE|Large)\b\s*([^|\\}\n]+?)(?:\s*\|\s*[^}\n]+)?(?=\}|\s*\\\\|\n)",
            r"\{\s*\\(?:huge|Huge|LARGE|Large)\b\s*([^|}]+?)(?:\s*\|\s*[^}]+)?\}",
            r"\\textbf\{\s*\\(?:huge|Huge|LARGE|Large)\b([^|}]+?)(?:\s*\|\s*[^}]+)?\}",
        ]
        for pat in name_patterns:
            name_match = re.search(pat, header)
            if name_match:
                candidate = clean_latex(name_match.group(1)).split("|")[0].strip()
                if candidate and len(candidate) >= 2:
                    full_name = candidate
                    break

        if not full_name:
            # Check \name{...} or \firstname{...}\lastname{...} or \author{...}
            fn_m = re.search(r"\\(?:firstname|givenname)\{([^}]+)\}", clean_full_tex)
            ln_m = re.search(r"\\(?:lastname|familyname)\{([^}]+)\}", clean_full_tex)
            if fn_m and ln_m:
                full_name = f"{clean_latex(fn_m.group(1))} {clean_latex(ln_m.group(1))}".strip()
            else:
                m = re.search(r"\\(?:name|author)\{([^}]+)\}", clean_full_tex)
                if m:
                    full_name = clean_latex(m.group(1))

        if not full_name and header.strip():
            # Fallback: first non-empty line in header that looks like a person's name
            for raw_line in header.splitlines():
                cleaned_line = clean_latex(raw_line).split("|")[0].strip()
                if (
                    cleaned_line
                    and 2 <= len(cleaned_line.split()) <= 5
                    and "@" not in cleaned_line
                    and not any(ch.isdigit() for ch in cleaned_line)
                ):
                    full_name = cleaned_line
                    break

        # 2. Email (normalize \_ to _ first so escaped underscores in LaTeX emails match cleanly)
        header_norm_email = header.replace(r"\_", "_")
        body_norm_email = body_tex.replace(r"\_", "_")
        email = ""
        email_regex = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"

        email_href = (
            re.search(rf"\\href\{{(?:mailto:)?{email_regex}\}}", header_norm_email)
            or re.search(rf"\\href\{{(?:mailto:)?{email_regex}\}}", body_norm_email)
        )
        if email_href:
            email = email_href.group(1).strip().rstrip(".")
        else:
            email_match = re.search(rf"\b{email_regex}\b", header_norm_email) or re.search(
                rf"\b{email_regex}\b", body_norm_email
            )
            if email_match:
                email = email_match.group(1).strip().rstrip(".")

        # 3. Phone (search inside document body header, never in preamble/comments)
        phone = ""
        dial_code = "+20"
        country_code = "EG"
        phone_match = re.search(
            r"(?:\\faPhone\b\s*\\?\s*|\\faMobile\b\s*\\?\s*)?(\+[0-9]{1,4}[\s\-]?[0-9]{2,4}[\s\-]?[0-9]{3,5}[\s\-]?[0-9]{3,5}|\b01[0125][0-9]{8}\b)",
            header,
        )
        if phone_match:
            raw_phone = phone_match.group(1).strip()
            if raw_phone.startswith("+"):
                if raw_phone.startswith("+20"):
                    dial_code = "+20"
                    country_code = "EG"
                    phone = raw_phone[3:].strip().replace(" ", "").replace("-", "")
                elif raw_phone.startswith("+966"):
                    dial_code = "+966"
                    country_code = "SA"
                    phone = raw_phone[4:].strip().replace(" ", "").replace("-", "")
                elif raw_phone.startswith("+971"):
                    dial_code = "+971"
                    country_code = "AE"
                    phone = raw_phone[4:].strip().replace(" ", "").replace("-", "")
                elif raw_phone.startswith("+974"):
                    dial_code = "+974"
                    country_code = "QA"
                    phone = raw_phone[4:].strip().replace(" ", "").replace("-", "")
                elif raw_phone.startswith("+1"):
                    dial_code = "+1"
                    country_code = "US"
                    phone = raw_phone[2:].strip().replace(" ", "").replace("-", "")
                else:
                    phone = raw_phone.replace(" ", "").replace("-", "")
            elif raw_phone.startswith("01") and len(raw_phone) == 11:
                dial_code = "+20"
                country_code = "EG"
                phone = raw_phone[1:]
            else:
                phone = raw_phone.replace(" ", "").replace("-", "")

        # 4. Links (LinkedIn, GitHub, Portfolio - search header so project/cert URLs aren't mistaken for portfolio)
        links: Dict[str, str] = {}
        header_hrefs = re.findall(r"\\href\{(https?://[^{}]+)\}", header)
        body_hrefs = re.findall(r"\\href\{(https?://[^{}]+)\}", body_tex)

        for h in header_hrefs + body_hrefs:
            low = h.lower()
            if "linkedin.com/in/" in low and "linkedin" not in links:
                links["linkedin"] = h
            elif "github.com/" in low and "github" not in links:
                links["github"] = h

        for h in header_hrefs:
            low = h.lower()
            if (
                "linkedin.com" not in low
                and "github.com" not in low
                and "mailto:" not in low
                and "@" not in low
                and "portfolio" not in links
            ):
                links["portfolio"] = h

        contact_numbers = (
            [
                {
                    "country_code": country_code,
                    "dial_code": dial_code,
                    "phone_number": phone,
                    "is_primary": True,
                    "label": "Primary Contact",
                }
            ]
            if phone
            else []
        )

        return {
            "full_name": full_name,
            "primary_email": email,
            "contact_numbers": contact_numbers,
            "links": links,
        }

    def _parse_residence(self, header: str) -> Dict[str, Any]:
        city = "Cairo"
        country = "Egypt"
        matched = False

        # First check for a full address line ending with ", Country" (e.g. "El Banafseg 8, New Cairo, Egypt")
        for line in header.splitlines():
            cleaned_line = clean_latex(line)
            if not cleaned_line or "@" in cleaned_line or "|" in cleaned_line or "+" in cleaned_line:
                continue
            if "linkedin" in cleaned_line.lower() or "github" in cleaned_line.lower():
                continue
            parts = [p.strip() for p in cleaned_line.split(",") if p.strip()]
            if len(parts) >= 2:
                potential_country = parts[-1]
                potential_city = ", ".join(parts[:-1]).strip()
                if (
                    2 < len(potential_city) <= 60
                    and 2 < len(potential_country) <= 30
                    and not any(ch.isdigit() for ch in potential_country)
                ):
                    city = potential_city
                    country = potential_country
                    matched = True
                    break

        if not matched:
            loc_patterns = [
                (r"New Cairo\s*,\s*Egypt", "New Cairo", "Egypt"),
                (r"Cairo\s*,\s*Egypt", "Cairo", "Egypt"),
                (r"Giza\s*,\s*Egypt", "Giza", "Egypt"),
                (r"Alexandria\s*,\s*Egypt", "Alexandria", "Egypt"),
                (r"Riyadh\s*,\s*Saudi Arabia", "Riyadh", "Saudi Arabia"),
                (r"Jeddah\s*,\s*Saudi Arabia", "Jeddah", "Saudi Arabia"),
                (r"Dubai\s*,\s*UAE", "Dubai", "United Arab Emirates"),
                (r"Dubai\s*,\s*United Arab Emirates", "Dubai", "United Arab Emirates"),
                (r"Abu Dhabi\s*,\s*UAE", "Abu Dhabi", "United Arab Emirates"),
                (r"Doha\s*,\s*Qatar", "Doha", "Qatar"),
                (r"London\s*,\s*UK", "London", "United Kingdom"),
            ]
            for pat, c, cntry in loc_patterns:
                if re.search(pat, header, re.IGNORECASE):
                    city = c
                    country = cntry
                    break

        short_city = city.split(",")[-1].strip() if "," in city else city
        return {
            "current_residence": {"city": city, "country": country},
            "willing_to_relocate": True,
            "target_locations": [
                {
                    "location_id": f"loc_{short_city.lower().replace(' ', '_')}",
                    "city": short_city,
                    "country": country,
                    "work_modes": ["Hybrid", "Remote"],
                    "is_active_for_search": True,
                }
            ],
        }

    def _parse_summary(self, sections: Dict[str, str], header: str) -> tuple[str, str]:
        target_title = ""
        title_match = re.search(
            r"\\(?:huge|Huge|LARGE|Large)\b[^|}\n]+?\|\s*([^}\n\\]+)",
            header,
        )
        if title_match:
            target_title = clean_latex(title_match.group(1))

        summary_bio = ""
        for sec_name, content in sections.items():
            if any(k in sec_name for k in ["profile", "summary", "objective", "about"]):
                clean_text = clean_latex(content)
                if target_title and clean_text.lower().startswith(target_title.lower()):
                    remainder = clean_text[len(target_title):].strip()
                    # Only strip target_title prefix if followed by a separator (e.g. ":" or "-" or "|"),
                    # not when it's the subject of the sentence ("Data Engineer with a proven track record...")
                    if remainder.startswith((":", "-", "–", "—", "|")):
                        clean_text = remainder.lstrip(":-–—| ").strip()
                summary_bio = clean_text[:800]
                break

        return target_title, summary_bio

    def _parse_experiences(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        experiences: List[Dict[str, Any]] = []

        exp_text = ""
        for sec_name, content in sections.items():
            if any(k in sec_name for k in ["experience", "employment", "work history", "career"]):
                exp_text = content
                break

        if not exp_text:
            return experiences

        # 1. Check for \resumeSubheading blocks using balanced brace parser
        sub_list = extract_macro_calls(exp_text, "resumeSubheading", 4)
        if sub_list:
            for i, (args, _, match_end) in enumerate(sub_list):
                arg1 = clean_latex(args[0])
                arg2 = clean_latex(args[1])
                arg3 = clean_latex(args[2])
                arg4 = clean_latex(args[3])

                block_start = match_end
                block_end = sub_list[i + 1][1] if i + 1 < len(sub_list) else len(exp_text)
                block_text = exp_text[block_start:block_end]

                # Extract optional role intro paragraph before \textbf{Key achievements:} or \resumeItemListStart
                intro_split = re.split(
                    r"\\textbf\{Key achievements:?\}|\\resumeItemListStart",
                    block_text,
                    maxsplit=1,
                )
                role_intro = ""
                if len(intro_split) > 1:
                    candidate_intro = clean_latex(intro_split[0])
                    if candidate_intro and len(candidate_intro) > 15:
                        role_intro = candidate_intro

                achievements = self._extract_bullet_items(block_text)
                if role_intro:
                    achievements.insert(0, f"[Role Summary] {role_intro}")

                role, company = self._disentangle_role_company(arg1, arg3)
                start_date, end_date = self._parse_date_range(arg2 or arg4)
                location = arg3 if (arg3 and company != arg3) else arg4

                experiences.append({
                    "company": company or "Company",
                    "role": role or "Engineer",
                    "start_date": start_date or "2022-01",
                    "end_date": end_date or "Present",
                    "location": location or "",
                    "achievements": achievements,
                })
        else:
            # 2. Check for \textbf{Role} -- Company \hfill Dates format
            blocks = re.split(r"\\textbf\{", exp_text)
            for block in blocks[1:]:
                header_part = block.split("\n")[0]
                role_company = clean_latex(header_part)
                achievements = self._extract_bullet_items(block)

                dates_match = re.search(
                    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[A-Za-z]+)?\s*\d{4}\s*(?:--|—|–|-|\bto\b)\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[A-Za-z]+)?\s*\d{4})|\d{4})",
                    block,
                )
                dates_str = dates_match.group(0) if dates_match else ""
                start_date, end_date = self._parse_date_range(dates_str)

                parts = re.split(r"\s*(?:--|—|–|\||@|\\hfill)\s*", role_company)
                role = parts[0].strip() if parts else "Engineer"
                company = parts[1].strip() if len(parts) > 1 else "Company"

                experiences.append({
                    "company": company,
                    "role": role,
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": "Cairo, Egypt",
                    "achievements": achievements,
                })

        return experiences

    def _parse_education(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        education: List[Dict[str, Any]] = []

        edu_text = ""
        for sec_name, content in sections.items():
            if any(k in sec_name for k in ["education", "academic", "university", "degrees"]):
                edu_text = content
                break

        if not edu_text:
            return education

        # 1. \resumeSubheading blocks in education
        subheadings = extract_macro_calls(edu_text, "resumeSubheading", 4)
        if subheadings:
            for args, _, _ in subheadings:
                c1, c2, c3, c4 = [clean_latex(x) for x in args]
                degree = (
                    c1
                    if any(
                        w in c1.lower()
                        for w in ["b.s", "b.a", "bachelor", "m.s", "master", "phd", "science", "engineering", "degree"]
                    )
                    else c3
                )
                institution = c3 if degree == c1 else c1

                years = re.findall(r"\b(20\d{2}|19\d{2})\b", f"{c2} {c4}")
                grad_year = int(years[-1]) if years else 2023

                grade_match = re.search(r"(?:Grade|GPA|Honors?):\s*([^\n\\}]+)", edu_text, re.IGNORECASE)
                gpa = clean_latex(grade_match.group(1)) if grade_match else ""

                field_of_study = "Computer Science"
                if " - " in degree:
                    deg_left, deg_right = degree.split(" - ", 1)
                    degree = deg_left.strip()
                    field_of_study = deg_right.strip()
                else:
                    in_match = re.search(r"\b(?:in|of)\s+(.+)$", degree, re.IGNORECASE)
                    if in_match:
                        field_of_study = in_match.group(1).strip()

                education.append({
                    "institution": institution or "University",
                    "degree": degree or "Bachelor's Degree",
                    "field_of_study": field_of_study,
                    "graduation_year": grad_year,
                    "grade_or_gpa": gpa,
                })
        else:
            degree_match = re.search(r"(B\.?S\.?|M\.?S\.?|Bachelor|Master|Ph\.?D)[^,\n\\]+", edu_text)
            degree_str = clean_latex(degree_match.group(0)) if degree_match else "Bachelor's Degree"

            inst_match = re.search(r"(?:at|--|—|-)?\s*([A-Za-z\s\-]+(?:University|College|Institute|Academy))", edu_text)
            inst_str = clean_latex(inst_match.group(1)) if inst_match else "University"

            years = re.findall(r"\b(20\d{2}|19\d{2})\b", edu_text)
            grad_year = int(years[-1]) if years else 2023

            grade_match = re.search(r"(?:Grade|GPA|Honors?):\s*([^\n\\}]+)", edu_text, re.IGNORECASE)
            gpa = clean_latex(grade_match.group(1)) if grade_match else ""

            field_of_study = "Computer Science"
            if " - " in degree_str:
                field_of_study = degree_str.split(" - ", 1)[1].strip()
            else:
                in_match = re.search(r"\b(?:in|of)\s+(.+)$", degree_str, re.IGNORECASE)
                if in_match:
                    field_of_study = in_match.group(1).strip()

            education.append({
                "institution": inst_str,
                "degree": degree_str,
                "field_of_study": field_of_study,
                "graduation_year": grad_year,
                "grade_or_gpa": gpa,
            })

        return education

    def _parse_skills(self, sections: Dict[str, str]) -> Dict[str, List[str]]:
        skills_text = ""
        for sec_name, content in sections.items():
            if any(k in sec_name for k in ["skill", "technologies", "competencies", "technical"]):
                skills_text = content
                break

        core_skills: List[str] = []
        languages: List[str] = []
        frameworks: List[str] = []
        tools: List[str] = []

        if skills_text:
            lines = skills_text.splitlines()
            for line in lines:
                cleaned = clean_latex(line)
                if not cleaned or len(cleaned) < 2:
                    continue
                if any(k in cleaned.lower() for k in ["beginitemize", "enditemize", "resumeitem"]):
                    continue

                if ":" in cleaned:
                    cat, vals = cleaned.split(":", 1)
                    cat_lower = cat.lower()
                    raw_items = [
                        clean_latex(item).strip()
                        for item in re.split(r",\s*(?![^()]*\))", vals)
                        if clean_latex(item).strip()
                    ]

                    valid_items = [
                        item
                        for item in raw_items
                        if not any(
                            w in item.lower() for w in ["begin", "end", "margin", "leftmargin", "label", "samepage"]
                        )
                    ]

                    if any(k in cat_lower for k in ["language", "programming"]):
                        languages.extend(valid_items)
                    elif any(k in cat_lower for k in ["framework", "librar", "ai", "machine learning", "analytics", "visualization"]):
                        frameworks.extend(valid_items)
                        core_skills.extend(valid_items[:4])
                    elif any(k in cat_lower for k in ["data engineering", "core", "competenc"]):
                        core_skills.extend(valid_items)
                        tools.extend(valid_items)
                    elif any(k in cat_lower for k in ["tool", "cloud", "devops", "mlops", "platform", "database", "vector"]):
                        tools.extend(valid_items)
                    else:
                        core_skills.extend(valid_items)
                else:
                    items = [
                        clean_latex(item).strip()
                        for item in re.split(r",\s*(?![^()]*\))", cleaned)
                        if clean_latex(item).strip()
                    ]
                    valid_items = [
                        item
                        for item in items
                        if not any(
                            w in item.lower() for w in ["begin", "end", "margin", "leftmargin", "label", "samepage"]
                        )
                    ]
                    if len(valid_items) > 1:
                        core_skills.extend(valid_items)

        def dedup(arr: List[str]) -> List[str]:
            seen = set()
            out = []
            for a in arr:
                if a and len(a) > 1 and a not in seen:
                    seen.add(a)
                    out.append(a)
            return out

        clean_core = dedup(core_skills or languages[:4] or tools[:6])
        clean_langs = dedup(languages)
        clean_frames = dedup(frameworks)
        clean_tools = dedup(tools)

        return {
            "core_skills": clean_core,
            "programming_languages": clean_langs,
            "frameworks_and_libraries": clean_frames,
            "tools_and_platforms": clean_tools,
        }

    def _parse_projects(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        projects: List[Dict[str, Any]] = []

        # Collect project sections as well as any \resumeProjectHeading inside Education (e.g. Graduation Project)
        candidate_texts: List[str] = []
        for sec_name, content in sections.items():
            if "project" in sec_name:
                candidate_texts.append(content)
        for sec_name, content in sections.items():
            if "project" not in sec_name and "\\resumeProjectHeading" in content:
                candidate_texts.append(content)

        for proj_text in candidate_texts:
            head_list = extract_macro_calls(proj_text, "resumeProjectHeading", 2)
            for i, (args, _, match_end) in enumerate(head_list):
                header = clean_latex(args[0])
                parts = header.split("|")
                name = parts[0].strip()
                stack = (
                    [
                        s.strip()
                        for s in re.split(r",\s*(?![^()]*\))", parts[1])
                        if s.strip() and not s.strip().lower().startswith("grade")
                    ]
                    if len(parts) > 1
                    else []
                )

                block_start = match_end
                block_end = head_list[i + 1][1] if i + 1 < len(head_list) else len(proj_text)
                bullets = self._extract_bullet_items(proj_text[block_start:block_end])

                # If a bullet is "Tech Stack: ...", extract stack from it
                filtered_bullets: List[str] = []
                for b in bullets:
                    if b.lower().startswith(("tech stack:", "stack:")):
                        extracted = [
                            s.strip()
                            for s in re.split(r",\s*(?![^()]*\))", b.split(":", 1)[1])
                            if s.strip()
                        ]
                        if extracted and not stack:
                            stack = extracted
                    else:
                        filtered_bullets.append(b)

                projects.append({
                    "name": name or "Engineering Project",
                    "tech_stack": stack or ["Python"],
                    "summary": "\n".join(filtered_bullets) if filtered_bullets else f"Engineered {name}.",
                    "link": "",
                })

        return projects

    def _parse_certifications(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        certs: List[Dict[str, Any]] = []
        cert_text = ""
        for sec_name, content in sections.items():
            if any(k in sec_name for k in ["certificat", "licens", "credentials"]):
                cert_text = content
                break

        if not cert_text:
            return certs

        subheadings = extract_macro_calls(cert_text, "resumeSubheading", 4)
        for args, _, _ in subheadings:
            c1, c2, c3, c4 = [clean_latex(x) for x in args]
            name = c3 or c1
            issuer = c1 if name == c3 else (c3 or "Verified Issuer")
            date_str = c4 or c2 or ""
            certs.append({
                "name": name,
                "issuer": issuer,
                "issue_date": date_str,
            })

        return certs

    def _parse_languages(self, sections: Dict[str, str]) -> List[Dict[str, str]]:
        default_languages = [
            {"language": "Arabic", "proficiency": "Native"},
            {"language": "English", "proficiency": "Fluent"},
        ]
        lang_text = ""
        for sec_name, content in sections.items():
            if "language" in sec_name:
                lang_text = content
                break

        if lang_text:
            # Replace LaTeX linebreaks (\newline, \\) with actual newlines before cleaning
            pre_split = re.sub(r"\\newline\b|\\\\", "\n", lang_text)
            found: List[Dict[str, str]] = []
            for raw_chunk in re.split(r"[,•|\n]+", pre_split):
                item = clean_latex(raw_chunk).strip()
                if not item:
                    continue
                prof = "Fluent"
                for p in ["Native", "Fluent", "Professional Working", "Professional", "Intermediate", "Conversational"]:
                    if p.lower() in item.lower():
                        prof = p
                        item = re.sub(rf"\({re.escape(p)}\)|{re.escape(p)}", "", item, flags=re.IGNORECASE).strip()
                        break
                item = item.strip(":-–— ").strip()
                if item:
                    found.append({"language": item, "proficiency": prof})
            if found:
                return found

        return default_languages

    def _extract_bullet_items(self, text: str) -> List[str]:
        bullets: List[str] = []
        macro_items = extract_macro_calls(text, "resumeItem", 1)
        if macro_items:
            for idx, (args, _, match_end) in enumerate(macro_items):
                cleaned = clean_latex(args[0])
                if not cleaned or len(cleaned) <= 10:
                    continue
                # Check if a nested \item \textbf{Stack: ...} follows before the next \resumeItem
                next_start = macro_items[idx + 1][1] if idx + 1 < len(macro_items) else len(text)
                between_slice = text[match_end:next_start]
                stack_match = re.search(r"\\item\s*(?:\\textbf\{)?\s*Stack:\s*([^}\n]+)", between_slice, re.IGNORECASE)
                if stack_match:
                    stack_str = clean_latex(stack_match.group(1)).strip()
                    if stack_str:
                        cleaned = f"{cleaned} [Stack: {stack_str}]"
                bullets.append(cleaned)
        else:
            for line in text.splitlines():
                if "\\item" in line:
                    cleaned = clean_latex(line.replace("\\item", ""))
                    if cleaned and len(cleaned) > 10:
                        bullets.append(cleaned)
        return bullets

    def _parse_custom_sections(self, body_tex: str) -> List[Dict[str, Any]]:
        """
        Scans the LaTeX document body for all non-standard sections (e.g. Publications,
        Awards & Honors, Volunteer Work, Patents, Conferences, Courses, Leadership, etc.)
        and parses them into structured CustomSection payloads.
        """
        standard_keywords = [
            "education", "academic", "university", "school",
            "experience", "employment", "work", "history", "career",
            "skill", "technical", "technologies", "competenc", "tools",
            "project",
            "certificat", "license", "credential",
            "language",
            "summary", "objective", "about", "profile", "bio",
        ]

        pattern = r"\\section\*?\{([^}]+)\}"
        matches = list(re.finditer(pattern, body_tex))
        custom_sections: List[Dict[str, Any]] = []

        for i, match in enumerate(matches):
            raw_title = match.group(1)
            display_title = clean_latex(raw_title)
            title_lower = display_title.lower()

            if any(k in title_lower for k in standard_keywords):
                continue

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body_tex)
            raw_section_text = body_tex[start:end]

            custom_sec = self._parse_single_custom_section(display_title, raw_section_text)
            if custom_sec:
                custom_sections.append(custom_sec)

        return custom_sections

    def _parse_single_custom_section(self, display_title: str, raw_tex: str) -> Optional[Dict[str, Any]]:
        if not display_title or not raw_tex.strip():
            return None

        sec_id = f"sec_{re.sub(r'[^a-z0-9]+', '_', display_title.lower()).strip('_')}"
        items: List[Dict[str, Any]] = []

        # 1. Look for \resumeSubheading
        subheadings = extract_macro_calls(raw_tex, "resumeSubheading", 4)
        if subheadings:
            for idx, (args, _, match_end) in enumerate(subheadings):
                c1 = clean_latex(args[0])
                c2 = clean_latex(args[1])
                c3 = clean_latex(args[2])
                c4 = clean_latex(args[3])
                start = match_end
                end = subheadings[idx + 1][1] if idx + 1 < len(subheadings) else len(raw_tex)
                bullets = self._extract_bullet_items(raw_tex[start:end])
                items.append({
                    "id": f"item_{idx + 1}",
                    "title": c1 or "Entry",
                    "date": c2,
                    "subtitle": c3,
                    "location_or_link": c4,
                    "description": "",
                    "bullet_points": bullets,
                })

        # 2. Look for \resumeProjectHeading
        elif "\\resumeProjectHeading" in raw_tex:
            proj_headings = extract_macro_calls(raw_tex, "resumeProjectHeading", 2)
            for idx, (args, _, match_end) in enumerate(proj_headings):
                header = clean_latex(args[0])
                date_val = clean_latex(args[1])
                parts = header.split("|")
                name = parts[0].strip()
                subtitle = parts[1].strip() if len(parts) > 1 else ""
                start = match_end
                end = proj_headings[idx + 1][1] if idx + 1 < len(proj_headings) else len(raw_tex)
                bullets = self._extract_bullet_items(raw_tex[start:end])
                items.append({
                    "id": f"item_{idx + 1}",
                    "title": name or "Entry",
                    "subtitle": subtitle,
                    "date": date_val,
                    "location_or_link": "",
                    "description": "",
                    "bullet_points": bullets,
                })

        # 3. Look for \item blocks
        elif "\\item" in raw_tex:
            item_matches = re.split(r"\\item\b", raw_tex)
            for idx, raw_item in enumerate(item_matches[1:]):
                cleaned = clean_latex(raw_item)
                if not cleaned:
                    continue

                date_match = re.search(r"\b(19\d{2}|20\d{2})(?:\s*[-–—]\s*(?:Present|19\d{2}|20\d{2}))?\b", cleaned)
                date_str = date_match.group(0) if date_match else ""

                link_match = re.search(r"\\href\{([^}]+)\}", raw_item)
                link_str = link_match.group(1) if link_match else ""

                parts = [p.strip() for p in cleaned.split("|") if p.strip()]
                if len(parts) >= 2:
                    t = parts[0]
                    sub = parts[1]
                elif " - " in cleaned or " -- " in cleaned:
                    split_dash = re.split(r"\s+[-–—]+\s+", cleaned, 1)
                    t = split_dash[0].strip()
                    sub = split_dash[1].strip() if len(split_dash) > 1 else ""
                else:
                    t = cleaned
                    sub = ""

                items.append({
                    "id": f"item_{idx + 1}",
                    "title": t,
                    "subtitle": sub,
                    "date": date_str,
                    "location_or_link": link_str,
                    "description": "",
                    "bullet_points": [],
                })

        # 4. Fallback to freeform lines or paragraph
        else:
            cleaned_text = clean_latex(raw_tex)
            if cleaned_text:
                lines = [l.strip() for l in cleaned_text.splitlines() if l.strip()]
                if len(lines) > 1:
                    for idx, line in enumerate(lines):
                        items.append({
                            "id": f"item_{idx + 1}",
                            "title": line,
                            "subtitle": "",
                            "date": "",
                            "location_or_link": "",
                            "description": "",
                            "bullet_points": [],
                        })
                else:
                    items.append({
                        "id": "item_1",
                        "title": display_title,
                        "subtitle": "",
                        "date": "",
                        "location_or_link": "",
                        "description": cleaned_text,
                        "bullet_points": [],
                    })

        return {
            "id": sec_id,
            "section_title": display_title,
            "section_type": "items",
            "content_text": clean_latex(raw_tex),
            "items": items,
        }

    def _disentangle_role_company(self, arg1: str, arg3: str) -> tuple[str, str]:
        if "," in arg1:
            parts = arg1.split(",", 1)
            return parts[0].strip(), parts[1].strip()
        if arg3 and not arg1:
            return arg3, "Company"
        return arg1, arg3 or "Company"

    def _parse_date_range(self, date_str: str) -> tuple[str, str]:
        if not date_str:
            return "2022-01", "Present"
        parts = re.split(r"\s*(?:--|—|–|\bto\b|-)\s*", date_str, maxsplit=1, flags=re.IGNORECASE)
        start = parts[0].strip() if parts else "2022-01"
        end = parts[1].strip() if len(parts) > 1 else "Present"
        return start, end


latex_cv_parser = LatexCvParser()
