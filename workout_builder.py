def build_running_workout_text(warmup_min: int, reps: int, work_duration: str, work_target: str, rest_duration: str, cooldown_min: int, notes: str = "") -> str:
    """Génère la syntaxe officielle Intervals.icu compatible Garmin."""
    lines = []
    if notes:
        lines.append(notes.strip())
        lines.append("")

    lines.append("Warmup")
    lines.append(f"- {warmup_min}m 60-70% HR")
    lines.append("")

    if reps > 1:
        lines.append(f"{reps}x")
    lines.append(f"- {work_duration} {work_target}")
    if rest_duration and rest_duration.strip() != "0":
        lines.append(f"- {rest_duration} 55-65% HR")
    lines.append("")

    lines.append("Cooldown")
    lines.append(f"- {cooldown_min}m 55-65% HR")

    return "\n".join(lines)

def build_home_gym_workout_text(focus: str, duration_min: int, exercises: list, notes: str = "") -> str:
    """Génère une séance structurée pour le Home Gym (Cage GOIMU, poulies, poids libres)."""
    lines = [f"Objectif : {focus} ({duration_min} min)", "Équipement : Cage GOIMU C1-V4, Poulie haute/basse, Banc, Poids libres", ""]
    if notes:
        lines.append(notes.strip())
        lines.append("")
    lines.append("Circuit / Exercices :")
    for ex in exercises:
        lines.append(f"- {ex}")
    return "\n".join(lines)
