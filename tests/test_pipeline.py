import json
import os
import unittest

from helpers import EX, FACTS, Workdir, dp, have_chrome, xml


class TestBuildAndParse(unittest.TestCase):
    def test_build_is_a_real_docx_with_expected_sections(self):
        with Workdir() as w:
            self.assertIn("anchor heading: SUMMARY", dp("inspect", w.cv).stdout)
            from docproof.render import parse
            header, sections, lang, _ = parse(w.cv)
            self.assertEqual(header["name"], "JORDAN RIVERA")
            self.assertEqual(lang, "en")
            self.assertEqual([s["key"] for s in sections],
                             ["SUMMARY", "PROFESSIONAL EXPERIENCE", "SKILLS", "EDUCATION", "LANGUAGES", "PROJECTS"])
            exp = [b for b in sections[1]["blocks"] if b["type"] == "entry"]
            self.assertEqual(len(exp), 2)
            self.assertEqual(len(exp[0]["bullets"]), 5)
            self.assertEqual(exp[0]["date"], "Mar 2022 – Aug 2025")
            kinds = [c["kind"] for c in header["contacts"]]
            self.assertEqual(kinds, ["location", "email", "phone", "web"])

    def test_german_headings(self):
        with Workdir() as w:
            spec = json.loads((EX / "resume.json").read_text())
            spec["language"] = "de"
            (w.p("de.json")).write_text(json.dumps(spec))
            dp("build", w.p("de.json"), w.p("de.docx"))
            self.assertIn("KURZPROFIL", xml(w.p("de.docx")))
            self.assertIn("language: German", dp("inspect", w.p("de.docx")).stdout)


