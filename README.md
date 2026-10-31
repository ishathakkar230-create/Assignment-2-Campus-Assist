# Assignment 2 — Campus Assist

Extension of Assignment 1: the SAME core, agent and policy data are preserved, with VERSION set to 2. Adds pending programme changes, separate reviewer approval/rejection, transactional execution and audit visibility.

## What this project demonstrates

Campus Assist uses Groq's official Python client and a bounded model → tool → model loop. All records and policies are fictional. No friend's source code, credentials, virtual environment, database or evaluation claims are copied into this deliverable. This continues the Campus Assist implementation developed in this conversation.

## Windows: start here

Use Python 3.11 (your installed 3.11.9 is suitable). Extract to a short local path, for example `D:\CampusA1` or `D:\CampusA2`; keep the two versions in different folders.

1. Double-click **SETUP_WINDOWS.cmd**. This creates `.venv`, installs requirements and creates `.env` from `.env.example`.
2. Set and repeat a password of at least 12 characters for every requested account. Password typing is hidden. Existing accounts are kept. Setup repeats an invalid password prompt until it succeeds.
3. In VS Code, open the local `.env` file. Replace `paste_your_groq_key_here` with your own Groq key; keep the model line. Save. Do not record the screen while doing this. Do not send or publish this file.
4. Double-click **START_WINDOWS.cmd**. Open the Local URL shown in its terminal and sign in.
5. Keep that terminal running. If several old app servers remain open, use the Local URL from this launch; stop an old instance with Ctrl+C in its own terminal.

Your Groq account must allow the configured model. A Free account has request/token limits; no paid-plan upgrade is required for using its available free allowance. A 429 can require waiting; it is not solved by repeatedly creating new keys. Availability depends on your account. OpenAI API credits are not used by this app.

Manual equivalent from the project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe setup_demo.py
# Edit and save .env locally, then:
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Only use `Copy-Item` the first time; do not overwrite an existing configured `.env`. Terminal environment variables take precedence over `.env`; clear an old GROQ_API_KEY variable or start a new terminal if an older value unexpectedly remains active.

macOS/Linux: create/activate a Python 3.11 virtual environment, install requirements, copy `.env.example` to `.env`, configure it, run `python setup_demo.py`, then `python -m streamlit run app.py`.

## Architecture

| Component | File | Decision |
| --- | --- | --- |
| UI and identity | app.py | Sign-in creates a server-held session; chat never supplies authority |
| Agent loop and API | agent.py | At most six model calls; only registered tools execute |
| Records and permissions | core.py | Authenticated student ownership checked before SQL access |
| Handbook retrieval | data/policy.json + core.py | Four sections of one fictional handbook; at most two lexical matches |
| Memory | core.py | SQLite; student-scoped programme/language enums only |
| Tracing | agent.py | Per-run tools, evidence, usage, latency and status in local JSON |
| Assignment selection | settings.py | Fixed version per deliverable; no confusing in-app version switch |
| Local account setup | setup_demo.py | Salted PBKDF2 hashes; private passwords entered locally |
| Live evaluation | evaluate.py | Actual model responses and reported usage; human rubric grading |
| Cross-version comparison | compare_results.py | Shared-task comparison from two completed scoring CSVs |

Each turn starts with system instructions and the current question. There is no automatic full-document or full-history injection. Tools supply only relevant record fields, up to two policy sections or one requested memory key. A new chat clears display context; signing out clears the complete Streamlit session; SQLite preferences survive sign-in. Remembering a programme preference does not change the official record.

Tools include `get_status`, `search_policy`, `remember`, `recall`, and `create_ticket`. Assignment 2 adds `request_programme_change`; the model cannot approve it. Fee amounts, scholarship state and programme facts come from local synthetic records. Policy answers must identify retrieved section IDs. Missing evidence leads to abstention. Retrieval is deliberately lexical; paraphrase quality and weak matches require evaluation.

## Data and privacy

Synthetic student S001 starts with fee INR 25,000, scholarship Pending and programme PGDM AI. S002 starts with fee INR 10,000, scholarship Approved and programme PGDM AI. These are not real student records or real institutional policies.

Only fixed language/programme preference values can enter persistent memory. A conservative gate discards messages with credential keywords, API-key patterns or 4–8 digit codes before the model is called. False positives are possible; it is not comprehensive secret detection. Tickets persist only a category, not free text. No raw chat question or answer is written into operational traces; synthetic allowlisted tool evidence is recorded. The UI retains ordinary chat only in its session memory. Model requests go to Groq, so no zero-retention guarantee is claimed.

The database and traces remain local under ignored `runtime/`. Local filesystem administrators can read or change this database. Authentication is educational, with no SSO, rate limiting or institutional identity verification. Audits are useful evidence, not tamper-proof records. Use fictional data only.

## Tests and measured evaluation

Run **TEST_WINDOWS.cmd**, or:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`reports/OFFLINE_TEST_RESULTS.txt` contains the actual offline run supplied with this version. These are deterministic code tests with a mocked model where needed; their fake usage counts are never live API measurements. UI layout and a live API run of this packaged build have not been verified in this environment.

For live results, sign in locally and run **EVALUATE_WINDOWS.cmd**. Press Enter for each case, leaving enough time for free-tier limits. Every question gets fresh model context. The saved CSV contains blank human pass/tool-choice columns; review the JSON against each rubric and fill all fields with 0 or 1. Count errors as failures. A blank token field means no usage was reported, not fabricated zero. Blocked sensitive-input cases make zero API calls and have no reported API usage.

Start with a fresh demo database for a reproducible baseline. The evaluator changes language memory, creates a ticket and, in Assignment 2, stages a pending request. Do not delete your working database unintentionally; use a fresh extracted folder for a clean run.

After evaluating both versions and filling both CSVs:

```powershell
.\.venv\Scripts\python.exe compare_results.py "D:\CampusA1\reports\scoring_A1_TIMESTAMP.csv" "D:\CampusA2\reports\scoring_A2_TIMESTAMP.csv"
```

This writes `reports/comparison.json` with shared-task success rate, mean shared-task latency, reported token totals and cases lacking usage. Token totals over all cases should be interpreted with the differing test counts. Manually attach privacy-denial, approval, rejection and audit evidence from Assignment 2 as well. Human waiting time is not part of chat latency. Complete `reports/FINAL_EVALUATION_TEMPLATE.csv` using real results; it is intentionally marked NOT_RUN before your live run.

## Repository and video submission

Publish complete source, this README, policy data, dependencies, tests, your reviewed evaluation evidence and the relevant video link through your own public GitHub repository. Do not publish `.env`, `.venv`, runtime databases, local passwords, session tokens or unreviewed traces. `.gitignore` helps only when Git honors it; it cannot protect a manually uploaded ZIP containing credentials.

Read VIDEO_SCRIPT.md, understand the implementation and record your own walkthrough with voice and the working app. Demonstrate tool/evidence traces and your actual measurements. The script does not replace the required recording. Open repository/video links in a signed-out browser before submitting them through the instructor's form.

Official implementation references:
- https://console.groq.com/docs/quickstart
- https://console.groq.com/docs/tool-use
- https://console.groq.com/docs/model/openai/gpt-oss-20b
- https://console.groq.com/docs/rate-limits
