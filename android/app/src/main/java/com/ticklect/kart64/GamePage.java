package com.ticklect.kart64;

/** Upgrade the known packaged page without touching private game/save files. */
final class GamePage {
    private static final String FIRST_PAINT = "<style id=\"k64-boot-cover\">#overlay{visibility:hidden!important}body:not(.k64-tv-app)::after{content:\"Opening Kart64 TV...\";position:fixed;inset:0;display:grid;place-items:center;background:#16211a;color:#e4edac;font:700 22px Arial;z-index:40000}</style>";
    static String augment(String input) {
        String html = input.replace("\r\n", "\n");
        if (!html.contains("src=\"tv-shell.js\"")) {
            String anchor = "<script>\nconst ROM_SHA1";
            if (!html.contains(anchor)) throw new IllegalArgumentException("Update the game files using the desktop installer.");
            String assets = "<link rel=\"stylesheet\" href=\"tv-shell.css\">\n"
                + "<script src=\"tv-controls.js\"></script>\n<script src=\"tv-engine.js\"></script>\n<script src=\"tv-shell.js\"></script>\n";
            html = html.replace(anchor, assets + anchor);
        }
        if (!html.contains("src=\"tv-theme.js\"")) {
            html = html.replace("<script src=\"tv-shell.js\"", "<script src=\"tv-theme.js\"></script>\n<script src=\"tv-shell.js\"");
        }
        if (!html.contains("loadingMessage(t, bad)")) {
            html = html.replace("  statusEl.textContent = t;", "  globalThis.Kart64TV?.loadingMessage(t, bad);\n  statusEl.textContent = t;");
        }
        html = html.replace("const touchDevice = navigator.maxTouchPoints > 0 || qp.has('touch');", "const touchDevice = false;");
        html = html.replace("const touchable = navigator.maxTouchPoints > 0 || qp.has('touch');", "const touchable = false;");
        if (!html.contains("k64-boot-cover")) html = html.replaceFirst("(?i)</head>", FIRST_PAINT + "</head>");
        return html;
    }
}
