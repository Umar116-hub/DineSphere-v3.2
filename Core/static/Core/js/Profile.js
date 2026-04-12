function openTab(evt, tabName) {
    let i, tabcontent, tablinks;

    // Hide all tab content
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
        tabcontent[i].classList.remove("active");
    }

    // Remove "active" class from all buttons
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }

    // Show the specific tab and mark button as active
    document.getElementById(tabName).style.display = "block";
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

let currentCancelId = null;

function confirmCancel(orderId) {
    console.log("I am not getting called");
    
    currentCancelId = orderId;
    document.getElementById("cancelModal").style.display = "block";
}

function closeModal() {
    currentCancelId = null;
    document.getElementById("cancelModal").style.display = "none";
}

// When user clicks confirm
document.getElementById("confirmCancelBtn").onclick = function() {
    if (currentCancelId) {
        // Redirect to cancel URL (Django view should handle cancellation)
        window.location.href = `/reservation/cancel-booking/${currentCancelId}/`;
    }
};