class TestEditing(unittest.TestCase):
    def test_edit_ops_and_header_protection(self):
        with Workdir() as w:
            ops = [{"op": "set_text", "zone": "title", "match": "Product Analyst",
                    "text": "Experimentation Analyst  |  A/B Testing & Retention"},
                   {"op": "replace", "match": "Designed and analysed 40+", "old": "Designed", "new": "Planned"},
                   {"op": "delete", "match": "Defined the event tracking plan"}]
            w.p("ops.json").write_text(json.dumps(ops))
            dp("edit", w.cv, w.p("ops.json"), w.p("out.docx"))
            text = dp("text", w.p("out.docx")).stdout
            self.assertIn("Experimentation Analyst", text)
            self.assertIn("Planned and analysed 40+", text)
            self.assertNotIn("event tracking plan for", text)
            self.assertIn("PASSED", dp("header-diff", w.cv, w.p("out.docx")).stdout)

    def test_edit_refuses_ambiguous_match(self):
        with Workdir() as w:
            w.p("ops.json").write_text(json.dumps([{"op": "delete", "match": "Built"}]))
            r = dp("edit", w.cv, w.p("ops.json"), w.p("out.docx"), check=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(w.p("out.docx").exists())

    def test_keywords_bold_only_the_phrase(self):
        with Workdir() as w:
            w.p("kw.json").write_text(json.dumps({"Designed and analysed 40+": ["A/B tests"]}))
            dp("keywords", w.cv, w.p("kw.docx"), w.p("kw.json"))
            from docproof.render import parse
            _, sections, _, _ = parse(w.p("kw.docx"))
            first = sections[1]["blocks"][0]["bullets"][0]
            self.assertEqual([t for t, _, b in first if b], ["A/B tests"])

    def test_reorder_sections_keeps_content(self):
        with Workdir() as w:
            order = "SUMMARY,PROFESSIONAL EXPERIENCE,PROJECTS,SKILLS,EDUCATION,LANGUAGES"
            out = dp("reorder", w.cv, w.p("r.docx"), "sections", order).stdout
            self.assertIn("PROJECTS → SKILLS", out)
            self.assertEqual(sorted(dp("text", w.cv).stdout.splitlines()),
                             sorted(dp("text", w.p("r.docx")).stdout.splitlines()))

    def test_add_link_next_to_existing_and_new(self):
        with Workdir() as w:
            dp("add-link", w.cv, w.p("l1.docx"), "Churn Radar", "GitHub", "https://example.com/repo")
            dp("add-link", w.p("l1.docx"), w.p("l2.docx"), "BSc Economics", "Transcript", "https://example.com/t")
            from docproof.render import parse
            _, sections, _, _ = parse(w.p("l2.docx"))
            links = [h for s in sections for b in s["blocks"] if b["type"] == "entry"
                     for _, h, _ in b["title_runs"] if h]
            self.assertIn("https://example.com/repo", links)
            self.assertIn("https://example.com/t", links)
            edu = [b for b in sections[3]["blocks"] if b["type"] == "entry"][1]
            self.assertEqual(edu["date"], "Sep 2018 – Jun 2021")   # the date column survived

    def test_add_entry_and_summary(self):
        with Workdir() as w:
            spec = {"after": "Technologies: Python, scikit-learn", "like_title": "BSc Economics",
                    "like_bullet": "Built an open-source churn", "like_meta": "Technologies: Python",
                    "title": "Pricing Test Simulator — Personal Project", "date": "2025",
                    "bullets": ["Simulated price tests on synthetic subscription data."],
                    "meta": "Technologies: Python, NumPy."}
            w.p("e.json").write_text(json.dumps(spec))
            dp("add-entry", w.cv, w.p("e.docx"), w.p("e.json"))
            self.assertIn("Pricing Test Simulator", dp("text", w.p("e.docx")).stdout)
            spec2 = json.loads((EX / "resume.json").read_text())
            del spec2["summary"]
            w.p("ns.json").write_text(json.dumps(spec2))
            dp("build", w.p("ns.json"), w.p("ns.docx"))
            dp("add-summary", w.p("ns.docx"), w.p("s.docx"), "SUMMARY", "Short profile.", "PROFESSIONAL EXPERIENCE")
            self.assertEqual(dp("text", w.p("s.docx")).stdout.splitlines()[3:5], ["SUMMARY", "Short profile."])


class TestVerifyAndMatch(unittest.TestCase):
    def test_example_verifies_clean(self):
        with Workdir() as w:
            self.assertIn("VERIFY PASSED", dp("verify", w.cv, "--facts", FACTS).stdout)

    def test_invented_number_and_gap_fail(self):
        with Workdir() as w:
            ops = [{"op": "replace", "match": "Designed and analysed 40+", "old": "40+", "new": "60+"},
                   {"op": "replace", "match": "Automated the weekly KPI report with", "old": "scheduled dbt runs", "new": "Airflow"}]
            w.p("ops.json").write_text(json.dumps(ops))
            dp("edit", w.cv, w.p("ops.json"), w.p("bad.docx"))
            r = dp("verify", w.p("bad.docx"), "--facts", FACTS, "--json", check=False)
            self.assertEqual(r.returncode, 1)
            rep = json.loads(r.stdout)
            self.assertEqual([x["number"] for x in rep["numbers"]], ["60+"])
            self.assertEqual([x["term"] for x in rep["gaps"]], ["Airflow"])

    def test_match_report(self):
        rep = json.loads(dp("match", EX / "jobs" / "experimentation-analyst.txt", "--facts", FACTS, "--json").stdout)
        self.assertGreaterEqual(rep["coverage"], 60)
        by_req = {r["requirement"]: r for r in rep["requirements"]}
        self.assertEqual(by_req["Experience with GA4 and Braze"]["verdict"], "gap")
        self.assertEqual(by_req["Strong SQL; experience with dbt"]["verdict"], "evidence")


class TestRobustness(unittest.TestCase):
    def test_in_place_edit_is_safe(self):
        with Workdir() as w:
            before = dp("text", w.cv).stdout
            w.p("ops.json").write_text(json.dumps([{"op": "replace", "match": "Designed and analysed 40+",
                                                    "old": "Designed", "new": "Planned"}]))
            dp("edit", w.cv, w.p("ops.json"), w.cv)                       # same file in and out
            self.assertIn("Planned and analysed", dp("text", w.cv).stdout)
            w.p("kw.json").write_text(json.dumps({"Planned and analysed": ["A/B tests"]}))
            dp("keywords", w.cv, w.cv, w.p("kw.json"))
            dp("reorder", w.cv, w.cv, "sections", "summary,professional experience,projects,skills,education,languages")
            self.assertEqual(len(dp("text", w.cv).stdout.splitlines()), len(before.splitlines()))

    def test_failed_check_writes_nothing(self):
        with Workdir() as w:
            w.p("ops.json").write_text(json.dumps([{"op": "delete", "match": "Nonexistent line"}]))
            self.assertNotEqual(dp("edit", w.cv, w.p("ops.json"), w.p("o.docx"), check=False).returncode, 0)
            self.assertFalse(w.p("o.docx").exists())

    def test_short_gap_terms_do_not_hit_compounds(self):
        from docproof.verify import gap_in
        self.assertTrue(gap_in("R", "Python and R for analysis"))
        self.assertFalse(gap_in("R", "worked in R&D"))
        self.assertFalse(gap_in("R", "an R-squared of 0.8"))

    def test_every_command_without_args_prints_help_not_a_traceback(self):
        for cmd in ("build", "render", "check", "verify", "match", "dump", "edit", "text", "inspect",
                    "header-diff", "keywords", "reorder", "add-entry", "add-link", "add-summary",
                    "set-metadata", "lint", "prompt", "apply"):
            r = dp(cmd, check=False)
            self.assertNotEqual(r.returncode, 0, cmd)
            self.assertNotIn("Traceback", r.stderr + r.stdout, cmd)

    def test_friendly_error_for_missing_file_and_swapped_args(self):
        r = dp("verify", "nope.docx", "--facts", FACTS, check=False)
        self.assertIn("file not found", r.stderr)
        with Workdir() as w:
            r = dp("edit", w.cv, w.p("out.docx"), w.p("ops.json"), check=False)   # swapped
            self.assertIn("usage", r.stderr)


REPLY = """```json
{
  "go_no_go": "apply — strong experimentation evidence; GA4 and Braze are gaps",
  "ops": [
    {"op": "set_text", "zone": "title", "match": "Product Analyst",
     "text": "Experimentation Analyst  |  A/B Testing & Retention Analytics"},
    {"op": "replace", "match": "Designed and analysed 40+", "old": "Designed", "new": "Planned"},
    {"op": "delete", "match": "Cleaned and reconciled 2 years"}
  ],
  "keywords": {"Planned and analysed 40+": ["A/B tests"]},
  "notes": ["Prepare an answer on GA4 and Braze."]
}
```"""


class TestAnyAssistant(unittest.TestCase):
    def test_init_creates_templates_without_overwriting(self):
        with Workdir() as w:
            out = dp("init", w.p("me")).stdout
            self.assertIn("created", out)
            self.assertTrue(w.p("me/profile/fact-base.md").exists())
            dp("build", w.p("me/profile/resume.json"), w.p("me/base.docx"))
            self.assertIn("exists, kept", dp("init", w.p("me")).stdout)

    def test_prompts_contain_all_context(self):
        with Workdir() as w:
            ad = EX / "jobs" / "experimentation-analyst.txt"
            t = dp("prompt", "tailor", "--facts", FACTS, "--ad", ad, "--doc", w.cv).stdout
            for needle in ("## Known gaps", "Brightleaf Health", "coverage:", "JORDAN RIVERA", '"ops"'):
                self.assertIn(needle, t)
            self.assertIn("MACHINE CHECK", dp("prompt", "audit", "--facts", FACTS, "--doc", w.cv).stdout)
            r = dp("prompt", "review", "--doc", w.cv, "--persona", "hiring manager").stdout
            self.assertIn("You are a hiring manager", r)
            self.assertNotIn("Known gaps", r)                   # the reviewer never sees the fact base

    def test_apply_llm_reply_then_verify(self):
        with Workdir() as w:
            w.p("reply.json").write_text(REPLY)
            out = dp("apply", w.cv, w.p("reply.json"), w.p("t.docx"), "--facts", FACTS).stdout
            self.assertIn("VERIFY PASSED", out)
            self.assertIn("note: Prepare an answer", out)
            text = dp("text", w.p("t.docx")).stdout
            self.assertIn("Experimentation Analyst", text)
            self.assertIn("Planned and analysed 40+", text)
            bad = REPLY.replace('"new": "Planned"', '"new": "Planned 50+ tests and"')
            w.p("bad.json").write_text(bad)
            r = dp("apply", w.cv, w.p("bad.json"), w.p("b.docx"), "--facts", FACTS, check=False)
            self.assertEqual(r.returncode, 1)
            self.assertIn("50+", r.stdout)


class TestLintAndCli(unittest.TestCase):
    def test_lint(self):
        with Workdir() as w:
            w.p("notes.md").write_text("We report weekly in Excel.\nOld: monthly in Excel\n")
            w.p("rules.json").write_text(json.dumps([{"pattern": r"weekly in Excel", "fix": "reports now run in dbt"}]))
            r = dp("lint", w.p("notes.md"), "--rules", w.p("rules.json"), check=False)
            self.assertEqual(r.returncode, 1)
            self.assertIn("1 stale hit", r.stdout)

    def test_help_and_unknown_command(self):
        self.assertIn("docproof", dp("--help").stdout)
        self.assertNotEqual(dp("nope", check=False).returncode, 0)


@unittest.skipUnless(have_chrome() or os.environ.get("DOCPROOF_REQUIRE_CHROME"), "needs Chrome/Chromium and poppler")
class TestRender(unittest.TestCase):
    def test_render_and_full_check(self):
        with Workdir() as w:
            out = dp("check", w.cv, "--png", w.d).stdout
            self.assertIn("ALL HARD CHECKS PASSED", out)
            self.assertIn("pages   : 1", out)
            self.assertNotIn("WARN", out)
            self.assertTrue(list(w.d.glob("cv-*.png")))


if __name__ == "__main__":
    unittest.main()
