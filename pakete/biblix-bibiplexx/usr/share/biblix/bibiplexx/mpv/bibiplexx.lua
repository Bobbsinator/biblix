-- Bibiplexx fuer mpv: eigene Steuerleiste, Kinomodus (Vorhang + Gong), "Weiterschauen",
-- Intro ueberspringen, Countdown zur naechsten Folge, Schlaf-Timer und Nachtmodus.
-- Wird von bibiplexx mit --script geladen. Optionen (--script-opts):
--   bibiplexx-kino=yes|no        Vorhang-Intro beim ersten Film
--   bibiplexx-gong=/pfad.wav     Gong fuer das Intro (leer = ohne Gong)
--   bibiplexx-countdown=15       Sekunden vor Schluss: "Naechste Folge in ..." (0 = aus)
--   bibiplexx-intro_knopf=yes    Knopf "Intro ueberspringen" bei passenden Kapiteln
local mp = require "mp"
local utils = require "mp.utils"
local options = require "mp.options"

local opts = { kino = true, gong = "", stand = "", countdown = 15, intro_knopf = true }
options.read_options(opts, "bibiplexx")

local HOME = os.getenv("HOME") or "/tmp"
local STAND = opts.stand ~= "" and opts.stand or (HOME .. "/.local/state/bibiplexx/fortschritt.json")

local PINK, ORANGE, LILA, SCHWARZ, TEXT = "#ff4d9d", "#ff8a00", "#7b2cbf", "#07070c", "#f2e9ff"
local NACHT_FILTER = "@nacht:lavfi=[dynaudnorm=f=150:g=15:p=0.7]"

-- ---------------------------------------------------------------- ASS-Zeichenhilfen

local function farbe(hex)
    return "&H" .. hex:sub(6, 7) .. hex:sub(4, 5) .. hex:sub(2, 3) .. "&"
end

local function rechteck(x, y, w, h, f, alpha)
    return string.format("{\\an7\\pos(0,0)\\bord0\\shad0\\1c%s\\1a&H%s&\\p1}m %d %d l %d %d %d %d %d %d{\\p0}",
        farbe(f), alpha or "00", x, y, x + w, y, x + w, y + h, x, y + h)
end

local function rund(x, y, w, h, r, f, alpha)
    r = math.min(r, h / 2, w / 2)
    local k = r * 0.45
    return string.format("{\\an7\\pos(0,0)\\bord0\\shad0\\1c%s\\1a&H%s&\\p1}" ..
        "m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d{\\p0}",
        farbe(f), alpha or "00",
        x + r, y, x + w - r, y, x + w - k, y, x + w, y + k, x + w, y + r,
        x + w, y + h - r, x + w, y + h - k, x + w - k, y + h, x + w - r, y + h,
        x + r, y + h, x + k, y + h, x, y + h - k, x, y + h - r,
        x, y + r, x, y + k, x + k, y, x + r, y)
end

local function form(punkte, f, alpha)
    local s = string.format("{\\an7\\pos(0,0)\\bord0\\shad0\\1c%s\\1a&H%s&\\p1}m %d %d", farbe(f), alpha or "00", punkte[1], punkte[2])
    for i = 3, #punkte, 2 do
        s = s .. string.format(" l %d %d", punkte[i], punkte[i + 1])
    end
    return s .. "{\\p0}"
end

local function sauber(t)
    return (t or ""):gsub("[{}\\]", "")
end

local function text(x, y, t, groesse, f, an, fett, alpha)
    return string.format("{\\an%d\\pos(%d,%d)\\fnDejaVu Sans\\fs%d\\b%d\\bord0\\shad0\\1c%s\\1a&H%s&}%s",
        an or 4, x, y, groesse, fett and 1 or 0, farbe(f), alpha or "00", sauber(t))
end

local function zeit(s)
    if not s or s < 0 then return "--:--" end
    s = math.floor(s)
    local h, m, sek = math.floor(s / 3600), math.floor(s / 60) % 60, s % 60
    if h > 0 then return string.format("%d:%02d:%02d", h, m, sek) end
    return string.format("%d:%02d", m, sek)
end

-- ---------------------------------------------------------------- Weiterschauen

