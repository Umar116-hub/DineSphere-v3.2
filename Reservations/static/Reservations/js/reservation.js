
/* =========================
   UTILITIES
========================= */
function timeToMinutes(time) {
    if (!time || typeof time !== 'string' || !time.includes(':')) return 0;
    const [h, m] = time.split(":").map(Number);
    return (isNaN(h) ? 0 : h) * 60 + (isNaN(m) ? 0 : m);
}

function normalizeRange(open, close) {
    const openMin = timeToMinutes(open);
    let closeMin = timeToMinutes(close);

    // overnight case
    if (closeMin <= openMin) {
        closeMin += 24 * 60;
    }

    return { openMin, closeMin };
}

function normalizeStart(start, openMin) {
    let startMin = timeToMinutes(start);

    // push after midnight into next day window
    if (startMin < openMin) {
        startMin += 24 * 60;
    }

    return startMin;
}

/* =========================
   CORE LOGIC
========================= */
function getMaxDuration(startTime) {
    const { openMin, closeMin } = normalizeRange(restaurant_opening_hour, restaurant_closing_hour);
    const startMin = normalizeStart(startTime, openMin);

    const remaining = closeMin - startMin;

    return Math.floor(remaining / 60);
}

/* =========================
   UI UPDATE
========================= */
function updateDurationOptions() {
    const input = document.getElementById("startTimeBtn");
    const select = document.getElementById("durationHrs");
    const error = document.getElementById("errorMsg");

    const startTime = input.value;

    // reset UI
    select.innerHTML = "";
    error.textContent = "";

    if (!startTime) return;

    const { openMin, closeMin } = normalizeRange(restaurant_opening_hour, restaurant_closing_hour);
    const startMin = normalizeStart(startTime, openMin);

    /* =========================
       EDGE CASE 1: invalid time selection
    ========================= */
    const isValid = (startMin >= openMin && startMin <= closeMin);

    if (!isValid) {
        error.textContent = "Selected time is outside operating hours.";
        input.value = "";
        return;
    }

    const maxHours = getMaxDuration(startTime);

    /* =========================
       EDGE CASE 2: no duration available
    ========================= */
    if (maxHours <= 0) {
        error.textContent = "No booking duration available for this time.";
        return;
    }

    /* =========================
       POPULATE OPTIONS
    ========================= */
    for (let i = 1; i <= maxHours; i++) {
        const opt = document.createElement("option");
        opt.value = i;
        opt.textContent = `${i} Hour${i > 1 ? "s" : ""}`;
        select.appendChild(opt);
    }
}

/* =========================
   EVENT LISTENER
========================= */
document.getElementById("startTimeBtn")
    .addEventListener("change", updateDurationOptions);
