**\[TODO, My Approach, Key areas, Dr. Anas Abutaha, Dai Haiwen pipeline Analysis, P1, P2, *Info to look into latest:*]**

###### ***\[KEEP Reading this Regularly]* ->** https://dblalock.github.io/how-to-undergrad-research/

###### **\[Graduate Scholarship Program] ->** https://innolight.qrdi.org.qa/innovation/p/opportunities/p/24





#### **TODO:**

1\. Literature review (3 papers) \[Done]

2\. Refine AI/ML skills - Project based approach -> (Learn by doing) \[Done]

3\. Cross check "My approach" with Dai Haiwen pipeline approach -> then u get refined "My approach" \[Done]

4\. Extract all relevant information, just do it (Graph2table)\[HERE]

5\. Look at the images Dr. Anas drew and figure out the right pipeline for extraction using existing tools (Go to the references and extract from there(Its there in the caption)) (Sci-hub.se) \[HERE]

6\.



==================

https://chatgpt.com/c/693fca6a-2098-8332-887b-b173b2c732fa

==================



Dai Haiwen \[Interview] ->

1. scopas -> search engine
2. web of sciences
3. google scholar -> compile pdfs

4\. method to extract pdfs \[Identify the right research groups]

 	a. Identify styles of (many seeback and electrical conductivity) -> list all methods

 	b.





#### **My Approach:**

Resources -> \[Medium articles, Videos, Academic papers, msg DH \&\& AA]

1. Establish the entire dataset -> Sample evenly for ground truth based on differing format/publication owners
2. Design algo -> Test against ground truth -> Define 5 metrics (Provides good analysis) -> Accuracy
3. Once Algo obtains high accuracy -> Run on entire dataset -> Save CSV









#### **Key areas:**

1. XYdigitizer -> Tedious method
2. Text-mining/Data-mining
3. automatic data extraction



#### **Dr. Anas Abutaha**

Mine Parameters -> *See back* and *electrical conductivity* for conducting polymers

thermoelectric polymers -> scopas

Text mining Approach



#### **Dai Haiwen pipeline Analysis:**

**Key Sections to Extract:**

1. Clear schema \& traceability

Example: For one paper, link Cu nanoparticle (25 nm) → spray coating (0.5 mg cm⁻²) → flow cell → i–V–FE curve → 12 h stability decay = 8%.



2\. Golden Dataset (manual, high quality)

Example: Manually extract all fields from a Feng Jiao paper and store them in a clean table or JSON with zero missing values.



3\. Multimodal parsing (text + figures)

Example: Read electrolyte composition from text, then digitize the FE vs voltage curve from a plotted figure to recover numeric data points.

\[Ingest paper (PDF) and split into: text blocks, tables, figures. Detect figure types (is this an i–V curve, FE curve, stability plot, or schematic?). Extract structured fields from text/tables (NER + rules + LLM). Digitize plots for curves (axis detection, scaling, line extraction, point sampling). Normalize units and vocabulary (RHE vs SHE, sccm vs mL/min, “MEA” synonyms). Validate with constraints (schema rules + cross-checks).Attach provenance (page/figure/table references).Export to DB-ready JSON/CSV.]



4\. Defaults \& normalization rules

Example: If temperature is not reported, automatically record 298 K and flag it as “assumed”.



5\. Silver Dataset (semi-automated)

Example: Run the pipeline on 50 papers, then manually spot-check 5 to compare extracted FE values against the originals.



6\. Iterative prompt and logic refinement

Example: Adjust prompts so that “flow cell with anion-exchange membrane” is always classified as MEA-type rather than free text.



7\. Final searchable database

Example: Query the database with “Cu catalyst + flow cell + FE > 60% for C₂ products” and retrieve matching papers instantly.================================================================================================================================

#### **Paper 1 (Machine Learning for molecules and material science):**



Machine Learning for Molecular and Materials Science







Foundations



1. Quantum mechanics and Schrödinger equation: provide the fundamental laws that determine electron behaviour and bonding in materials.

2\. Structure → property relationships: explain how atomic arrangement controls physical and chemical properties.

3\. Computational chemistry and DFT: use approximate quantum methods to predict material properties before experiments.

4\. High-throughput simulations and databases: rapidly compute and store properties of thousands of materials for large-scale screening.

⬇️



Core Machine Learning Framework



Data-driven modelling instead of explicit physics



Learning patterns from data rather than hard-coded rules



⬇️



Machine Learning Workflow



Data collection



Experiments



Simulations (DFT)



Databases (Materials Project, ICSD, ZINC, etc.)



Data representation (featurization)



Molecular descriptors (Coulomb matrix, graphs)



Crystal descriptors (RDFs, Voronoi, fragments)



Learning type



Supervised



Semi-supervised



Unsupervised



Model selection



Cross-validation



Ensembles



Bias–variance trade-off



Model optimization



Hyperparameter tuning



Overfitting vs underfitting control



⬇️



Machine Learning Methods



Bayesian models (Naive Bayes)



