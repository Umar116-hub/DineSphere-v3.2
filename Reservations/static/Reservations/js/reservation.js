
// Global Config from template
const appConfig = JSON.parse(document.getElementById('app-config').textContent);
const restaurantId = appConfig.restaurantId;
const restaurantName = appConfig.restaurantName.replace(/ /g, "_");
const isAuthenticated = appConfig.isAuthenticated;

// Dynamic Operational Hours State
let currentOpeningHour = appConfig.openingHour;
let currentClosingHour = appConfig.closingHour;

/* =========================
   UTILITIES
========================= */
function timeToMinutes(time) {
    if (!time || typeof time !== 'string' || !time.includes(':')) return 0;
    const [h, m] = time.split(":").map(Number);
    return (isNaN(h) ? 0 : h) * 60 + (isNaN(m) ? 0 : m);
}

function formatAMPM(hours, minutes) {
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const h = hours % 12 || 12;
    const m = String(minutes).padStart(2, '0');
    return `${h}:${m} ${ampm}`;
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
    if (startMin < openMin) {
        startMin += 24 * 60;
    }
    return startMin;
}

/* =========================
   CORE LOGIC
========================= */
function generateTimeSlots(opening, closing) {
    const select = document.getElementById('startTimeBtn');
    select.innerHTML = '<option value="">Select Time</option>';
    
    const [openH, openM] = opening.split(':').map(Number);
    const [closeH, closeM] = closing.split(':').map(Number);
    
    if (isNaN(openH) || isNaN(closeH)) return;

    let currentH = openH;
    let currentM = openM;
    let slots = 0;

    while (slots < 48) {
        const timeStr = `${String(currentH).padStart(2, '0')}:${String(currentM).padStart(2, '0')}`;
        const label = formatAMPM(currentH, currentM);
        const opt = new Option(label, timeStr);
        select.add(opt);

        if (currentH === closeH && currentM >= closeM) break;

        currentM += 30;
        if (currentM >= 60) {
            currentM = 0;
            currentH++;
        }
        if (currentH >= 24) currentH = 0;
        slots++;
    }
}

