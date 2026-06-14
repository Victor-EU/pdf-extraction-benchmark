# Per-category audit — which vendor is good at what (v2 corrected GT)

Fair total (weighted) per page category, with sample size, mean recall, and fidelity. gpt-5 rows (◆) are upper bounds (built the GT). **Image/Photo n is tiny — see the warning.**

**Pages per category (n):** Text 149, Table 128, Chart/Diagram 152, Mixed 113, Cover/Divider 55, Image/Photo 2

## Text  (n=149)

| Vendor | Fair total | Mean recall | Unsupported |
|---|---:|---:|---:|
| gpt-5 (image) ◆ | 97% | 97% | 2% |
| Gemini 3.5 Flash | 96% | 96% | 3% |
| Gemini 3.1 Flash-Lite | 95% | 95% | 2% |
| gpt-5 (file) ◆ | 95% | 95% | 2% |
| Landing AI | 95% | 95% | 12% |
| PyMuPDF | 91% | 91% | 1% |
| Tesseract | 86% | 86% | 7% |
| LlamaParse | 79% | 80% | 2% |

**Clean winner:** Gemini 3.5 Flash (96%), +1pp over Gemini 3.1 Flash-Lite.

_By document_ (exposes doc/category confound):

| Vendor | Alpha-deck (n=25) | AnnualRpt (n=116) | SOTER-deck (n=8) |
|---|---:|---:|---:|
| gpt-5 (image) ◆ | 94% | 98% | 99% |
| Gemini 3.5 Flash | 91% | 97% | 99% |
| Gemini 3.1 Flash-Lite | 91% | 96% | 97% |
| gpt-5 (file) ◆ | 95% | 95% | 98% |
| Landing AI | 92% | 96% | 85% |
| PyMuPDF | 89% | 91% | 91% |
| Tesseract | 80% | 86% | 93% |
| LlamaParse | 85% | 78% | 86% |

## Table  (n=128)

| Vendor | Fair total | Mean recall | Unsupported |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 91% | 91% | 9% |
| Gemini 3.1 Flash-Lite | 91% | 91% | 8% |
| gpt-5 (image) ◆ | 89% | 89% | 8% |
| gpt-5 (file) ◆ | 89% | 89% | 8% |
| Landing AI | 87% | 86% | 18% |
| PyMuPDF | 86% | 85% | 6% |
| LlamaParse | 71% | 72% | 13% |
| Tesseract | 62% | 63% | 22% |

**Clean winner:** Gemini 3.5 Flash (91%), +1pp over Gemini 3.1 Flash-Lite.

_By document_ (exposes doc/category confound):

| Vendor | Alpha-deck (n=58) | AnnualRpt (n=54) | SOTER-deck (n=16) |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 84% | 98% | 94% |
| Gemini 3.1 Flash-Lite | 83% | 98% | 94% |
| gpt-5 (image) ◆ | 79% | 98% | 93% |
| gpt-5 (file) ◆ | 80% | 97% | 91% |
| Landing AI | 77% | 97% | 84% |
| PyMuPDF | 76% | 97% | 81% |
| LlamaParse | 68% | 74% | 74% |
| Tesseract | 59% | 64% | 64% |

## Chart/Diagram  (n=152)

| Vendor | Fair total | Mean recall | Unsupported |
|---|---:|---:|---:|
| gpt-5 (file) ◆ | 87% | 88% | 13% |
| Gemini 3.5 Flash | 87% | 88% | 13% |
| gpt-5 (image) ◆ | 86% | 87% | 15% |
| Gemini 3.1 Flash-Lite | 83% | 84% | 10% |
| PyMuPDF | 80% | 80% | 3% |
| Landing AI | 76% | 77% | 22% |
| LlamaParse | 63% | 64% | 12% |
| Tesseract | 50% | 51% | 15% |

**Clean winner:** Gemini 3.5 Flash (87%), +4pp over Gemini 3.1 Flash-Lite.

_By document_ (exposes doc/category confound):

| Vendor | Alpha-deck (n=34) | AnnualRpt (n=38) | SOTER-deck (n=80) |
|---|---:|---:|---:|
| gpt-5 (file) ◆ | 87% | 91% | 85% |
| Gemini 3.5 Flash | 85% | 92% | 86% |
| gpt-5 (image) ◆ | 84% | 92% | 84% |
| Gemini 3.1 Flash-Lite | 82% | 91% | 81% |
| PyMuPDF | 74% | 83% | 81% |
| Landing AI | 67% | 86% | 76% |
| LlamaParse | 63% | 67% | 61% |
| Tesseract | 44% | 57% | 49% |