local aktuell = { pfad = nil, pos = 0, dauer = 0 }

local function stand_lesen()
    local f = io.open(STAND, "r")
    if not f then return {} end
    local inhalt = f:read("*a")
    f:close()
    local d = utils.parse_json(inhalt)
    return type(d) == "table" and d or {}
end

local function stand_schreiben(fertig)
    if not aktuell.pfad or aktuell.dauer <= 0 then return end
    local d = stand_lesen()
    local ende = fertig or (aktuell.pos / aktuell.dauer) > 0.93
    d[aktuell.pfad] = { pos = ende and 0 or math.floor(aktuell.pos), dauer = math.floor(aktuell.dauer),
                        zeit = os.time(), fertig = ende }
    local tmp = STAND .. ".tmp"
    local f = io.open(tmp, "w")
    if not f then return end
    f:write(utils.format_json(d))
    f:close()
    os.rename(tmp, STAND)
end

mp.observe_property("time-pos", "number", function(_, v) if v then aktuell.pos = v end end)
mp.observe_property("duration", "number", function(_, v) if v then aktuell.dauer = v end end)
mp.observe_property("pause", "bool", function(_, p) if p then stand_schreiben(false) end end)
mp.add_periodic_timer(10, function() stand_schreiben(false) end)

mp.register_event("file-loaded", function()
    aktuell = { pfad = mp.get_property("path"), pos = 0, dauer = mp.get_property_number("duration", 0) }
end)
mp.register_event("end-file", function(e)
    stand_schreiben(e.reason == "eof")
end)

-- ---------------------------------------------------------------- Overlay

local ov = mp.create_osd_overlay("ass-events")
local sichtbar_bis = 0
local knoepfe = {}
local intro_laeuft = false
local meldung, meldung_bis = nil, 0
local melden                    -- weiter unten
local schlaf, schlaf_ende = "aus", nil   -- aus | folge | 30 | 60 | 90
local countdown_abgebrochen = nil
local abspann_ab = nil          -- Position, an der ein Abspann-Kapitel begann

local function schlaf_text()
    if schlaf == "aus" then return "aus" end
    if schlaf == "folge" then return "nach der Folge" end
    local rest = schlaf_ende and math.max(0, math.ceil((schlaf_ende - mp.get_time()) / 60)) or tonumber(schlaf)
    return rest .. " Min."
end

local function nacht_an()
    for _, f in ipairs(mp.get_property_native("af") or {}) do
        if f.label == "nacht" then return true end
    end
    return false
end

local function kapitel_titel()
    local i = mp.get_property_number("chapter", -1)
    local liste = mp.get_property_native("chapter-list") or {}
    if i >= 0 and liste[i + 1] then return (liste[i + 1].title or ""):lower() end
    return nil
end

local function ist_intro(t)
    return t and (t:find("intro") or t:find("opening") or t:find("vorspann") or t:find("recap")
        or t:find("rückblick") or t:find("previously")) ~= nil
end

local function ist_abspann(t)
    return t and (t:find("credits") or t:find("abspann") or t:find("ending") or t:find("outro")) ~= nil
end

local function groesse()
    local w, h = mp.get_osd_size()
    if not w or w <= 0 then return 1920, 1080, 1 end
    return w, h, math.max(0.6, h / 1080)
end

local function knopf(liste, x, y, w, h, aktion, inhalt, hover)
    table.insert(knoepfe, { x = x, y = y, w = w, h = h, aktion = aktion })
    if hover then table.insert(liste, rund(x, y, w, h, h / 2, PINK, "B0")) end
    table.insert(liste, inhalt)
end

local function maus_ueber(x, y, w, h)
    local mx, my = mp.get_mouse_pos()
    return mx >= x and mx <= x + w and my >= y and my <= y + h
end

