# Reproduction of the base analysis and the Medicare extension

The validation run used an empty Python 3.12.14 virtual environment on Linux, an archive of the public base tag `v1.3.1` (commit `253c09f`), and a separate archive of the exploratory Medicare module (local commit `2940038`). Both archives came from the author's source tree. The run used the same Linux host as the original analysis. `requirements-linux-py312.txt` records the installed versions of all 18 direct and transitive Python packages.

Thirty base outputs were deleted before reconstruction. The 12 numerical commands completed successfully and all 30 outputs matched the archived bytes. The 12 commands include a compatibility copy of the model checker. The primary NHANES model used 197 respondents and returned an odds ratio of 2.8162646562. All 32 original NHS workbooks rebuilt a panel with 6,754 rows and 76 columns.

The official sources supplied fresh copies of the three CDC survey files, 32 NHS workbooks, three CMS files and ten Census annual archives. All 48 SHA-256 digests matched the archived inputs. Both packages were rerun using these downloads. The six Medicare and Census analytical outputs matched the archived bytes. Source verification covered the archived CMS methods PDF as well as its numerical inputs. The Australian program series still relies on the distributed transcription of official statistics. The Monitor annex text was taken from the base release.

The figure run located Arial through Matplotlib and XeLaTeX. All 11 regenerated base vector figures produced the same RGB pixels as their distributed versions when rendered at 72 dpi. The separate event-study PNG also matched its archived bytes. The supplied mechanism illustration was counted separately as fixed artwork in the historical baseline.

## Current supplementary archive

The recorded tagged run and its hashes are historical. The current supplement applies the open-ended age-class recursion in the manuscript to `verification_results.json`. For the extracted supplement, repeat the comparison with `--current-supplement`. This reads the expected hash for that one output from the supplied manifest and uses the recorded hashes for the other 29 base and six extension outputs. The default continues to verify the historical tag.

## Reproduce the comparisons

Use a checkout of the base tag and an extracted copy of the Medicare extension. In a fresh virtual environment, install the requirements from this directory. The examples below use POSIX shell variables with absolute paths and Python 3.12.

```sh
BASE=/path/to/access-is-not-use-codes
CMS=/path/to/medicare_spillover_pilot
AUDIT=/path/to/clean_reproduction
python -m pip install -r "$AUDIT/requirements-linux-py312.txt"
python "$AUDIT/download_verified.py" --base "$BASE"
python "$BASE/reproduce_all.py" --analysis-only
python "$CMS/download_inputs.py"
python "$CMS/analyze.py"
python "$CMS/coverage_check.py"
python "$AUDIT/verify_outputs.py" --base "$BASE" --cms "$CMS"
```

The base archive already contains survey files and workbooks. `download_verified.py` retrieves any missing source file, checks existing inputs and stops on a digest mismatch. To test the upstream URLs, use a new empty destination for `--base` and keep the resulting directory structure when transferring these raw inputs into a checkout. `--offline` only checks local input files. The CMS downloader retains the original archived source verification. Default analysis commands are independent of Arial. To regenerate figures, obtain Arial, XeLaTeX and the TeX packages listed in the base README. Use `python "$BASE/reproduce_all.py" --figures` and `python "$CMS/make_event_pdf.py"`.

`validation.json` records the reference outputs and figure pixel digests. The final verification compares exact file hashes. Differences on other platforms may also arise from text line endings or low-order floating-point representation and warrant comparison of the numerical values.

The current v1.4.0 release typesets Figure 1 from tikz/model_mechanism_illustrated.tex. The historical render comparisons above refer to the assets in the stated audit.