function fetchOperationalHours(dateStr) {
    const errorMsg = document.getElementById('errorMsg');
    const timeSelect = document.getElementById('startTimeBtn');
    
    fetch(`/business/get-operational-hours/?restaurant_id=${restaurantId}&date=${dateStr}`)
        .then(r => r.json())
        .then(data => {
            if (data.status === 'closed') {
                errorMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${data.message}`;
                timeSelect.innerHTML = '<option value="">Restaurant Closed</option>';
                timeSelect.disabled = true;
            } else {
                errorMsg.innerHTML = '';
                timeSelect.disabled = false;
                currentOpeningHour = data.opening;
                currentClosingHour = data.closing;
                generateTimeSlots(data.opening, data.closing);
                
                // Show a small hint about the hours
                errorMsg.innerHTML = `<span style="color: #64748b; font-size: 0.8rem;">Hours for today: ${data.opening_display} - ${data.closing_display}</span>`;
            }
        })
        .catch(err => console.error("Error fetching hours", err));
}

function getMaxDuration(startTime) {
    const { openMin, closeMin } = normalizeRange(currentOpeningHour, currentClosingHour);
    const startMin = normalizeStart(startTime, openMin);
    const remaining = closeMin - startMin;
    return Math.floor(remaining / 60);
}

function updateDurationOptions() {
    const input = document.getElementById("startTimeBtn");
    const select = document.getElementById("durationHrs");
    const error = document.getElementById("errorMsg");

    const startTime = input.value;
    select.innerHTML = "";
    if (!startTime) return;

    const { openMin, closeMin } = normalizeRange(currentOpeningHour, currentClosingHour);
    const startMin = normalizeStart(startTime, openMin);

    const isValid = (startMin >= openMin && startMin <= closeMin);
    if (!isValid) {
        error.textContent = "Selected time is outside operating hours.";
        input.value = "";
        return;
    }

    const maxHours = getMaxDuration(startTime);
    if (maxHours <= 0) {
        error.textContent = "No booking duration available.";
        return;
    }

    for (let i = 1; i <= maxHours; i++) {
        const opt = document.createElement("option");
        opt.value = i;
        opt.textContent = `${i} Hour${i > 1 ? "s" : ""}`;
        select.appendChild(opt);
    }
}

/* =========================
   UI & SEATING
========================= */
function openSeating(evt, seatingId) {
    document.querySelectorAll(".seating-content").forEach(c => c.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    document.getElementById(seatingId).classList.add("active");
    evt.currentTarget.classList.add("active");
}

let selectedTables = [];
function toggleTableSelection(el) {
    el.classList.toggle('selected');
    const tableId = el.dataset.id;
    if (el.classList.contains('selected')) {
        selectedTables.push({
            id: tableId,
            price: parseFloat(el.dataset.price),
            cap: parseInt(el.dataset.cap)
        });
    } else {
        selectedTables = selectedTables.filter(t => t.id !== tableId);
    }
    updateSummary();
}

function updateSummary() {
    let totalHourly = 0;
    let totalCap = 0;
    selectedTables.forEach(t => {
        totalHourly += t.price;
        totalCap += t.cap;
    });
    const hours = parseInt(document.getElementById('durationHrs').value) || 1;
    const finalTotal = totalHourly * hours;
    
    document.getElementById('sum-cap').innerText = totalCap;
    document.getElementById('sum-hourly').innerText = "$" + totalHourly.toFixed(2);
    document.getElementById('sum-total').innerText = "$" + finalTotal.toFixed(2);
    document.getElementById('form-cap').value = totalCap;
}

function checkAvailability() {
    const dateStr = document.getElementById('form-date').value;
    const startTime = document.getElementById('startTimeBtn').value;
    const duration = document.getElementById('durationHrs').value;

    if (!dateStr || !startTime) {
        document.querySelectorAll(".table-item").forEach(t => t.classList.remove("booked-table"));
        return;
    }

    const url = `../get-unavailable-tables/?date=${dateStr}&start_time=${startTime}&duration=${duration}&restaurant=${restaurantName}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const bookedTables = data.booked_tables || [];
            document.querySelectorAll(".table-item").forEach(table => {
                const tableId = parseInt(table.dataset.id);
                if (bookedTables.includes(tableId)) {
                    table.classList.add("booked-table");
                    if (table.classList.contains("selected")) toggleTableSelection(table);
                } else {
                    table.classList.remove("booked-table");
                }
            });
        })
        .catch(err => console.error("Error fetching availability", err));
}

/* =========================
   AUTH & SUBMIT
========================= */
function handleReserveClick() {
    if (isAuthenticated) {
        submitReservation();
    } else {
        document.getElementById('authModal').classList.add('active');
        document.body.classList.add('modal-active');
    }
}

function closeAuthModal() {
    document.getElementById('authModal').classList.remove('active');
    document.body.classList.remove('modal-active');
}

function submitReservation() {
    const startTime = document.getElementById('startTimeBtn').value;
    const date = document.getElementById('form-date').value;
    
    if (!date || !startTime || selectedTables.length === 0) {
        return alert("Please select Date, Time, and at least one Table.");
    }
    
    const duration = parseInt(document.getElementById('durationHrs').value) || 1;
    const [h, m] = startTime.split(':');
    const endH = (parseInt(h) + duration).toString().padStart(2, '0');
    
    document.getElementById('form-start').value = startTime;
    document.getElementById('form-end').value = `${endH}:${m}`;
    document.getElementById('form-date').value = date;
    
    let durInput = document.getElementById('form-duration') || document.createElement('input');
    durInput.type = 'hidden'; durInput.name = 'duration'; durInput.id = 'form-duration';
    document.getElementById('finalForm').appendChild(durInput);
    durInput.value = duration;
    
    document.getElementById('form-price').value = document.getElementById('sum-total').innerText.replace('$', '');
    
    const container = document.getElementById('table-ids-container');
    container.innerHTML = '';
    selectedTables.forEach(t => {
        const inp = document.createElement('input');
        inp.type = 'hidden'; inp.name = 'table_ids'; inp.value = t.id;
        container.appendChild(inp);
    });
    
    document.getElementById('finalForm').submit();
}

/* =========================
   INITIALIZATION
========================= */
document.addEventListener("DOMContentLoaded", function () {
    // Flatpickr
    flatpickr("#dateBtn", {
        minDate: "today",
        onChange: function (selectedDates, dateStr) {
            document.getElementById('dateBtn').innerText = dateStr;
            document.getElementById('form-date').value = dateStr;
            fetchOperationalHours(dateStr);
            checkAvailability();
        }
    });

    // Event Listeners
    document.getElementById('startTimeBtn').addEventListener('change', () => {
        updateDurationOptions();
        checkAvailability();
    });
    
    document.getElementById('durationHrs').addEventListener('change', () => {
        checkAvailability();
        updateSummary();
    });

    // Review Stars
    const stars = document.querySelectorAll("#star-container i");
    const ratingInput = document.getElementById("selected-rating");
    stars.forEach(star => {
        star.addEventListener("click", () => {
            ratingInput.value = star.dataset.value;
            stars.forEach(s => s.classList.toggle('active', s.dataset.value <= ratingInput.value));
        });
    });

    // Initial load
    generateTimeSlots(currentOpeningHour, currentClosingHour);
    initTestimonialCarousel();
});

function initTestimonialCarousel() {
    const track = document.getElementById('testimonial-track');
    if (!track) return;
    const slides = Array.from(track.children);
    if (slides.length === 0) return;
    let current = 0;
    setInterval(() => {
        current = (current + 1) % slides.length;
        const percentage = -(current * (100 / slides.length));
        track.style.transform = `translateX(${percentage}%)`;
    }, 3000);
}