local function leiste_zeichnen()
    local w, h, s = groesse()
    knoepfe = {}
    local l = {}
    local pause = mp.get_property_bool("pause", false)
    local pos = mp.get_property_number("time-pos", 0)
    local dauer = mp.get_property_number("duration", 0)
    -- Kopf mit Titel
    table.insert(l, rechteck(0, 0, w, math.floor(80 * s), SCHWARZ, "50"))
    table.insert(l, text(math.floor(40 * s), math.floor(40 * s), mp.get_property("media-title", ""), math.floor(30 * s), TEXT, 4, true))
    table.insert(l, text(w - math.floor(40 * s), math.floor(40 * s), "BIBIPLEXX", math.floor(24 * s), PINK, 6, true))
    -- Fuss
    local fh = math.floor(150 * s)
    table.insert(l, rechteck(0, h - fh, w, fh, SCHWARZ, "40"))
    table.insert(l, rechteck(0, h - fh, w, math.max(2, math.floor(3 * s)), LILA, "00"))
    -- Fortschritt
    local x0, x1 = math.floor(150 * s), w - math.floor(150 * s)
    local ty = h - math.floor(105 * s)
    local th = math.max(4, math.floor(8 * s))
    table.insert(l, rund(x0, ty, x1 - x0, th, th / 2, "#2f2050", "00"))
    local anteil = (dauer > 0) and math.min(1, pos / dauer) or 0
    if anteil > 0 then
        table.insert(l, rund(x0, ty, math.max(th, math.floor((x1 - x0) * anteil)), th, th / 2, PINK, "00"))
    end
    local kx = x0 + math.floor((x1 - x0) * anteil)
    table.insert(l, rund(kx - math.floor(9 * s), ty + th / 2 - math.floor(9 * s), math.floor(18 * s), math.floor(18 * s), 9 * s, ORANGE, "00"))
    table.insert(knoepfe, { x = x0, y = ty - math.floor(14 * s), w = x1 - x0, h = th + math.floor(28 * s), aktion = "spulen" })
    if dauer > 0 and maus_ueber(x0, ty - math.floor(14 * s), x1 - x0, th + math.floor(28 * s)) then
        local mx = mp.get_mouse_pos()
        local ziel = math.max(0, math.min(1, (mx - x0) / (x1 - x0))) * dauer
        table.insert(l, rund(mx - math.floor(48 * s), ty - math.floor(52 * s), math.floor(96 * s), math.floor(34 * s), 10 * s, SCHWARZ, "20"))
        table.insert(l, text(mx, ty - math.floor(35 * s), zeit(ziel), math.floor(22 * s), ORANGE, 5, true))
    end
    table.insert(l, text(math.floor(40 * s), ty + th / 2, zeit(pos), math.floor(24 * s), TEXT, 4, false))
    table.insert(l, text(w - math.floor(40 * s), ty + th / 2, "-" .. zeit(dauer - pos), math.floor(24 * s), TEXT, 6, false))
    -- Knoepfe
    local by = h - math.floor(62 * s)
    local bh = math.floor(52 * s)
    local cy = by + bh / 2
    local x = math.floor(40 * s)
    local function zeichen_knopf(aktion, breite, zeichner)
        local hov = maus_ueber(x, by, breite, bh)
        knopf(l, x, by, breite, bh, aktion, zeichner(x, by, breite, bh), hov)
        x = x + breite + math.floor(10 * s)
    end
    local q = math.floor(14 * s)
    zeichen_knopf("zurueck", math.floor(70 * s), function(bx)
        local m = bx + math.floor(35 * s)
        return form({ m + q, cy - q, m - q / 3, cy, m + q, cy + q }, TEXT) .. "\n" ..
               form({ m, cy - q, m - q * 4 / 3, cy, m, cy + q }, TEXT)
    end)
    zeichen_knopf("pause", bh, function(bx)
        local m = bx + bh / 2
        if pause then
            return form({ m - q * 0.7, cy - q * 1.1, m + q * 1.1, cy, m - q * 0.7, cy + q * 1.1 }, ORANGE)
        end
        return rechteck(m - q * 0.8, cy - q, q * 0.55, q * 2, ORANGE) .. "\n" .. rechteck(m + q * 0.25, cy - q, q * 0.55, q * 2, ORANGE)
    end)
    zeichen_knopf("vor", math.floor(70 * s), function(bx)
        local m = bx + math.floor(35 * s)
        return form({ m - q, cy - q, m + q / 3, cy, m - q, cy + q }, TEXT) .. "\n" ..
               form({ m, cy - q, m + q * 4 / 3, cy, m, cy + q }, TEXT)
    end)
    if mp.get_property_number("playlist-count", 1) > 1 then
        zeichen_knopf("naechste", math.floor(170 * s), function(bx)
            return text(bx + math.floor(85 * s), cy, "Nächste Folge", math.floor(22 * s), TEXT, 5, true)
        end)
    end
    -- rechts: Untertitel, Ton, Lautstaerke, Vollbild, Schliessen
    local rechts = {
        { "schlaf", 190, "Schlaf: " .. schlaf_text() }, { "nacht", 120, nacht_an() and "Nacht: an" or "Nacht: aus" },
        { "untertitel", 70, "UT" }, { "ton", 80, "Ton" },
        { "lauter", 150, "Lautstärke " .. math.floor(mp.get_property_number("volume", 100)) },
        { "vollbild", 110, mp.get_property_bool("fullscreen") and "Fenster" or "Vollbild" }, { "schliessen", 52, "✕" },
    }
    x = w - math.floor(40 * s)
    for i = #rechts, 1, -1 do
        local r = rechts[i]
        local breite = math.floor(r[2] * s)
        x = x - breite
        local hov = maus_ueber(x, by, breite, bh)
        knopf(l, x, by, breite, bh, r[1], text(x + breite / 2, cy, r[3], math.floor((r[1] == "schliessen" and 34 or 22) * s), r[1] == "schliessen" and PINK or TEXT, 5, true), hov)
        x = x - math.floor(10 * s)
    end
    return l
