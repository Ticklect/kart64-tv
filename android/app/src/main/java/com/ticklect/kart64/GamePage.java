package com.ticklect.kart64;

/** Upgrade the known packaged page without touching private game/save files. */
final class GamePage {
    static String augment(String input) {
        String html = input.replace("\r\n", "\n");
        if (!html.contains("src=\"tv-shell.js\"")) {
            String anchor = "<script>\nconst ROM_SHA1";
            if (!html.contains(anchor)) throw new IllegalArgumentException("Update the game files using the desktop installer.");
            String assets = "<link rel=\"stylesheet\" href=\"tv-shell.css\">\n"
                + "<script src=\"tv-controls.js\"></script>\n<script src=\"tv-engine.js\"></script>\n<script src=\"tv-shell.js\"></script>\n";
            html = html.replace(anchor, assets + anchor);
        }
        if (!html.contains("loadingMessage(t, bad)")) {
            html = html.replace("  statusEl.textContent = t;", "  globalThis.Kart64TV?.loadingMessage(t, bad);\n  statusEl.textContent = t;");
        }
        html = html.replace("const touchDevice = navigator.maxTouchPoints > 0 || qp.has('touch');", "const touchDevice = false;");
        html = html.replace("const touchable = navigator.maxTouchPoints > 0 || qp.has('touch');", "const touchable = false;");
        return html;
    }
}
