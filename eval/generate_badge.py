import json
from pathlib import Path

def main():
    report_path = Path(__file__).resolve().parent / "report" / "eval_report.json"
    if not report_path.exists():
        print("No eval_report.json found.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    accuracy = data.get("metrics", {}).get("accuracy_percent", 0.0)
    
    color = "red"
    if accuracy >= 85.0:
        color = "brightgreen"
    elif accuracy >= 75.0:
        color = "green"
    elif accuracy >= 60.0:
        color = "yellow"

    badge_data = {
        "schemaVersion": 1,
        "label": "eval accuracy",
        "message": f"{accuracy}%",
        "color": color
    }

    badge_path = Path(__file__).resolve().parent / "report" / "badge.json"
    with open(badge_path, "w", encoding="utf-8") as f:
        json.dump(badge_data, f, indent=2)

    print(f"Generated badge: {badge_data['message']} ({badge_data['color']}) -> {badge_path}")

if __name__ == "__main__":
    main()
