from pathlib import Path

def _find_naccess_config() -> Path:
    # Dossier courant: src/modules/data/
    here = Path(__file__).parent
    # Essaie les deux orthographes, au cas où
    for name in ("naccess.config", "nacess.config"):
        p = (here / name).resolve()
        if p.exists():
            return p
    # Si rien trouvé, lève une erreur claire (évite le "{}" pour freesasa)
    raise FileNotFoundError(
        f"Fichier naccess.config introuvable dans {here} "
        f"(essayé: naccess.config, nacess.config)."
    )

# Chemin absolu attendu par freesasa.Classifier(str(NACCESS_CONFIG))
NACCESS_CONFIG = _find_naccess_config()