## Mixed  (n=113)

| Vendor | Fair total | Mean recall | Unsupported |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 95% | 95% | 7% |
| gpt-5 (image) ◆ | 94% | 95% | 6% |
| gpt-5 (file) ◆ | 94% | 94% | 5% |
| Gemini 3.1 Flash-Lite | 92% | 93% | 8% |
| PyMuPDF | 89% | 89% | 1% |
| Landing AI | 85% | 85% | 15% |
| LlamaParse | 76% | 78% | 6% |
| Tesseract | 69% | 70% | 12% |

**Clean winner:** Gemini 3.5 Flash (95%), +2pp over Gemini 3.1 Flash-Lite.

_By document_ (exposes doc/category confound):

| Vendor | Alpha-deck (n=24) | AnnualRpt (n=73) | SOTER-deck (n=16) |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 92% | 96% | 92% |
| gpt-5 (image) ◆ | 94% | 96% | 83% |
| gpt-5 (file) ◆ | 94% | 96% | 85% |
| Gemini 3.1 Flash-Lite | 92% | 94% | 84% |
| PyMuPDF | 92% | 87% | 91% |
| Landing AI | 72% | 93% | 71% |
| LlamaParse | 79% | 75% | 77% |
| Tesseract | 76% | 68% | 63% |

## Cover/Divider  (n=55)

| Vendor | Fair total | Mean recall | Unsupported |
|---|---:|---:|---:|
| gpt-5 (image) ◆ | 91% | 91% | 3% |
| gpt-5 (file) ◆ | 90% | 91% | 2% |
| Gemini 3.5 Flash | 84% | 85% | 3% |
| Gemini 3.1 Flash-Lite | 83% | 85% | 1% |
| Landing AI | 82% | 83% | 20% |
| LlamaParse | 51% | 52% | 8% |
| PyMuPDF | 50% | 51% | 0% |
| Tesseract | 33% | 32% | 10% |

**Clean winner:** Gemini 3.5 Flash (84%), +0pp over Gemini 3.1 Flash-Lite.

_By document_ (exposes doc/category confound):

| Vendor | Alpha-deck (n=14) | AnnualRpt (n=29) | SOTER-deck (n=12) |
|---|---:|---:|---:|
| gpt-5 (image) ◆ | 92% | 92% | 88% |
| gpt-5 (file) ◆ | 88% | 94% | 81% |
| Gemini 3.5 Flash | 88% | 89% | 68% |
| Gemini 3.1 Flash-Lite | 85% | 87% | 74% |
| Landing AI | 82% | 88% | 69% |
| LlamaParse | 34% | 64% | 39% |
| PyMuPDF | 23% | 73% | 25% |
| Tesseract | 24% | 46% | 11% |

## Image/Photo  (n=2)  ⚠️ **n too small to draw vendor conclusions**

| Vendor | Fair total | Mean recall | Unsupported |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 95% | 95% | 2% |
| gpt-5 (file) ◆ | 94% | 94% | 2% |
| gpt-5 (image) ◆ | 90% | 92% | 2% |
| Gemini 3.1 Flash-Lite | 89% | 89% | 4% |
| LlamaParse | 74% | 66% | 38% |
| Tesseract | 70% | 66% | 2% |
| PyMuPDF | 61% | 61% | 8% |
| Landing AI | 60% | 62% | 4% |

**Clean winner:** Gemini 3.5 Flash (95%), +6pp over Gemini 3.1 Flash-Lite.

_By document_ (exposes doc/category confound):

| Vendor | Alpha-deck (n=1) | SOTER-deck (n=1) |
|---|---:|---:|
| Gemini 3.5 Flash | 95% | 95% |
| gpt-5 (file) ◆ | 93% | 95% |
| gpt-5 (image) ◆ | 88% | 95% |
| Gemini 3.1 Flash-Lite | 90% | 88% |
| LlamaParse | 91% | 40% |
| Tesseract | 78% | 55% |
| PyMuPDF | 62% | 60% |
| Landing AI | 55% | 70% |

## Highest-divergence pages per category (hand-audit targets)