Nearest neighbour methods



Decision trees and random forests



Kernel methods (SVM, kernel ridge)



Neural networks and deep learning



⬇️



Application Domains



➡️ Chemical Synthesis



Retrosynthesis planning



Reaction prediction



Crystallization prediction



Active learning for experiments



Robotic and autonomous synthesis



➡️ Characterization



Image-based microstructure analysis



Spectroscopy and diffraction interpretation



Phase detection and surface reconstruction



➡️ Theory and Simulation



Learning DFT corrections



ML-derived density functionals



Neural network interatomic potentials



Fast surrogate models for quantum calculations



➡️ Materials Discovery



High-throughput screening



Inverse design



Crystal structure prediction



Alloy and functional material discovery



➡️ Molecular Design



QSAR modelling



Virtual screening



Generative models (GANs)



Reinforcement learning for de novo molecules



➡️ Literature and Knowledge Mining



Text mining of scientific papers



Automated database construction



Knowledge extraction and integration



⬇️



Frontiers and Future Directions



Learning from small datasets (meta-learning, one-shot learning)



Better chemical and crystal representations



Quantum machine learning



Discovering physical laws from data



Interpretability vs black-box models



⬇️



Vision



Fully AI-accelerated design–synthesis–characterization–discovery loop



Machine learning as a core scientific tool, not just an accelerator

================================================================================================================================

Paper 2: (High throughput and machine learning

approaches for thermoelectric materials)



=







================================================================================================================================







#### ***Info to look into latest:***

===========================

1. Cross check "My approach" with Dai Haiwen pipeline approach -> then u get refined "My approach"
2. 

===========================

Improved version of your approach



1\. Dataset definition and stratified sampling



Define the full dataset and its heterogeneity (publisher, year, layout type, scanned vs digital).



Create a stratified ground-truth subset that evenly represents these variations.



2\. Ground-truth schema design



Define variables, units, acceptable ranges, and tolerance rules.



Specify what counts as “correct” (exact match vs numeric tolerance).



3\. Algorithm design (iterative)



Build a baseline extraction algorithm.



Attach provenance to every extracted value (page, snippet, bounding box).



4\. Evaluation against ground truth



Evaluate using multiple metrics, not just accuracy:



Precision



Recall



F1-score



Numeric error (MAE or tolerance-based accuracy)



Missing rate



5\. Error analysis and refinement



Categorize failures (layout error, OCR error, unit mismatch, ambiguity).



Improve rules or models based on dominant failure modes.



6\. Acceptance threshold



Define a minimum acceptable performance per variable (e.g. F1 ≥ 0.9, missing rate ≤ 5%).



7\. Scale-up execution



Run algorithm on full dataset.



Log confidence scores and flag low-confidence extractions.



8\. Post-run validation



Perform random audits and consistency checks on large-scale outputs.



Export final structured dataset (CSV).



Why this is better than the original

1\. Accuracy alone is not enough



Accuracy hides failure modes.

Precision and recall tell you what you missed vs what you hallucinated.



2\. Stratified sampling prevents false confidence



If your ground truth is biased toward “easy PDFs”, your algorithm will fail at scale.



3\. Provenance is critical



Without source location, you cannot debug or trust your outputs.



4\. Error analysis is where real progress happens



Most performance gains come from fixing the top 2–3 failure types, not adding complexity.



5\. Acceptance thresholds make it scientific



You are no longer “hoping” it works. You are certifying it works.



One-line summary (research-grade framing)



Develop an extraction algorithm, validate it against a stratified ground-truth dataset using multi-metric evaluation, iterate through error analysis, and deploy at scale with confidence-aware outputs.



If you want, next I can:



Turn this into a methods section for a paper



Design the exact 5 metrics mathematically



Help you define a ground-truth annotation protocol



Just tell me what you want to formalize next.



**\[Ask Questions it will take you deep]**

1. **Vector pdf -> Is a PDF where figures are stored as mathematical objects (lines, curves, text, coordinates), not pixels.**
2. **Should we prepare a solid dataset**
3. **Are you looking for a fully developed pipeline \[Takes in 100 pdfs]**





***Options I have:***

1. Extract vector paths directly from the PDF if the figure is vector

2\. Render the figure at high DPI and do image-based digitization

3\. Use axis calibration + curve tracing to recover numerical data

4\. Apply color or style separation to handle multiple lines

5\. Run OCR on axis labels and legends to recover units and meaning

6\. Use semi-automatic tools (e.g. manual calibration, auto-trace) **\[NO]**

7\. Build a fully automated OpenCV pipeline for batch extraction

8\. Validate extracted curves against ground-truth or physics constraints

9\. Store outputs as structured datasets (CSV, JSON)

10\. Add quality checks and confidence scores per extracted curve





**We here:**

1. Use fast heuristics to get the correct image
2. Grab the text according to the polymers of interest
3. System prompt



Heuristics approach:

1. There seems to be a,b,c,d
2. It needs to have a legend