end

-- Sekunden bis zur naechsten Folge (nil = kein Countdown)
local function countdown_rest()
    if opts.countdown <= 0 then return nil end
    if mp.get_property_number("playlist-pos", 0) >= mp.get_property_number("playlist-count", 1) - 1 then return nil end
    if countdown_abgebrochen == mp.get_property("path") then return nil end
    local dauer = mp.get_property_number("duration", 0)
    local pos = mp.get_property_number("time-pos", 0)
    if dauer < 120 then return nil end
    local rest = dauer - pos
    if abspann_ab then rest = math.min(rest, opts.countdown - (pos - abspann_ab)) end
    if rest <= opts.countdown then return math.max(0, rest) end
    return nil
end

local function pille(l, x, y, bw, bh, aktion, beschriftung, s, gefuellt)
    local hov = maus_ueber(x, y, bw, bh)
    table.insert(knoepfe, { x = x, y = y, w = bw, h = bh, aktion = aktion })
    table.insert(l, rund(x, y, bw, bh, bh / 2, gefuellt and ORANGE or SCHWARZ, gefuellt and "00" or "30"))
    if hov then table.insert(l, rund(x, y, bw, bh, bh / 2, PINK, "A0")) end
    table.insert(l, text(x + bw / 2, y + bh / 2, beschriftung, math.floor(24 * s), gefuellt and "#1b0d00" or TEXT, 5, true))
end

local function zusatz_zeichnen(l, w, h, s, leiste)
    local unten = h - (leiste and math.floor(175 * s) or math.floor(60 * s))
    -- Intro ueberspringen
    if opts.intro_knopf and ist_intro(kapitel_titel())
        and mp.get_property_number("chapter", -1) < mp.get_property_number("chapters", 0) - 1 then
        local bw, bh = math.floor(290 * s), math.floor(62 * s)
        pille(l, w - bw - math.floor(50 * s), unten - bh, bw, bh, "intro_weg", "Intro überspringen", s, true)
        return
    end
    -- Naechste Folge in ...
    local rest = countdown_rest()
    if rest then
        local pw, ph = math.floor(520 * s), math.floor(150 * s)
        local x, y = w - pw - math.floor(50 * s), unten - ph
        table.insert(l, rund(x, y, pw, ph, 18 * s, SCHWARZ, "18"))
        table.insert(l, rechteck(x + math.floor(18 * s), y + math.floor(16 * s), math.floor(6 * s), ph - math.floor(32 * s), PINK))
        table.insert(l, text(x + math.floor(40 * s), y + math.floor(40 * s), string.format("Nächste Folge in %d", math.ceil(rest)), math.floor(30 * s), TEXT, 4, true))
        local bh = math.floor(52 * s)
        pille(l, x + math.floor(40 * s), y + ph - bh - math.floor(20 * s), math.floor(220 * s), bh, "jetzt_weiter", "Jetzt ansehen", s, true)
        pille(l, x + math.floor(275 * s), y + ph - bh - math.floor(20 * s), math.floor(200 * s), bh, "countdown_weg", "Abbrechen", s, false)
        if rest <= 0 and abspann_ab then
            countdown_abgebrochen = mp.get_property("path")
            mp.commandv("playlist-next")
        end
    end