Pages where clean vendors disagree most (max−min recall). These are where the category score is being decided — read GT vs vendor here to confirm the gap is real, not a judge artifact.

### Text
- Alpha-deck p5 (w5, spread 100): land:100 pymu:85 llam:85 tess:85 gemi:0 gemi:0
- AnnualRpt p103 (w6, spread 99): gemi:99 llam:99 pymu:97 land:95 tess:75 gemi:0
- AnnualRpt p237 (w6, spread 88): gemi:96 gemi:95 land:88 tess:70 pymu:8 llam:8
- AnnualRpt p236 (w6, spread 87): tess:92 gemi:88 land:86 gemi:85 pymu:5 llam:5
- AnnualRpt p235 (w6, spread 87): gemi:90 gemi:90 land:85 tess:75 llam:5 pymu:3
- AnnualRpt p228 (w5, spread 87): gemi:92 land:90 gemi:88 tess:70 llam:10 pymu:5

### Table
- SOTER-deck p48 (w9, spread 75): gemi:90 gemi:90 land:90 llam:25 pymu:20 tess:15
- AnnualRpt p270 (w9, spread 75): land:100 gemi:99 gemi:99 pymu:98 llam:60 tess:25
- AnnualRpt p166 (w9, spread 75): gemi:100 gemi:100 land:100 pymu:100 tess:85 llam:25
- AnnualRpt p277 (w9, spread 70): gemi:100 gemi:100 land:100 pymu:100 llam:60 tess:30
- Alpha-deck p129 (w8, spread 70): gemi:80 gemi:75 land:70 pymu:30 llam:25 tess:10
- Alpha-deck p110 (w5, spread 70): gemi:95 gemi:80 tess:70 llam:65 pymu:55 land:25

### Chart/Diagram
- SOTER-deck p92 (w7, spread 95): gemi:100 gemi:100 land:100 pymu:100 llam:60 tess:5
- SOTER-deck p77 (w5, spread 90): gemi:100 land:95 gemi:90 llam:25 pymu:15 tess:10
- SOTER-deck p69 (w9, spread 87): gemi:97 gemi:90 land:70 pymu:40 llam:20 tess:10
- SOTER-deck p85 (w8, spread 85): pymu:95 tess:80 llam:70 gemi:60 land:50 gemi:10
- SOTER-deck p112 (w9, spread 83): gemi:98 gemi:91 pymu:85 land:55 tess:20 llam:15
- SOTER-deck p107 (w9, spread 83): land:98 gemi:95 pymu:95 llam:90 gemi:75 tess:15

### Mixed
- SOTER-deck p30 (w9, spread 87): pymu:97 gemi:96 llam:78 land:50 gemi:40 tess:10
- AnnualRpt p204 (w7, spread 83): gemi:95 pymu:60 tess:50 gemi:35 land:30 llam:12
- AnnualRpt p215 (w7, spread 80): pymu:100 gemi:98 gemi:98 llam:98 land:95 tess:20
- AnnualRpt p47 (w7, spread 80): gemi:98 gemi:97 land:92 llam:25 pymu:20 tess:18
- Alpha-deck p119 (w5, spread 80): gemi:100 gemi:100 pymu:100 llam:90 tess:55 land:20
- AnnualRpt p202 (w8, spread 77): land:97 gemi:96 gemi:96 pymu:96 llam:92 tess:20

### Cover/Divider
- SOTER-deck p119 (w1, spread 100): gemi:100 gemi:100 land:100 pymu:100 llam:100 tess:0
- AnnualRpt p238 (w3, spread 98): gemi:98 gemi:95 land:90 pymu:85 llam:80 tess:0
- AnnualRpt p212 (w2, spread 95): gemi:95 land:85 gemi:80 llam:55 pymu:50 tess:0
- AnnualRpt p300 (w2, spread 90): land:90 gemi:70 gemi:70 pymu:55 llam:50 tess:0
- Alpha-deck p54 (w3, spread 85): gemi:90 gemi:70 land:55 llam:20 tess:15 pymu:5
- SOTER-deck p99 (w2, spread 85): gemi:100 gemi:85 land:85 llam:70 pymu:30 tess:15

### Image/Photo
- SOTER-deck p86 (w3, spread 55): gemi:95 gemi:88 land:70 pymu:60 tess:55 llam:40
- Alpha-deck p94 (w6, spread 40): gemi:95 llam:91 gemi:90 tess:78 pymu:62 land:55

