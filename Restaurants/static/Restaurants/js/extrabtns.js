// -------------------------------
// GET ALL SELECTED CARDS
// -------------------------------
function getSelectedCards() {
    return document.querySelectorAll('.clickable-card.selected');
}


// -------------------------------
// CSRF TOKEN
// -------------------------------
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}


// -------------------------------
// GENERIC POST
// -------------------------------
function sendPost(url, payload) {
    return fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams(payload)
    })
    .then(res => {
        if (!res.ok) throw new Error("Request failed");
        return res.text();
    });
}


// -------------------------------
// BOOKING → FINISH
// -------------------------------
document.querySelector('.booking_finish')?.addEventListener('click', async () => {
    const cards = getSelectedCards();
    if (cards.length === 0) return alert("Select at least one booking first!");

    for (let card of cards) {
        const id = card.dataset.id;
        try {
            await sendPost('/business/markfinish/', { booking_id: id });
        } catch (err) {
            console.error(`Failed to finish booking ${id}:`, err);
        }
    }
    location.reload();
});


// -------------------------------
// BOOKING → CANCEL
// -------------------------------
document.querySelector('.booking_cancel')?.addEventListener('click', async () => {
    const cards = getSelectedCards();
    if (cards.length === 0) return alert("Select at least one booking first!");

    const reason = prompt("Please enter a reason for cancellation (sent to the customer):", "Restaurant is closed due to unforeseen circumstances.");
    if (reason === null) return; // User cancelled the prompt

    for (let card of cards) {
        const id = card.dataset.id;
        try {
            await sendPost('/business/markcancel/', { booking_id: id, reason: reason });
        } catch (err) {
            console.error(`Failed to cancel booking ${id}:`, err);
        }
    }
    location.reload();
});


// -------------------------------
// REVIEW → SHOW
// -------------------------------
document.querySelector('.review_display_on')?.addEventListener('click', async () => {
    const cards = getSelectedCards();
    if (cards.length === 0) return alert("Select at least one review first!");

    for (let card of cards) {
        const id = card.dataset.id;
        try {
            await sendPost('/business/unhide/', { review_id: id });
        } catch (err) {
            console.error(`Failed to unhide review ${id}:`, err);
        }
    }
    location.reload();
});


// -------------------------------
// REVIEW → HIDE
// -------------------------------
document.querySelector('.review_display_off')?.addEventListener('click', async () => {
    const cards = getSelectedCards();
    if (cards.length === 0) return alert("Select at least one review first!");

    for (let card of cards) {
        const id = card.dataset.id;
        try {
            await sendPost('/business/hide/', { review_id: id });
        } catch (err) {
            console.error(`Failed to hide review ${id}:`, err);
        }
    }
    location.reload();
});