end

local function zeichnen()
    if intro_laeuft then return end
    local w, h, s = groesse()
    local l = {}
    local jetzt = mp.get_time()
    local leiste = jetzt < sichtbar_bis or mp.get_property_bool("pause", false)
    if leiste then
        l = leiste_zeichnen()
    else
        knoepfe = {}
    end
    zusatz_zeichnen(l, w, h, s, leiste)
    if meldung and jetzt < meldung_bis then
        local mb = math.max(660, #meldung * 21) * s
        table.insert(l, rund(w / 2 - mb / 2, h / 2 - math.floor(50 * s), mb, math.floor(100 * s), 20 * s, SCHWARZ, "30"))
        table.insert(l, text(w / 2, h / 2, meldung, math.floor(40 * s), ORANGE, 5, true))
    end
    ov.res_x, ov.res_y = w, h
    ov.data = table.concat(l, "\n")
    ov:update()
end

local function zeigen()
    sichtbar_bis = mp.get_time() + 2.5
    zeichnen()
end

melden = function(t, dauer)
    meldung, meldung_bis = t, mp.get_time() + (dauer or 1.6)
    zeichnen()
end

-- ---------------------------------------------------------------- Schlaf-Timer

local SCHLAF_REIHE = { "aus", "folge", "30", "60", "90" }

local function schlaf_weiter()
    local i = 1
    for k, v in ipairs(SCHLAF_REIHE) do if v == schlaf then i = k end end
    schlaf = SCHLAF_REIHE[i % #SCHLAF_REIHE + 1]
    schlaf_ende = tonumber(schlaf) and (mp.get_time() + tonumber(schlaf) * 60) or nil
    melden(schlaf == "aus" and "Schlaf-Timer aus" or ("Schlaf-Timer: " .. schlaf_text()), 1.6)
end

local function gute_nacht()
    schlaf, schlaf_ende = "aus", nil
    stand_schreiben(false)
    melden("Gute Nacht.", 4)
    local v0, n = mp.get_property_number("volume", 100), 0
    local t
    t = mp.add_periodic_timer(0.1, function()
        n = n + 1
        mp.set_property_number("volume", v0 * math.max(0, 1 - n / 30))
        if n >= 30 then
            t:kill()
            mp.commandv("quit")
        end
    end)
end

mp.add_periodic_timer(1, function()
    if schlaf_ende and mp.get_time() >= schlaf_ende then gute_nacht() end
end)

mp.register_event("end-file", function(e)
    if schlaf == "folge" and e.reason == "eof" then
        schlaf = "aus"
        mp.commandv("quit")
    end
end)

mp.register_event("file-loaded", function()
    abspann_ab = nil
    countdown_abgebrochen = nil
end)

mp.observe_property("chapter", "number", function()
    if ist_abspann(kapitel_titel()) then
        abspann_ab = abspann_ab or mp.get_property_number("time-pos", 0)
    else
        abspann_ab = nil
    end
end)

mp.add_periodic_timer(0.25, zeichnen)
mp.observe_property("mouse-pos", "native", function(_, m) if m and m.hover then zeigen() end end)
mp.observe_property("pause", "bool", function() zeichnen() end)

-- ---------------------------------------------------------------- Bedienung

local function lauter(schritt)
    local v = mp.get_property_number("volume", 100)
    if schritt > 0 and v >= 100 then
        melden("BEREITS REFERENZPEGEL.", 1.8)
        return
    end
    mp.set_property_number("volume", math.max(0, math.min(100, v + schritt)))
    zeigen()
end

local function ausfuehren(aktion, mx)
    if aktion == "pause" then mp.commandv("cycle", "pause")
    elseif aktion == "zurueck" then mp.commandv("seek", "-10")
    elseif aktion == "vor" then mp.commandv("seek", "10")
    elseif aktion == "naechste" then mp.commandv("playlist-next")
    elseif aktion == "untertitel" then mp.commandv("cycle", "sub")
    elseif aktion == "ton" then mp.commandv("cycle", "audio")
    elseif aktion == "lauter" then lauter(10)
    elseif aktion == "vollbild" then mp.commandv("cycle", "fullscreen")
    elseif aktion == "schliessen" then mp.commandv("quit")
    elseif aktion == "schlaf" then schlaf_weiter()
    elseif aktion == "nacht" then
        mp.commandv("af", "toggle", NACHT_FILTER)
        melden(nacht_an() and "Nachtmodus an: leise Stellen lauter, laute leiser" or "Nachtmodus aus", 2.2)
    elseif aktion == "intro_weg" then mp.commandv("add", "chapter", "1")
    elseif aktion == "jetzt_weiter" then mp.commandv("playlist-next")
    elseif aktion == "countdown_weg" then countdown_abgebrochen = mp.get_property("path")
    elseif aktion == "spulen" then
        for _, k in ipairs(knoepfe) do
            if k.aktion == "spulen" then
                local p = math.max(0, math.min(100, (mx - k.x) / k.w * 100))
                mp.commandv("seek", tostring(p), "absolute-percent")
            end
        end
    end
    zeigen()
end

mp.add_forced_key_binding("MBTN_LEFT", "bibiplexx-klick", function()
    if intro_laeuft then return end
    local mx, my = mp.get_mouse_pos()
    for _, k in ipairs(knoepfe) do
        if mx >= k.x and mx <= k.x + k.w and my >= k.y and my <= k.y + k.h then
            ausfuehren(k.aktion, mx)
            return
        end
    end
    -- Klick ins Bild: Pause
    mp.commandv("cycle", "pause")
    zeigen()
end)
mp.add_forced_key_binding("MBTN_LEFT_DBL", "bibiplexx-doppelklick", function() mp.commandv("cycle", "fullscreen") end)
mp.add_forced_key_binding("WHEEL_UP", "bibiplexx-lauter", function() lauter(5) end)
mp.add_forced_key_binding("WHEEL_DOWN", "bibiplexx-leiser", function() lauter(-5) end)
mp.add_forced_key_binding("0", "bibiplexx-lauter-taste", function() lauter(2) end, { repeatable = true })
mp.add_forced_key_binding("*", "bibiplexx-lauter-taste2", function() lauter(2) end, { repeatable = true })
mp.add_forced_key_binding("9", "bibiplexx-leiser-taste", function() lauter(-2) end, { repeatable = true })
mp.add_forced_key_binding("/", "bibiplexx-leiser-taste2", function() lauter(-2) end, { repeatable = true })
mp.add_key_binding("t", "bibiplexx-schlaf", function() ausfuehren("schlaf") end)
mp.add_key_binding("n", "bibiplexx-nacht", function() ausfuehren("nacht") end)
mp.add_key_binding("f", "bibiplexx-vollbild", function() ausfuehren("vollbild") end)
mp.add_forced_key_binding("ESC", "bibiplexx-esc", function()
    if mp.get_property_bool("fullscreen") then mp.set_property_bool("fullscreen", false) else mp.commandv("quit") end
end)
mp.observe_property("seeking", "bool", function(_, v) if v then zeigen() end end)

-- ---------------------------------------------------------------- Kinomodus

local function gong()
    if opts.gong == "" then return end
    mp.command_native_async({ name = "subprocess", args = { "pw-play", opts.gong }, playback_only = false },
        function(ok, r)
            if not ok or (r and r.status ~= 0) then
                mp.command_native_async({ name = "subprocess", args = { "paplay", opts.gong }, playback_only = false }, function() end)
            end
        end)
end

local function ease(t)
    t = math.max(0, math.min(1, t))
    return t < 0.5 and 4 * t * t * t or 1 - (-2 * t + 2) ^ 3 / 2
end

local function vorhang(l, x, breite, h, s, links)
    local streifen = math.max(8, math.floor(46 * s))
    table.insert(l, rechteck(x, 0, breite, h, "#7a1426"))
    local i = 0
    local px = x
    while px < x + breite do
        local sb = math.min(streifen, x + breite - px)
        if i % 2 == 0 then table.insert(l, rechteck(px, 0, sb, h, "#931c33")) end
        table.insert(l, rechteck(px + sb - math.max(1, math.floor(4 * s)), 0, math.max(1, math.floor(4 * s)), h, "#5e0f1d"))
        px = px + sb
        i = i + 1
    end
    local kante = links and (x + breite - math.floor(10 * s)) or x
    table.insert(l, rechteck(kante, 0, math.floor(10 * s), h, "#d4a73c", "40"))
end

local function intro_bild(t)
    local w, h, s = groesse()
    local l = {}
    local DAUER_ZU, DAUER_AUF = 1.5, 1.7
    local auf = ease((t - DAUER_ZU) / DAUER_AUF)
    if t < DAUER_ZU + 0.2 then
        table.insert(l, rechteck(0, 0, w, h, SCHWARZ))
    end
    local halb = math.floor(w / 2 * (1 - auf))
    if halb > 0 then
        vorhang(l, 0, halb, h, s, true)
        vorhang(l, w - halb, halb, h, s, false)
    end
    -- Schabracke oben
    local sh = math.floor(70 * s)
    table.insert(l, rechteck(0, 0, w, sh, "#5e0f1d", auf > 0.9 and string.format("%02X", math.floor((auf - 0.9) * 10 * 255)) or "00"))
    table.insert(l, rechteck(0, sh, w, math.max(2, math.floor(5 * s)), "#d4a73c", auf > 0.9 and "80" or "00"))
    if auf < 0.35 then
        local a = string.format("%02X", math.floor(math.min(1, auf / 0.35) * 255))
        table.insert(l, text(w / 2, h / 2 - math.floor(40 * s), "BIBIPLEXX", math.floor(110 * s), PINK, 5, true, a))
        table.insert(l, text(w / 2, h / 2 + math.floor(50 * s), "Reihe sieben.", math.floor(34 * s), TEXT, 5, false, a))
        -- Sitzreihe, Platz fuer Platz an
        local plaetze, pb = 9, math.floor(54 * s)
        local gesamt = plaetze * pb + (plaetze - 1) * math.floor(14 * s)
        local sx = w / 2 - gesamt / 2
        local an = math.floor(math.min(1, t / DAUER_ZU) * plaetze + 0.5)
        for i = 1, plaetze do
            local f = (i == 5) and ORANGE or (i <= an and LILA or "#1a1030")
            table.insert(l, rund(sx, h - math.floor(170 * s), pb, pb, 10 * s, f, a))
            sx = sx + pb + math.floor(14 * s)
        end
    end
    ov.res_x, ov.res_y = w, h
    ov.data = table.concat(l, "\n")
    ov:update()
    return auf
end

local intro_gezeigt = false
mp.register_event("file-loaded", function()
    if intro_gezeigt or not opts.kino then
        zeigen()
        return
    end
    intro_gezeigt = true
    intro_laeuft = true
    local war_pause = mp.get_property_bool("pause", false)
    mp.set_property_bool("pause", true)
    gong()
    local t0 = mp.get_time()
    local timer
    local gestartet = false
    timer = mp.add_periodic_timer(1 / 30, function()
        local auf = intro_bild(mp.get_time() - t0)
        if auf > 0.6 and not gestartet then
            gestartet = true
            if not war_pause then mp.set_property_bool("pause", false) end
        end
        if auf >= 1 then
            timer:kill()
            intro_laeuft = false
            zeigen()
        end
    end)
end)

-- Vor dem Intro schwarz, damit kein Filmbild aufblitzt
if opts.kino then
    local w, h = groesse()
    ov.res_x, ov.res_y = w, h
    ov.data = rechteck(0, 0, w, h, SCHWARZ)
    ov:update()
end
