from __future__ import annotations


def build_heatmap_svg(result):
    trained = {
        item["name"].lower().replace(" ", ""): item["count"]
        for item in result["muscles"]
    }

    def color(muscle: str) -> str:
        count = trained.get(muscle.lower().replace(" ", ""), 0)
        if count <= 0:
            return "#2a2f38"
        if count == 1:
            return "#fde047"
        if count == 2:
            return "#fb923c"
        return "#ef4444"

    return f"""
        <svg viewBox="0 0 500 650" width="100%" style="max-width:520px">
            <style>
                .muscle {{
                    stroke: #0f1115;
                    stroke-width: 2.5;
                    transition: all 0.25s ease;
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.35));
                }}
                .muscle:hover {{
                    opacity: 0.85;
                    cursor: pointer;
                    transform-origin: center;
                }}
                text {{
                    fill: #e5e7eb;
                    font-size: 16px;
                    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                    font-weight: 500;
                    letter-spacing: 0.3px;
                    text-anchor: middle;
                }}
            </style>

            <circle cx="250" cy="70" r="40" fill="#4b5563" stroke="#0f1115" stroke-width="2.5"/>

            <rect class="muscle" x="125" y="125" width="80" height="55" rx="25" fill="{color('shoulders')}"/>
            <rect class="muscle" x="295" y="125" width="80" height="55" rx="25" fill="{color('shoulders')}"/>

            <rect class="muscle" x="175" y="140" width="70" height="90" rx="20" fill="{color('chest')}"/>
            <rect class="muscle" x="255" y="140" width="70" height="90" rx="20" fill="{color('chest')}"/>

            <path class="muscle" d="M175 245 Q250 290 325 245 L315 350 Q250 390 185 350 Z" fill="{color('back')}"/>

            <rect class="muscle" x="205" y="245" width="90" height="125" rx="25" fill="{color('abs')}"/>
            <line x1="250" y1="250" x2="250" y2="360" stroke="#111" stroke-width="3"/>
            <line x1="210" y1="285" x2="290" y2="285" stroke="#111" stroke-width="3"/>
            <line x1="210" y1="325" x2="290" y2="325" stroke="#111" stroke-width="3"/>

            <rect class="muscle" x="95" y="190" width="55" height="120" rx="25" fill="{color('biceps')}"/>
            <rect class="muscle" x="350" y="190" width="55" height="120" rx="25" fill="{color('biceps')}"/>

            <rect class="muscle" x="60" y="210" width="45" height="120" rx="22" fill="{color('triceps')}"/>
            <rect class="muscle" x="395" y="210" width="45" height="120" rx="22" fill="{color('triceps')}"/>

            <rect class="muscle" x="180" y="390" width="60" height="180" rx="28" fill="{color('legs')}"/>
            <rect class="muscle" x="260" y="390" width="60" height="180" rx="28" fill="{color('legs')}"/>

            <text x="250" y="625">Muscle groups trained this week</text>
        </svg>
        """
