## Installation

Clone the repository and set up the Python environment:

```bash
git clone https://github.com/adboussif/explorae.git
cd explorae
python3 -m venv .venv
source .venv/bin/activate
./install_explorae.sh

  ## Usage de base

  ```bash
  python ./src/explorae.py ./test.xlsx ./interactions
  ```

  Ce que fait le script :
  - parcourt `./interactions` (un dossier par interaction),
  - lit `ranking_debug.json` pour retrouver le modèle top et ipTM/pTM,
  - calcule ipSAE / pDockQ2 via `ipsae.py` (fichiers de résumé),
  - lance PRODIGY ( CLI + parsing),
  - lance PyRosetta InterfaceAnalyze,
  - met à jour l'Excel/CSV en ajoutant les colonnes (ou les crée si manquantes).

  ---

  ## Options (principales)

  | Option | Usage |
  |--------|-------|
  | `--pae` | seuil PAE (Å) pour ipSAE (par défaut `10`) |
  | `--dist` | cutoff distance (Å) pour ipSAE (par défaut `10`) |
  | `--id-col` | nom de la colonne ID dans l'Excel (par défaut `jobs`) |
  | `--sheet` | onglet Excel (index ou nom, par défaut `0`) |

  Exemple :
  ```bash
  python ./src/explorae.py test.xlsx ./interactions --pae 12 --dist 8 --id-col jobs --sheet 0
  ```

  ---

  ---

  ## Exemple de sortie console

  ```
=== A0A3Q7EZF3_SOLLC_and_RdRPL ===
ipSAE   : 0.014296
pDockQ2 : 0.079000
PRODIGY Kd (M): 2.178e-07
PRODIGY ΔG internal : -9.082449616519174
iptm+ptm: 6.480e-01
iptm : 6.440e-01
dG_SASA_ratio (kJ/A): 2.069e+00
dG Rosetta (dG_cross): 3342.93115234375
  ```

  ---


## References

This project builds upon and integrates several established tools and recent methodological advances in protein structure prediction and protein–protein interaction assessment.

1. **AlphaPulldown**  
   Kosinski Lab. *AlphaPulldown: A Python package for high-throughput protein–protein interaction screening using AlphaFold.*  
   GitHub: https://github.com/KosinskiLab/AlphaPulldown

2. **PRODIGY**  
   Xue et al. *PRODIGY: A web server for predicting the binding affinity of protein–protein complexes.*  
   GitHub: https://github.com/haddocking/prodigy

3. **ipSAE and pDockQ2**  
   Johansson-Åkhe et al. *Assessing the reliability of AlphaFold multimer predictions using ipSAE and pDockQ2.*  
   Nucleic Acids Research, 2024.  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC11844409/

4. **Predicting Experimental Success in de novo Binder Design**  
   Bryant et al. *Predicting experimental success in de novo protein binder design.*  
   bioRxiv, 2025.  
   https://www.biorxiv.org/content/10.1101/2025.08.14.670059v1.full.pdf
